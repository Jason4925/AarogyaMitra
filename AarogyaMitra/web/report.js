const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "https://aarogyamitra-zp8i.onrender.com";
function getSession() {
  try { return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null"); }
  catch { return null; }
}

function requireLogin() {
  const s = getSession();
  if (!s || !s.token) {
    window.location.href = "login.html";
    return null;
  }
  return s;
}

function escapeHtml(value) {
  const d = document.createElement("div");
  d.textContent = String(value ?? "");
  return d.innerHTML;
}

function humanValue(value) {
  if (value === null || value === undefined) return "";

  if (typeof value === "string") {
    const t = value.trim();
    if (!t) return "";

    if ((t.startsWith("[") && t.endsWith("]")) || (t.startsWith("{") && t.endsWith("}"))) {
      try {
        return humanValue(JSON.parse(t));
      } catch (_) {}
    }

    return t
      .replace(/^\s*[-*•]+\s*/, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  if (Array.isArray(value)) {
    return value.map(humanValue).filter(Boolean).join(" · ");
  }

  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => {
        const text = humanValue(val);
        if (!text) return "";
        return `${key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase())}: ${text}`;
      })
      .filter(Boolean)
      .join(" · ");
  }

  return String(value);
}

function cleanText(value, fallback = "") {
  const text = humanValue(value);
  return text || fallback;
}

function normalizeList(value) {
  if (value === null || value === undefined) return [];

  if (Array.isArray(value)) {
    return value.flatMap(item => {
      if (item && typeof item === "object") {
        const text = humanValue(item);
        return text ? [text] : [];
      }
      const text = humanValue(item);
      return text ? [text] : [];
    });
  }

  const text = humanValue(value);
  return text ? [text] : [];
}

function medicalItemHtml(item) {
  if (item === null || item === undefined) return "";

  if (typeof item === "object" && !Array.isArray(item)) {
    const entries = Object.entries(item).filter(([, value]) => cleanText(value));

    if (!entries.length) return "";

    return `
      <li class="medical-item">
        <div class="medical-item-grid">
          ${entries.map(([key, value]) => `
            <div>
              <div class="medical-item-label">
                ${escapeHtml(key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()))}
              </div>
              <div class="medical-item-value">
                ${escapeHtml(cleanText(value))}
              </div>
            </div>
          `).join("")}
        </div>
      </li>
    `;
  }

  const text = cleanText(item);
  if (!text) return "";

  // Convert common "key=value" AI output into a readable card.
  const parts = text
    .split(/\s*(?:,|;|\||\n)\s*/)
    .map(part => part.trim())
    .filter(Boolean);

  const keyValuePairs = parts
    .map(part => {
      const match = part.match(/^([A-Za-z][A-Za-z _-]{1,40})\s*=\s*(.+)$/);
      return match ? [match[1], match[2]] : null;
    })
    .filter(Boolean);

  if (keyValuePairs.length >= 2) {
    return `
      <li class="medical-item">
        <div class="medical-item-grid">
          ${keyValuePairs.map(([key, value]) => `
            <div>
              <div class="medical-item-label">
                ${escapeHtml(key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()))}
              </div>
              <div class="medical-item-value">
                ${escapeHtml(value)}
              </div>
            </div>
          `).join("")}
        </div>
      </li>
    `;
  }

  return `<li>${escapeHtml(text)}</li>`;
}

function listHtml(value, emptyText = "Information will be discussed with a qualified healthcare professional.") {
  const items = normalizeList(value);
  if (!items.length) return `<p>${escapeHtml(emptyText)}</p>`;
  return `<ul>${items.map(medicalItemHtml).filter(Boolean).join("")}</ul>`;
}

function toggleSection(head) {
  if (!head) return;
  head.classList.toggle("open");
  const body = head.nextElementSibling;
  const toggle = head.querySelector(".rs-toggle");
  if (body) body.classList.toggle("open");
  if (toggle) toggle.classList.toggle("open");
}

function riskClass(level) {
  return level === "High" ? "risk-high" : level === "Moderate" ? "risk-moderate" : "risk-low";
}

function riskIcon(level) {
  return level === "High" ? "🔴" : level === "Moderate" ? "🟡" : "🟢";
}

function safeSourceUrl(url) {
  const value = String(url || "").trim();
  if (!value) return "#";
  try {
    const parsed = new URL(value, window.location.href);
    if (!["http:", "https:"].includes(parsed.protocol)) return "#";
    return parsed.href;
  } catch {
    return "#";
  }
}

function renderRisk(risk) {
  if (!risk || !risk.level) return "";

  const factors = normalizeList(risk.factors);

  return `
    <section class="intel-card risk-explain ${riskClass(risk.level)}">
      <div class="intel-kicker">AarogyaMitra Risk Engine</div>
      <h3>${riskIcon(risk.level)} ${escapeHtml(risk.priority || `${risk.level} Priority`)}</h3>
      <p><strong>Risk score:</strong> ${escapeHtml(risk.score ?? "—")} · <strong>Indicators:</strong> ${escapeHtml(risk.risk_indicators ?? 0)}</p>
      ${factors.length ? `<div class="risk-factors">${factors.map(f => `<div>✓ ${escapeHtml(f)}</div>`).join("")}</div>` : ""}
      <p class="risk-why"><strong>Why?</strong> The priority is calculated from the structured assessment, symptoms, severity, duration, age, medical history, red flags and follow-up information.</p>
      <p><strong>Recommended next step:</strong> ${escapeHtml(cleanText(risk.recommended_action, "Discuss the findings with a qualified healthcare professional."))}</p>
      <div class="followup-buttons">
        <button class="btn-ghost btn-sm" type="button" onclick="window.location.href='healthcare.html'">📍 Find Nearby Care</button>
        ${risk.level === "High" ? `<button class="btn-primary btn-sm" type="button" onclick="triggerEmergencyCall()">📞 Call Family</button>` : ""}
        <button class="btn-primary btn-sm" type="button" onclick="openDoctorHandoff()">🤝 Doctor Handoff</button>
        <button class="btn-ghost btn-sm" type="button" onclick="window.location.href='care-pathway.html'">🧭 Care Pathway</button>
      </div>
    </section>
  `;
}

function renderPatientSummary(data, risk) {
  const questions = Number(data.questions_answered ?? Object.keys(data.follow_up_details || {}).length) || 0;
  const symptoms = normalizeList(data.symptoms);
  const conditions = normalizeList(data.conditions);
  const meds = cleanText(data.medications);
  const allergies = cleanText(data.allergies);

  return `
    <section class="handoff-card">
      <div class="intel-kicker">Doctor-Ready Health Summary</div>
      <h2>PATIENT SUMMARY</h2>

      <div class="handoff-grid">
        <div><div class="handoff-label">Chief concern</div><div class="handoff-value">${escapeHtml(cleanText(data.mainProblem, "Not recorded"))}</div></div>
        <div><div class="handoff-label">Duration</div><div class="handoff-value">${escapeHtml(cleanText(data.duration, "—"))}</div></div>
        <div><div class="handoff-label">Severity</div><div class="handoff-value">${escapeHtml(data.severity ?? "—")}/10</div></div>
        <div><div class="handoff-label">Associated symptoms</div><div class="handoff-value">${escapeHtml(symptoms.join(", ") || "None selected")}</div></div>
        <div><div class="handoff-label">Relevant history</div><div class="handoff-value">${escapeHtml(conditions.join(", ") || "None reported")}</div></div>
        <div><div class="handoff-label">Medications / allergies</div><div class="handoff-value">${escapeHtml([meds ? `Meds: ${meds}` : "", allergies ? `Allergies: ${allergies}` : ""].filter(Boolean).join(" · ") || "None reported")}</div></div>
        <div><div class="handoff-label">Questions answered</div><div class="handoff-value">${questions}</div></div>
        <div><div class="handoff-label">Urgency</div><div class="handoff-value">${riskIcon(risk?.level)} ${escapeHtml(risk?.level || "Not calculated")}</div></div>
        <div><div class="handoff-label">Generated</div><div class="handoff-value">${escapeHtml(new Date(data.created_at || Date.now()).toLocaleDateString("en-IN", {day:"2-digit", month:"short", year:"numeric"}))}</div></div>
      </div>

      <div style="margin-top:18px">
        <div class="handoff-label">Key findings</div>
        ${listHtml(data.report?.key_findings, "No key findings were recorded.")}
      </div>

      <div style="margin-top:18px">
        <div class="handoff-label">Patient's own description</div>
        <div class="handoff-value">“${escapeHtml(cleanText(data.mainProblem, "Not recorded"))}”</div>
      </div>
    </section>
  `;
}

function renderReport(data) {
  const root = document.getElementById("resultBody");
  if (!root) return;

  const report = data.report && typeof data.report === "object" ? data.report : data;
  const risk = data.risk_engine || data.risk || {};
  const flags = normalizeList(data.red_flags ?? report.red_flags ?? risk.red_flags);
  const symptoms = normalizeList(data.symptoms);
  const summary = cleanText(report.problem_summary ?? data.problem_summary, "The assessment was completed, but a detailed summary was not returned.");
  const nextSteps = cleanText(report.next_steps ?? risk.recommended_action, "Discuss persistent, severe or worsening symptoms with a qualified healthcare professional.");
  const allopathy = report.allopathy || {};
  const homeopathy = report.homeopathy || {};
  const ayurveda = report.ayurveda || {};
  const sources = Array.isArray(report.sources) ? report.sources : [];

  const flagsHtml = flags.length ? `
    <div class="red-flag-block">
      <div class="rf-title">🚨 Red Flag Warnings</div>
      ${flags.map(flag => `<div class="rf-item">• ${escapeHtml(flag)}</div>`).join("")}
      <button class="emergency-call-btn" type="button" onclick="triggerEmergencyCall()">📞 Alert Emergency Contact</button>
    </div>
  ` : "";

  const symptomsHtml = symptoms.length ? `
    <div style="margin-bottom:20px">
      <div style="font-size:.72rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin-bottom:10px">Reported Symptoms</div>
      <div class="symptoms-list">${symptoms.map(s => `<span class="symptom-tag">${escapeHtml(s)}</span>`).join("")}</div>
    </div>
  ` : "";

  const sourceHtml = sources.length ? `
    <div class="report-section">
      <div class="rs-head open" onclick="toggleSection(this)">
        <div class="rs-icon">🔎</div>
        <div class="rs-title-wrap"><div class="rs-system">Evidence</div><div class="rs-title">Trusted Information Sources</div></div>
        <div class="rs-toggle open">▾</div>
      </div>
      <div class="rs-body open">
        <div class="source-citations">
          ${sources.map(source => `
            <a href="${escapeHtml(safeSourceUrl(source.url))}" target="_blank" rel="noopener noreferrer">
              <strong>${escapeHtml(cleanText(source.title, "Trusted source"))}</strong>
              <span>${escapeHtml(cleanText(source.source, "Source"))}</span>
            </a>
          `).join("")}
        </div>
      </div>
    </div>
  ` : "";

  root.innerHTML = `
    <div class="report-header">
      <div class="rh-logo">
        <img src="assets/aarogyamitra-logo.png" alt="AarogyaMitra logo" class="report-brand-logo">
        <img src="assets/aarogyamitra-text.png" alt="AarogyaMitra" class="report-brand-name">
      </div>
      <div class="rh-id">Health Information Report</div>
      <div class="rh-title">${escapeHtml(cleanText(data.mainProblem, "Health Assessment"))}</div>
      <div class="rh-meta">
        <div><div class="rh-meta-label">Duration</div><div class="rh-meta-val">${escapeHtml(cleanText(data.duration, "—"))}</div></div>
        <div><div class="rh-meta-label">Severity</div><div class="rh-meta-val">${escapeHtml(data.severity ?? "—")} / 10</div></div>
        <div><div class="rh-meta-label">Age</div><div class="rh-meta-val">${escapeHtml(data.age ?? "—")}</div></div>
        <div><div class="rh-meta-label">Urgency</div><div class="rh-meta-val">${riskIcon(risk.level)} ${escapeHtml(risk.level || "—")}</div></div>
        <div><div class="rh-meta-label">Generated</div><div class="rh-meta-val">${escapeHtml(new Date(data.created_at || Date.now()).toLocaleDateString("en-IN", {day:"numeric",month:"short",year:"numeric"}))}</div></div>
      </div>
    </div>

    ${renderRisk(risk)}
    ${flagsHtml}
    ${renderPatientSummary(data, risk)}
    ${symptomsHtml}

    <div class="report-section">
      <div class="rs-head open" onclick="toggleSection(this)">
        <div class="rs-icon">📋</div>
        <div class="rs-title-wrap"><div class="rs-system">Problem Summary</div><div class="rs-title">What was reported</div></div>
        <div class="rs-toggle open">▾</div>
      </div>
      <div class="rs-body open">
        <div class="rs-item"><p>${escapeHtml(summary)}</p></div>
        <hr class="rs-divider"/>
        <div class="rs-grid">
          <div class="rs-item"><h5>Important symptoms</h5>${listHtml(report.key_findings || symptoms, "No specific symptoms were selected.")}</div>
          <div class="rs-item"><h5>Next-step guidance</h5><p>${escapeHtml(nextSteps)}</p></div>
        </div>
      </div>
    </div>

    <div class="report-section">
      <div class="rs-head open" onclick="toggleSection(this)">
        <div class="rs-icon">💊</div>
        <div class="rs-title-wrap"><div class="rs-system">Modern Medicine</div><div class="rs-title">Allopathy Section</div></div>
        <div class="rs-toggle open">▾</div>
      </div>
      <div class="rs-body open">
        <div class="rs-grid">
          <div class="rs-item"><h5>Health interpretation</h5><p>${escapeHtml(cleanText(allopathy.overview, "Informational overview only; the cause should be assessed by a qualified clinician."))}</p></div>
          <div class="rs-item"><h5>Medicine information — not a prescription</h5>${listHtml(allopathy.medicine_information, "Medication choices depend on the cause, age, allergies and existing conditions; discuss options with a clinician or pharmacist.")}</div>
        </div>
        <hr class="rs-divider"/>
        <div class="rs-item"><h5>Investigations to discuss</h5>${listHtml(allopathy.investigations, "A clinician can decide whether an examination or investigation is appropriate.")}</div>
      </div>
    </div>

    <div class="report-section">
      <div class="rs-head" onclick="toggleSection(this)">
        <div class="rs-icon">🔬</div>
        <div class="rs-title-wrap"><div class="rs-system">Complementary Perspective</div><div class="rs-title">Homeopathy Section</div></div>
        <div class="rs-toggle">▾</div>
      </div>
      <div class="rs-body">
        <div class="rs-grid">
          <div class="rs-item"><h5>Informational perspective</h5><p>${escapeHtml(cleanText(homeopathy.overview, "A complementary perspective only; it should not replace necessary medical care."))}</p></div>
          <div class="rs-item"><h5>Commonly discussed remedies</h5>${listHtml(homeopathy.remedy_information, "No specific remedy information was returned.")}</div>
        </div>
        <hr class="rs-divider"/>
        <div class="rs-item"><h5>Safety note</h5><p>${escapeHtml(cleanText(homeopathy.safety_note, "Do not replace urgent or prescribed care with homeopathic products."))}</p></div>
      </div>
    </div>

    <div class="report-section">
      <div class="rs-head" onclick="toggleSection(this)">
        <div class="rs-icon">🌿</div>
        <div class="rs-title-wrap"><div class="rs-system">Traditional Indian Perspective</div><div class="rs-title">Ayurveda Section</div></div>
        <div class="rs-toggle">▾</div>
      </div>
      <div class="rs-body">
        <div class="rs-grid">
          <div class="rs-item"><h5>Informational perspective</h5><p>${escapeHtml(cleanText(ayurveda.overview, "Traditional lifestyle perspective only; use qualified practitioners for individualized advice."))}</p></div>
          <div class="rs-item"><h5>Diet & lifestyle ideas</h5>${listHtml(ayurveda.lifestyle_information, "Maintain appropriate hydration, nutrition, sleep and activity as tolerated." )}</div>
        </div>
        <hr class="rs-divider"/>
        <div class="rs-item"><h5>Safety note</h5><p>${escapeHtml(cleanText(ayurveda.safety_note, "Tell your clinician about herbs or traditional products, especially when taking medicines."))}</p></div>
      </div>
    </div>

    ${sourceHtml}

    <div class="disclaimer-block">
      <strong>Disclaimer:</strong>
      This report is an informational health overview, not a diagnosis or prescription. Medication information is for discussion with a qualified healthcare professional. Do not delay urgent care based on this report.
    </div>
  `;

  loadTimeline();
}

async function withTimeout(promise, ms = 5000) {
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error("Request timed out")), ms));
  return Promise.race([promise, timeout]);
}

async function loadTimeline() {
  const el = document.getElementById("reportTimeline");
  if (!el) return;

  try {
    const s = requireLogin();
    if (!s) return;

    const response = await withTimeout(fetch(`${API_BASE}/timeline`, {
      headers: { Authorization: `Bearer ${s.token}` }
    }), 5000);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    const rows = Array.isArray(data.events) ? data.events : [];

    if (!rows.length) {
      el.innerHTML = "<p>No timeline events have been recorded yet.</p>";
      return;
    }

    el.innerHTML = `<div class="timeline-wrap">${rows.map(ev => `
      <div class="timeline-item">
        <span class="timeline-dot"></span>
        <div class="timeline-date">${escapeHtml(new Date(ev.timestamp).toLocaleDateString("en-IN", {month:"short",day:"numeric"}))}</div>
        <div class="timeline-title">${escapeHtml(cleanText(ev.title || ev.event_type, "Health event"))}</div>
        <div class="timeline-summary">
          ${escapeHtml(cleanText(ev.summary))}
          ${ev.severity !== null && ev.severity !== undefined && ev.severity !== "" ? ` · Severity ${escapeHtml(ev.severity)}/10` : ""}
          ${ev.urgency ? ` · ${riskIcon(ev.urgency)} ${escapeHtml(ev.urgency)}` : ""}
        </div>
      </div>
    `).join("")}</div>`;
  } catch (error) {
    console.warn("Timeline could not be loaded:", error);
    el.innerHTML = "<p>Timeline is temporarily unavailable. Your report itself is still available.</p>";
  }
}

function openDoctorHandoff() {
  const s = requireLogin();
  if (!s) return;
  window.location.href = "handoff.html?v=22";
}

async function triggerEmergencyCall() {
  const s = requireLogin();
  if (!s) return;

  let stored = {};
  try { stored = JSON.parse(localStorage.getItem("aarogyamitra_latest_report") || "{}"); } catch (_) {}

  try {
    const response = await withTimeout(fetch(`${API_BASE}/emergency/call`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${s.token}`
      },
      body: JSON.stringify({ reason: stored.mainProblem || "Red flag identified in health assessment" })
    }), 7000);

    const data = await response.json();
    alert(data.message || (data.success ? "Emergency contact alerted." : "Emergency call failed."));
  } catch (error) {
    console.error("Emergency call error:", error);
    alert("Unable to place the emergency call right now.");
  }
}

async function fetchLatestReport(session) {
  const response = await withTimeout(fetch(`${API_BASE}/latest-report`, {
    headers: { Authorization: `Bearer ${session.token}` }
  }), 5000);

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function safeParseStoredReport() {
  try {
    const data = JSON.parse(localStorage.getItem("aarogyamitra_latest_report") || "null");
    return data && typeof data === "object" ? data : null;
  } catch {
    return null;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const session = requireLogin();
  if (!session) return;

  const edit = document.getElementById("editInputsBtn");
  if (edit) edit.onclick = () => window.location.href = "assessment.html";

  const dashboard = document.getElementById("dashboardBtn");
  if (dashboard) dashboard.onclick = () => window.location.href = "dashboard.html";

  const root = document.getElementById("resultBody");
  if (!root) return;

  root.innerHTML = `
    <div class="report-section">
      <div class="rs-body open" style="display:block">
        <p>Loading your health report…</p>
      </div>
    </div>
  `;

  // Render saved report immediately, then refresh it from PostgreSQL.
  let data = safeParseStoredReport();

  if (data) {
    renderReport(data);
  }

  try {
    const fresh = await fetchLatestReport(session);
    if (fresh && fresh.report) {
      data = fresh;
      localStorage.setItem("aarogyamitra_latest_report", JSON.stringify(fresh));
      renderReport(fresh);
    }
  } catch (error) {
    console.warn("Backend report refresh failed:", error);
  }

  if (!data || !data.report) {
    root.innerHTML = `
      <div class="report-section">
        <div class="rs-body open" style="display:block">
          <p>No report was found for this account.</p>
          <button class="btn-primary btn-sm" type="button" onclick="window.location.href='assessment.html'">Complete Assessment</button>
        </div>
      </div>
    `;
  }
});
