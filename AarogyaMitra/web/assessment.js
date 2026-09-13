const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "http://localhost:8000";

const formData = {
  mainProblem: "", duration: "", severity: 5, symptoms: [],
  age: "", gender: "", weight: "", pregnancy: "",
  conditions: [], medications: "", allergies: "", diet: "", lifestyle: [],
  follow_up_details: {}
};

const SYMPTOMS = [
  ["headache","Headache","🤕"],["fever","Fever","🌡️"],["cough","Cough","😮‍💨"],
  ["sore_throat","Sore Throat","🤧"],["fatigue","Fatigue","😴"],["nausea","Nausea","🤢"],
  ["vomiting","Vomiting","🤮"],["diarrhea","Diarrhoea","💧"],["constipation","Constipation","😣"],
  ["abdominal_pain","Abdominal Pain","🫃"],["bloating","Bloating","🎈"],["back_pain","Back Pain","🦴"],
  ["joint_pain","Joint Pain","🦵"],["muscle_ache","Muscle Ache","💪"],["chest_pain","Chest Pain","💔"],
  ["shortness_breath","Breathlessness","😮"],["palpitations","Palpitations","💓"],["dizziness","Dizziness","😵"],
  ["loss_appetite","Loss of Appetite","🍽️"],["weight_loss","Weight Loss","⚖️"],["weight_gain","Weight Gain","📈"],
  ["skin_rash","Skin Rash","🩹"],["itching","Itching","🤫"],["dry_skin","Dry Skin","🌵"],
  ["hair_loss","Hair Loss","💇"],["insomnia","Insomnia","🌙"],["anxiety","Anxiety","😰"],
  ["depression","Low Mood","🌧️"],["memory_issues","Memory Issues","🧠"],["frequent_urination","Frequent Urination","🚿"],
  ["burning_urination","Burning Urination","🔥"],["blurred_vision","Blurred Vision","👁️"],
  ["nasal_congestion","Nasal Congestion","👃"],["sneezing","Sneezing","🤧"],
  ["swollen_lymph","Swollen Lymph Nodes","🔮"],["night_sweats","Night Sweats","💦"]
];

const SEV_LABELS = {
  1:"Barely noticeable",2:"Very mild",3:"Mild",4:"Somewhat uncomfortable",
  5:"Noticeable but manageable",6:"Moderately painful",7:"Quite uncomfortable",
  8:"Severe",9:"Very severe",10:"Extreme / Unbearable"
};

let currentStep = 1;

function getSession() {
  try { return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null"); }
  catch { return null; }
}

function requireLogin() {
  const s = getSession();
  if (!s || !s.token) { location.href = "login.html"; return null; }
  return s;
}

function escapeHtml(t) {
  const d = document.createElement("div");
  d.textContent = String(t ?? "");
  return d.innerHTML;
}

function updateSeverity(v) {
  const value = Math.max(1, Math.min(10, parseInt(v, 10) || 5));
  formData.severity = value;
  const display = document.getElementById("sevDisplay");
  const desc = document.getElementById("sevDesc");
  const slider = document.getElementById("severity");
  if (display) display.textContent = value;
  if (desc) desc.textContent = SEV_LABELS[value];
  if (slider) slider.style.setProperty("--val", (((value - 1) / 9) * 100).toFixed(1) + "%");
}

function buildSymptomGrid() {
  const grid = document.getElementById("symptomGrid");
  if (!grid) return;
  grid.innerHTML = SYMPTOMS.map(([id,label,emoji]) =>
    `<div class="sym-card"><input type="checkbox" id="sym_${id}" value="${escapeHtml(label)}"><label class="sym-label" for="sym_${id}"><span class="sym-emoji">${emoji}</span>${escapeHtml(label)}</label></div>`
  ).join("");
  grid.addEventListener("change", requestRiskQuestions);
}

function goToStep(n) {
  document.querySelectorAll(".form-step").forEach(s => s.classList.remove("active"));
  const target = document.getElementById("step" + n);
  if (target) target.classList.add("active");
  for (let i = 1; i <= 5; i++) {
    const ind = document.getElementById("sind-" + i);
    const con = document.getElementById("scon-" + i);
    if (ind) {
      ind.classList.remove("active","done");
      if (i < n) ind.classList.add("done"); else if (i === n) ind.classList.add("active");
    }
    if (con) con.classList.toggle("done", i < n);
  }
  const fill = document.getElementById("progressFill");
  const label = document.getElementById("progressLabel");
  if (fill) fill.style.width = ((n - 1) / 4 * 100) + "%";
  if (label) label.textContent = `Step ${n} of 5`;
  currentStep = n;
  window.scrollTo({top: 0, behavior: "smooth"});
}

function collectStep(step) {
  if (step === 1) {
    formData.mainProblem = document.getElementById("mainProblem")?.value.trim() || "";
    const d = document.querySelector('input[name="duration"]:checked');
    formData.duration = d ? d.value : "";
    formData.severity = parseInt(document.getElementById("severity")?.value || 5, 10);
  }
  if (step === 2) {
    formData.symptoms = Array.from(document.querySelectorAll("#symptomGrid input:checked")).map(x => x.value);
  }
  if (step === 3) {
    formData.age = parseInt(document.getElementById("age")?.value || 0, 10) || "";
    formData.weight = parseInt(document.getElementById("weight")?.value || 0, 10) || "";
    const g = document.querySelector('input[name="gender"]:checked'); formData.gender = g ? g.value : "";
    const p = document.querySelector('input[name="pregnancy"]:checked'); formData.pregnancy = p ? p.value : "";
  }
  if (step === 4) {
    formData.conditions = Array.from(document.querySelectorAll("#condGroup input:checked")).map(x => x.value);
    formData.medications = document.getElementById("medications")?.value.trim() || "";
    formData.allergies = document.getElementById("allergies")?.value.trim() || "";
    const d = document.querySelector('input[name="diet"]:checked'); formData.diet = d ? d.value : "";
    formData.lifestyle = Array.from(document.querySelectorAll(".lifestyle-chips input[type=checkbox]:checked")).map(x => x.value);
  }
}

function validateStep(step) {
  if (step === 1) {
    const p = document.getElementById("mainProblem")?.value.trim() || "";
    if (p.length < 10) { showToast("Please describe your main concern (at least 10 characters)."); return false; }
    if (!document.querySelector('input[name="duration"]:checked')) { showToast("Please select how long you have had this condition."); return false; }
  }
  if (step === 3) {
    const age = parseInt(document.getElementById("age")?.value || 0, 10);
    if (!age || age < 1 || age > 120) { showToast("Please enter a valid age."); return false; }
    if (!document.querySelector('input[name="gender"]:checked')) { showToast("Please select a gender."); return false; }
  }
  return true;
}

function goNext(step) {
  if (!validateStep(step)) return;
  collectStep(step);
  if (step === 1) {
    requestRiskQuestions().finally(() => goToStep(2));
    return;
  }
  if (step === 2) renderRiskQuestions();
  if (step === 4) buildReview();
  goToStep(step + 1);
}

function goPrev(step) { goToStep(step - 1); }

function requestRiskQuestions() {
  collectStep(1); collectStep(2);
  const box = document.getElementById("riskQuestionsBox");
  if (!box || !formData.mainProblem) return Promise.resolve();
  return fetch(`${API_BASE}/risk/questions`, {
    method: "POST",
    headers: {"Content-Type":"application/json", "Authorization": `Bearer ${getSession().token}`},
    body: JSON.stringify(formData)
  }).then(r => r.ok ? r.json() : {questions:[]})
    .then(data => {
      box.dataset.questions = JSON.stringify(data.questions || []);
      renderRiskQuestions();
    }).catch(() => { box.dataset.questions = "[]"; });
}

function renderRiskQuestions() {
  const box = document.getElementById("riskQuestionsBox");
  if (!box) return;
  let questions = [];
  try { questions = JSON.parse(box.dataset.questions || "[]"); } catch { questions = []; }
  if (!questions.length) {
    box.innerHTML = `<div class="risk-question-empty">The Risk Engine will use your assessment details to calculate priority.</div>`;
    return;
  }
  box.innerHTML = `<div class="risk-question-head"><span>🚨</span><div><strong>Dynamic Risk Check</strong><p>These questions are selected from your reported concern so the Risk Engine can assess priority.</p></div></div>` + questions.map(q => `
    <label class="risk-question"><span>${escapeHtml(q.question)}</span><select data-risk-key="${escapeHtml(q.id)}"><option value="">Select</option>${(q.options || []).map(o => `<option>${escapeHtml(o)}</option>`).join("")}</select></label>`).join("");
  box.querySelectorAll("select").forEach(sel => sel.addEventListener("change", e => {
    formData.follow_up_details[e.target.dataset.riskKey] = e.target.value;
    previewRisk();
  }));
}

async function previewRisk() {
  collectStep(1); collectStep(2); collectStep(3); collectStep(4);
  const el = document.getElementById("riskPreview");
  if (!el) return;
  try {
    const s = getSession();
    const r = await fetch(`${API_BASE}/risk/calculate`, {method:"POST", headers:{"Content-Type":"application/json","Authorization":`Bearer ${s.token}`}, body:JSON.stringify(formData)});
    const risk = await r.json();
    const cls = risk.level === "High" ? "risk-high" : risk.level === "Moderate" ? "risk-moderate" : "risk-low";
    el.innerHTML = `<div class="risk-preview-card ${cls}"><div class="risk-preview-title">${risk.level === "High" ? "🔴" : risk.level === "Moderate" ? "🟡" : "🟢"} ${escapeHtml(risk.priority)}</div><div class="risk-preview-meta">Risk indicators detected: <strong>${risk.risk_indicators}</strong></div><div class="risk-factors">${(risk.factors || []).slice(0,5).map(x=>`<div>✓ ${escapeHtml(x)}</div>`).join("")}</div><p>${escapeHtml(risk.recommended_action || "")}</p></div>`;
  } catch {}
}

function buildReview() {
  collectStep(4);
  const rb = document.getElementById("reviewBlock");
  if (!rb) return;
  const row = (k,v) => `<div class="rev-row"><span class="rev-key">${escapeHtml(k)}</span><span class="rev-val">${escapeHtml(v || "—")}</span></div>`;
  rb.innerHTML = `
    <div class="rev-section"><div class="rev-title">Main Concern</div>${row("Concern",formData.mainProblem)}${row("Duration",formData.duration)}${row("Severity",formData.severity + " / 10")}</div>
    <div class="rev-section"><div class="rev-title">Symptoms</div>${row("Selected",formData.symptoms.length ? formData.symptoms.join(", ") : "None selected")}</div>
    <div class="rev-section"><div class="rev-title">Profile</div>${row("Age",formData.age)}${row("Gender",formData.gender)}${row("Weight",formData.weight ? formData.weight + " kg" : "—")}${row("Pregnancy",formData.pregnancy || "—")}</div>
    <div class="rev-section"><div class="rev-title">Medical History</div>${row("Conditions",formData.conditions.length ? formData.conditions.join(", ") : "None")}${row("Medications",formData.medications || "None")}${row("Allergies",formData.allergies || "None")}${row("Diet",formData.diet || "Not specified")}${row("Lifestyle",formData.lifestyle.length ? formData.lifestyle.join(", ") : "None selected")}</div>`;
  previewRisk();
}

function showGenerating(show) { const el = document.getElementById("generatingOverlay"); if (el) el.style.display = show ? "flex" : "none"; }
function showToast(t) { const el = document.getElementById("toast"); if (!el) return; el.textContent = t; el.style.display = "block"; setTimeout(()=>el.style.display="none", 3500); }

async function submitForm() {
  if (!["c1","c2","c3","c4"].every(id => document.getElementById(id)?.checked)) { showToast("Please tick all four consent checkboxes to proceed."); return; }
  collectStep(1); collectStep(2); collectStep(3); collectStep(4); showGenerating(true);
  try {
    const s = requireLogin();
    const r = await fetch(`${API_BASE}/assessment`, {method:"POST", headers:{"Content-Type":"application/json","Authorization":`Bearer ${s.token}`}, body:JSON.stringify(formData)});
    const raw = await r.text();
    let data; try { data = JSON.parse(raw); } catch { throw new Error(`Backend returned invalid response (${r.status}).`); }
    if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
    localStorage.setItem("aarogyamitra_latest_report", JSON.stringify(data));
    showGenerating(false); location.href = "report.html";
  } catch (e) {
    console.error("ASSESSMENT ERROR:", e);
    showGenerating(false); showToast(e.message || "Unable to generate the report right now.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!requireLogin()) return;
  buildSymptomGrid();
  const slider = document.getElementById("severity");
  if (slider) {
    slider.addEventListener("input", e => updateSeverity(e.target.value));
    slider.addEventListener("change", e => updateSeverity(e.target.value));
    updateSeverity(slider.value);
  }
  document.querySelectorAll('input[name="duration"]').forEach(x => x.addEventListener("change", () => { collectStep(1); requestRiskQuestions(); }));
});
