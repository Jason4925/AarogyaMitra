const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "https://aarogyamitra-zp8i.onrender.com";

function getSession() {
  try {
    return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null");
  } catch {
    return null;
  }
}

function requireSession() {
  const session = getSession();
  if (!session?.token || !session?.user_id) {
    window.location.href = "login.html";
    return null;
  }
  return session;
}

function setMessage(text, type = "info") {
  const el = document.getElementById("securityMsg");
  if (!el) return;
  el.textContent = text || "";
  el.className = `security-message ${type}`;
}

function setBusy(button, busy, busyText = "Working…") {
  if (!button) return;
  if (busy) {
    if (!button.dataset.originalText) button.dataset.originalText = button.textContent;
    button.disabled = true;
    button.textContent = busyText;
  } else {
    button.disabled = false;
    if (button.dataset.originalText) button.textContent = button.dataset.originalText;
  }
}

async function api(path, options = {}, timeoutMs = 8000) {
  const session = getSession();
  if (!session?.token) throw new Error("Your session has expired. Please log in again.");

  const headers = {
    Accept: "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${session.token}`
  };

  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      cache: "no-store",
      signal: controller.signal
    });

    const raw = await response.text();
    let data = {};
    try { data = raw ? JSON.parse(raw) : {}; } catch { data = {}; }

    if (!response.ok) {
      let message = data.detail || data.error || `Request failed (${response.status})`;
      if (Array.isArray(data.detail)) {
        message = data.detail.map(x => x.msg || x.message || "Invalid request").join(", ");
      }
      throw new Error(message);
    }

    return data;
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function renderSecuritySummary(data) {
  const el = document.getElementById("securitySummary");
  if (!el) return;

  const areas = Array.isArray(data.stored_areas) ? data.stored_areas : [];
  const controls = Array.isArray(data.controls) ? data.controls : [];
  const sharing = data.sharing || {};

  el.innerHTML = `
    <div class="security-status-grid">
      <div><span>Authentication</span><strong>✓ Active</strong></div>
      <div><span>Account role</span><strong>${escapeHtml(data.account?.role || "user")}</strong></div>
      <div><span>Memory</span><strong>${data.memory_enabled ? "Enabled" : "Disabled"}</strong></div>
      <div><span>Doctor Handoff consent</span><strong>${sharing.doctor_handoff ? "Granted" : "Not granted"}</strong></div>
      <div><span>Emergency escalation consent</span><strong>${sharing.emergency_contact ? "Granted" : "Not granted"}</strong></div>
      <div><span>Population analytics</span><strong>${sharing.population_analytics ? "Granted" : "Not granted"}</strong></div>
    </div>
    <div class="security-detail-block">
      <h4>Stored data areas</h4>
      <p>${areas.map(escapeHtml).join(" · ") || "No application data areas reported."}</p>
    </div>
    <div class="security-detail-block">
      <h4>Available controls</h4>
      <p>${controls.map(escapeHtml).join(" · ")}</p>
    </div>
  `;
}

function renderMemory(enabled) {
  const toggle = document.getElementById("memoryToggle");
  const status = document.getElementById("memoryStatus");
  if (toggle) toggle.checked = !!enabled;
  if (status) {
    status.textContent = enabled
      ? "Memory is enabled. Previous conversations may be used to maintain context."
      : "Memory is disabled. Future AI requests will not use previous conversation history as context.";
  }
}

function renderConsents(consents) {
  document.getElementById("consentHandoff").checked = !!consents.doctor_handoff;
  document.getElementById("consentEmergency").checked = !!consents.emergency_contact;
  document.getElementById("consentAnalytics").checked = !!consents.population_analytics;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

async function loadAll() {
  const session = requireSession();
  if (!session) return;

  setMessage("Loading security settings…", "info");

  const results = await Promise.allSettled([
    api("/privacy/security-summary"),
    api("/memory/preferences"),
    api("/consents")
  ]);

  let loaded = 0;
  const [summary, memory, consents] = results;

  if (summary.status === "fulfilled") {
    renderSecuritySummary(summary.value);
    loaded++;
  } else {
    document.getElementById("securitySummary").innerHTML = `<p class="security-empty">Security status could not be loaded: ${escapeHtml(summary.reason?.message)}</p>`;
  }

  if (memory.status === "fulfilled") {
    renderMemory(memory.value.enabled);
    loaded++;
  }

  if (consents.status === "fulfilled") {
    renderConsents(consents.value.consents || {});
    loaded++;
  }

  if (loaded === 3) {
    setMessage("Security settings loaded successfully.", "success");
  } else if (loaded > 0) {
    setMessage("Some security settings could not be loaded. Check the message above and retry.", "warning");
  } else {
    setMessage("The Security Center could not connect to the AarogyaMitra backend.", "error");
  }
}

async function toggleMemory(enabled) {
  const toggle = document.getElementById("memoryToggle");
  try {
    const data = await api("/memory/preferences", {
      method: "PUT",
      body: JSON.stringify({ enabled })
    });
    renderMemory(data.enabled);
    setMessage("Memory preference saved.", "success");
  } catch (error) {
    if (toggle) toggle.checked = !enabled;
    setMessage(error.message, "error");
  }
}

async function saveConsents() {
  const button = document.getElementById("saveConsentsBtn");
  setBusy(button, true, "Saving…");
  try {
    const data = await api("/consents", {
      method: "PUT",
      body: JSON.stringify({
        ai_assistance: true,
        health_storage: true,
        doctor_handoff: document.getElementById("consentHandoff").checked,
        emergency_contact: document.getElementById("consentEmergency").checked,
        population_analytics: document.getElementById("consentAnalytics").checked
      })
    });
    renderConsents(data.consents || {});
    setMessage("Consent preferences saved.", "success");
    loadSecuritySummaryOnly();
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function clearConversationMemory() {
  const session = getSession();
  if (!session) return;
  const button = document.getElementById("clearMemoryBtn");
  if (!confirm("Clear your saved conversation history? This cannot be undone.")) return;

  setBusy(button, true, "Clearing…");
  try {
    await api(`/history/${encodeURIComponent(session.user_id)}`, { method: "DELETE" });
    setMessage("Conversation history cleared successfully.", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function exportData() {
  const button = document.getElementById("exportDataBtn");
  setBusy(button, true, "Preparing…");
  try {
    const data = await api("/privacy/export", {}, 15000);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "aarogyamitra-my-data.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    setMessage("Your personal data export has been downloaded.", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

let deleteModal = null;
let deleteInput = null;
let deleteConfirmButton = null;

function openDeleteModal() {
  deleteModal = document.getElementById("deleteModal");
  deleteInput = document.getElementById("deleteConfirmationInput");
  deleteConfirmButton = document.getElementById("deleteConfirmBtn");
  if (!deleteModal || !deleteInput || !deleteConfirmButton) return;

  deleteInput.value = "";
  deleteConfirmButton.disabled = true;
  deleteModal.classList.add("open");
  deleteModal.setAttribute("aria-hidden", "false");
  setTimeout(() => deleteInput.focus(), 50);
}

function closeDeleteModal() {
  if (!deleteModal) deleteModal = document.getElementById("deleteModal");
  if (!deleteModal) return;
  deleteModal.classList.remove("open");
  deleteModal.setAttribute("aria-hidden", "true");
}

function updateDeleteConfirmation() {
  if (!deleteInput || !deleteConfirmButton) return;
  deleteConfirmButton.disabled = deleteInput.value.trim() !== "DELETE MY ACCOUNT";
}

async function permanentlyDeleteAccount() {
  const button = deleteConfirmButton;
  const confirmation = deleteInput?.value.trim() || "";

  if (confirmation !== "DELETE MY ACCOUNT") {
    return;
  }

  setBusy(button, true, "Deleting…");
  try {
    await api("/privacy/account", {
      method: "DELETE",
      body: JSON.stringify({ confirmation: "DELETE" })
    }, 15000);

    localStorage.removeItem("aarogyamitra_session");
    localStorage.removeItem("aarogyamitra_latest_report");
    localStorage.removeItem("aarogyamitra_handoff");
    localStorage.removeItem("aarogyamitra_latest_handoff");
    window.location.href = "index.html?accountDeleted=1";
  } catch (error) {
    closeDeleteModal();
    setMessage(error.message, "error");
    setBusy(button, false);
  }
}

async function loadSecuritySummaryOnly() {
  try {
    const data = await api("/privacy/security-summary");
    renderSecuritySummary(data);
  } catch (error) {
    console.warn("Security summary refresh failed:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const session = requireSession();
  if (!session) return;

  document.getElementById("memoryToggle")?.addEventListener("change", (e) => toggleMemory(e.target.checked));
  document.getElementById("saveConsentsBtn")?.addEventListener("click", saveConsents);
  document.getElementById("clearMemoryBtn")?.addEventListener("click", clearConversationMemory);
  document.getElementById("exportDataBtn")?.addEventListener("click", exportData);
  document.getElementById("deleteAccountBtn")?.addEventListener("click", openDeleteModal);
  document.getElementById("deleteCancelBtn")?.addEventListener("click", closeDeleteModal);
  document.getElementById("deleteCloseBtn")?.addEventListener("click", closeDeleteModal);
  document.querySelector("[data-close-delete]")?.addEventListener("click", closeDeleteModal);
  deleteInput = document.getElementById("deleteConfirmationInput");
  deleteConfirmButton = document.getElementById("deleteConfirmBtn");
  deleteInput?.addEventListener("input", updateDeleteConfirmation);
  deleteConfirmButton?.addEventListener("click", permanentlyDeleteAccount);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDeleteModal();
  });

  loadAll();
});
