const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "http://localhost:8000";

document.getElementById("adminLoginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.getElementById("authError");
  error.textContent = "";
  try {
    const response = await fetch(`${API_BASE}/admin/login`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    localStorage.setItem("aarogyamitra_session", JSON.stringify(data));
    window.location.href = "admin.html";
  } catch (err) {
    error.textContent = err.message;
  }
});
