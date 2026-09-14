const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "https://aarogyamitra-zp8i.onrender.com/";

function saveSession(session) {
  localStorage.setItem("aarogyamitra_session", JSON.stringify(session));
}
function getSession() {
  try { return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null"); }
  catch { return null; }
}
async function postJSON(path, payload) {
  const r = await fetch(API_BASE + path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok || data.detail) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
}

document.addEventListener("DOMContentLoaded", () => {
  const lf = document.getElementById("loginForm");
  if (lf) lf.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = document.getElementById("authError");
    err.textContent = "";
    try {
      const data = await postJSON("/login", {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value
      });
      saveSession(data);
      window.location.href = data.role === "health_worker" ? "worker.html" : "dashboard.html";
    } catch (x) { err.textContent = x.message; }
  });

  const sf = document.getElementById("signupForm");
  if (sf) sf.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = document.getElementById("authError");
    err.textContent = "";
    try {
      const data = await postJSON("/signup", {
        name: document.getElementById("name").value.trim(),
        email: document.getElementById("email").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        password: document.getElementById("password").value
      });
      saveSession(data);
      window.location.href = "dashboard.html";
    } catch (x) { err.textContent = x.message; }
  });
});
