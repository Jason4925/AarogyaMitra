const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "http://localhost:8000";

function getSession() {
  try { return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null"); }
  catch { return null; }
}
function authHeaders() {
  const s = getSession();
  return s && s.token ? {"Authorization": `Bearer ${s.token}`} : {};
}
function requireLogin(requiredRole = null) {
  const s = getSession();
  if (!s || !s.token) { window.location.href = "login.html"; return null; }
  if (requiredRole && s.role !== requiredRole) { window.location.href = "dashboard.html"; return null; }
  return s;
}

async function api(path, options = {}, timeoutMs = 5000) {
  const headers = {...authHeaders(), ...(options.headers || {})};
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(API_BASE + path, {...options, headers, cache: "no-store", signal: controller.signal});
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || data.error || `HTTP ${r.status}`);
    return data;
  } catch (e) {
    if (e?.name === "AbortError") throw new Error("Request timed out. Please try again.");
    throw e;
  } finally { clearTimeout(timer); }
}
function escapeHtml(text) {
  const d = document.createElement("div"); d.textContent = String(text ?? ""); return d.innerHTML;
}
function riskIcon(level) { return level === "High" ? "🔴" : level === "Moderate" ? "🟡" : "🟢"; }

async function loadDashboardSnapshot() {
  const title = document.getElementById("summaryTitle");
  const text = document.getElementById("summaryText");
  const riskBox = document.getElementById("dashboardRisk");
  if (!title || !text) return;
  const fallback = () => {
    title.textContent = "No recent health assessment";
    text.textContent = "Complete an assessment or use AI Chat to build your personal health context.";
    if (riskBox) riskBox.innerHTML = "<p class='portal-muted'>No risk assessment recorded yet.</p>";
  };
  try {
    const data = await api("/dashboard/summary");
    const latest = data.latest_report || null;
    const risk = data.risk || {};
    if (latest) {
      title.textContent = latest.mainProblem || "Recent health assessment";
      text.textContent = latest.created_at
        ? `Last assessment ${new Date(latest.created_at).toLocaleString("en-IN")}. Severity: ${latest.severity ?? "not recorded"}/10.`
        : "Your latest health assessment is available.";
      if (riskBox && risk.level) {
        riskBox.innerHTML = `<div class="risk-preview-card risk-${escapeHtml(String(risk.level).toLowerCase())}"><strong>${riskIcon(risk.level)} ${escapeHtml(risk.priority || `${risk.level} Priority`)}</strong><p>Risk score: ${escapeHtml(risk.score ?? "—")} · Indicators: ${escapeHtml(risk.risk_indicators ?? 0)}</p><div class="risk-factors">${(risk.factors || []).slice(0,4).map(x => `<div>✓ ${escapeHtml(x)}</div>`).join("")}</div></div>`;
      }
      return;
    }
    const hs = data.health_state || {};
    if (hs.symptoms?.length) {
      title.textContent = hs.symptoms.join(", ");
      text.textContent = hs.last_updated ? `Health context updated ${new Date(hs.last_updated).toLocaleString("en-IN")}. Severity: ${hs.severity ?? "not recorded"}.` : "Your current health context is available.";
      if (riskBox) riskBox.innerHTML = "<p class='portal-muted'>Complete an assessment to calculate a formal risk score.</p>";
    } else fallback();
  } catch (e) {
    console.warn("Dashboard snapshot:", e);
    fallback();
  }
}

async function loadDashboardAwareness() {
  const title = document.getElementById("awarenessTitle");
  const text = document.getElementById("awarenessText");
  if (!title || !text) return;
  const fallbackItems = [
    {title:"Track changes in your health",text:"Recording symptom duration, severity, medicines and changes over time can make conversations with clinicians more useful."},
    {title:"Know urgent warning signs",text:"Severe breathing difficulty, major bleeding, loss of consciousness, severe chest pain or stroke-like symptoms require immediate emergency attention."}
  ];
  try {
    const data = await api("/awareness", {}, 3000);
    const item = (data.items || [])[0] || fallbackItems[0];
    title.textContent = item.title;
    text.textContent = item.text;
  } catch (e) {
    console.warn("Awareness:", e);
    const item = fallbackItems[0];
    title.textContent = item.title;
    text.textContent = item.text;
  }
}

async function loadHealthIntelligence(){
  const s=getSession(); if(!s||!s.token) return;
  const riskBox=document.getElementById("dashboardRisk");
  const timeline=document.getElementById("dashboardTimeline");
  const followBox=document.getElementById("followupBox");
  try{
    const [tl,fu,latest]=await Promise.all([
      api("/timeline", {}, 5000),
      api("/followup", {}, 5000),
      api("/latest-report", {}, 5000).catch(()=>({}))
    ]);
    const events=tl.events||[];
    const latestRisk=(latest.risk_engine||latest.risk||{});
    if(riskBox && latestRisk.level){
      riskBox.innerHTML=`<div class="risk-preview-card risk-${String(latestRisk.level).toLowerCase()}"><strong>${riskIcon(latestRisk.level)} ${escapeHtml(latestRisk.priority||latestRisk.level+" Priority")}</strong><p>Risk score: ${escapeHtml(latestRisk.score??"—")} · Indicators: ${escapeHtml(latestRisk.risk_indicators??0)}</p></div>`;
    }
    if(timeline){
      timeline.innerHTML=events.length?`<div class="timeline-wrap">${events.slice(0,8).map(ev=>`<div class="timeline-item"><span class="timeline-dot"></span><div class="timeline-date">${new Date(ev.timestamp).toLocaleDateString("en-IN",{month:"short",day:"numeric"})}</div><div class="timeline-title">${escapeHtml(ev.title||ev.event_type||"Health event")} ${ev.urgency?riskIcon(ev.urgency):""}</div><div class="timeline-summary">${escapeHtml(ev.summary||"")} ${ev.severity?` · ${escapeHtml(ev.severity)}/10`:""}</div></div>`).join("")}</div>`:"<p class='portal-muted'>Your health journey will appear here after your first assessment.</p>";
    }
    if(followBox){
      const item=fu.followup;
      if(!item){
        followBox.innerHTML="<p class='portal-muted'>No follow-up is currently due.</p>";
      } else {
        followBox.innerHTML=`<div class='followup-card'><h3>👋 How are you feeling today?</h3><p class='portal-muted'>Previous concern: <strong>${escapeHtml(item.concern)}</strong></p><div class='followup-buttons'><button class='btn-primary' onclick='submitFollowup("better")'>🟢 Better</button><button class='btn-ghost' onclick='submitFollowup("same")'>🟡 Same</button><button class='btn-ghost' onclick='submitFollowup("worse")'>🔴 Worse</button></div><div style='margin-top:12px'><label class='handoff-label'>Today's severity <input id='followupSeverity' type='range' min='1' max='10' value='${item.previous_severity||5}' style='width:100%'></label><div id='followupSeverityValue'>${item.previous_severity||5}/10</div></div><div id='followupMsg' class='portal-muted' style='margin-top:10px'></div></div>`;
        const sl=document.getElementById('followupSeverity');
        if(sl)sl.oninput=()=>document.getElementById('followupSeverityValue').textContent=sl.value+'/10';
      }
    }
  }catch(e){
    console.warn("Health intelligence:",e);
    if(timeline) timeline.innerHTML="<p class='portal-muted'>Health journey is temporarily unavailable. Please refresh in a moment.</p>";
    if(followBox) followBox.innerHTML="<p class='portal-muted'>Follow-up information is temporarily unavailable.</p>";
  }
}

async function submitFollowup(comparison){
  const sev=parseInt(document.getElementById('followupSeverity')?.value||5,10);
  try{const d=await api('/followup/check-in',{method:'POST',body:JSON.stringify({comparison,severity:sev,notes:''})});document.getElementById('followupMsg').textContent=d.message;loadHealthIntelligence();}catch(e){document.getElementById('followupMsg').textContent=e.message;}
}

document.addEventListener("DOMContentLoaded",()=>{
  const s=requireLogin(); if(!s)return;
  const logout=document.getElementById("logoutBtn");
  if(logout) logout.onclick=async()=>{try{await api("/logout",{method:"POST"},2500);}catch{} localStorage.removeItem("aarogyamitra_session");localStorage.removeItem(`aarogyamitra_chat_view_${s.user_id}`);window.location.href="index.html";};
  const welcome=document.getElementById("welcomeName"); if(welcome) welcome.textContent=`Welcome, ${s.name||"User"}`;
  loadDashboardSnapshot();
  loadDashboardAwareness();
  loadHealthIntelligence();
});
