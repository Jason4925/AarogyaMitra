const API_BASE = window.AAROGYAMITRA_CONFIG = {
  API_BASE: "https://api.aarogyamitra.example"
};
const VERSION = "15";
function esc(v){const d=document.createElement("div");d.textContent=String(v??"");return d.innerHTML;}
function session(){try{return JSON.parse(localStorage.getItem("aarogyamitra_session")||"null");}catch{return null;}}
function storedReport(){try{return JSON.parse(localStorage.getItem("aarogyamitra_latest_report")||"null");}catch{return null;}}
function cachedHandoff(){try{return JSON.parse(localStorage.getItem("aarogyamitra_latest_handoff")||"null");}catch{return null;}}
function icon(level){return level==="High"?"🔴":level==="Moderate"?"🟡":"🟢";}
function fromReport(report,s){
  if(!report?.mainProblem)return null;
  const risk=report.risk_engine||report.risk||{}; const body=report.report||{};
  return {id:report.handoff_id||`local-${report.id||Date.now()}`,patient_name:report.user_name||s?.name||"Patient",generated_at:report.created_at||new Date().toISOString(),chief_concern:report.mainProblem,duration:report.duration||"",severity:report.severity??"",associated_symptoms:Array.isArray(report.symptoms)?report.symptoms:[],relevant_history:Array.isArray(report.conditions)?report.conditions:[],medications:report.medications||"",allergies:report.allergies||"",red_flags_checked:Array.isArray(risk.red_flags)?risk.red_flags:(Array.isArray(report.red_flags)?report.red_flags:[]),risk,questions_answered:report.questions_answered??Object.keys(report.follow_up_details||{}).length,key_findings:Array.isArray(body.key_findings)?body.key_findings:[],patient_description:report.mainProblem,timeline:Array.isArray(report.timeline)?report.timeline:(report.timeline_event?[report.timeline_event]:[]),next_steps:body.next_steps||risk.recommended_action||""};
}
function list(items,empty="None reported"){return Array.isArray(items)&&items.length?`<ul class="handoff-list">${items.map(v=>`<li>${esc(v)}</li>`).join("")}</ul>`:`<p class="portal-muted">${esc(empty)}</p>`;}
function render(h,s,source="saved"){
 const body=document.getElementById("handoffBody"); if(!body||!h)return;
 const risk=h.risk||{}, symptoms=h.associated_symptoms||[], history=h.relevant_history||[], flags=h.red_flags_checked||[], timeline=h.timeline||[], factors=risk.factors||[];
 body.innerHTML=`<section class="handoff-card handoff-hero-card"><div class="intel-kicker">AI-to-Doctor Handoff · ${source==="server"?"Synced":"Saved assessment"}</div><div class="handoff-hero-top"><div><h2>AarogyaMitra Handoff</h2><p class="portal-muted">A structured clinical discussion summary. It is not a diagnosis.</p></div><div class="handoff-risk-pill">${icon(risk.level)} ${esc((risk.priority||`${risk.level||"Low"} Priority`).toUpperCase())}</div></div><div class="handoff-meta-line">${esc(h.patient_name||s?.name||"Patient")} · ${esc(new Date(h.generated_at||Date.now()).toLocaleString("en-IN"))}</div></section>
 <section class="handoff-card"><div class="intel-kicker">Patient Summary</div><div class="handoff-grid"><div><div class="handoff-label">Chief concern</div><div class="handoff-value">${esc(h.chief_concern||"—")}</div></div><div><div class="handoff-label">Duration</div><div class="handoff-value">${esc(h.duration||"—")}</div></div><div><div class="handoff-label">Severity</div><div class="handoff-value">${esc(h.severity||"—")}/10</div></div><div><div class="handoff-label">Associated symptoms</div><div class="handoff-value">${list(symptoms,"None selected")}</div></div><div><div class="handoff-label">Relevant history</div><div class="handoff-value">${list(history)}</div></div><div><div class="handoff-label">Current medications</div><div class="handoff-value">${esc(h.medications||"None reported")}</div></div><div><div class="handoff-label">Known allergies</div><div class="handoff-value">${esc(h.allergies||"None reported")}</div></div><div><div class="handoff-label">Questions answered</div><div class="handoff-value">${esc(h.questions_answered??0)}</div></div><div><div class="handoff-label">Red flags checked</div><div class="handoff-value">${list(flags,"No emergency red flags detected")}</div></div></div></section>
 <section class="handoff-card"><div class="intel-kicker">Explainable Risk Engine</div><h3>${icon(risk.level)} ${esc(risk.priority||`${risk.level||"Low"} Priority`)}</h3><p><strong>Risk score:</strong> ${esc(risk.score??"—")}</p><div class="risk-factor-box">${factors.length?factors.map(f=>`<div class="risk-factor">✓ ${esc(f)}</div>`).join(""):`<p class="portal-muted">Limited structured risk information was available.</p>`}</div><p style="margin-top:14px"><strong>Recommended next step:</strong> ${esc(h.next_steps||"Discuss the symptoms with a qualified clinician.")}</p></section>
 <section class="handoff-card"><div class="intel-kicker">Key Findings</div>${list(h.key_findings,"No additional structured findings were recorded.")}<div style="margin-top:20px"><div class="handoff-label">Patient's own description</div><blockquote class="handoff-quote">“${esc(h.patient_description||h.chief_concern||"")}”</blockquote></div></section>
 <section class="handoff-card"><div class="intel-kicker">My Health Journey</div><h3>Timeline</h3>${timeline.length?`<div class="timeline-wrap" style="margin-top:14px">${timeline.slice().sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp)).map(ev=>`<div class="timeline-item"><span class="timeline-dot"></span><div class="timeline-date">${esc(new Date(ev.timestamp).toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"}))}</div><div class="timeline-title">${esc(ev.title||ev.event_type||"Health event")} ${ev.urgency?icon(ev.urgency):""}</div><div class="timeline-summary">${esc(ev.summary||"")}${ev.severity?` · Severity ${esc(ev.severity)}/10`:""}</div></div>`).join("")}</div>`:`<p class="portal-muted">No timeline events have been recorded yet.</p>`}</section>
 <section class="handoff-card"><div class="intel-kicker">Clinician Note</div><p class="portal-muted">Use this handoff as a structured starting point for discussion. Confirm symptoms, history, medications, allergies, examination findings and urgency directly with the patient.</p></section>`;
}
async function fetchJSON(path,s){const c=new AbortController(),t=setTimeout(()=>c.abort(),3500);try{const r=await fetch(`${API_BASE}${path}`,{headers:{Authorization:`Bearer ${s.token}`},cache:"no-store",signal:c.signal});const text=await r.text();let d={};try{d=text?JSON.parse(text):{};}catch{}if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`);return d;}finally{clearTimeout(t);}}
async function loadHandoff(){
 const body=document.getElementById("handoffBody"),s=session();if(!body)return;
 if(!s?.token){body.innerHTML=`<section class="portal-card"><h3>Login required</h3><p class="portal-muted">Please log in to view your Doctor Handoff.</p><a class="btn-primary btn-sm" href="login.html">Login →</a></section>`;return;}
 const local=fromReport(storedReport(),s)||cachedHandoff();
 if(local)render(local,s,"saved");
 else body.innerHTML=`<section class="portal-card"><h3>No handoff yet</h3><p class="portal-muted">Complete a health assessment first. The handoff is generated automatically.</p><a class="btn-primary btn-sm" href="assessment.html">Start Assessment →</a></section>`;
 try{const server=await fetchJSON(`/handoff/latest?v=${VERSION}`,s);if(server?.id||server?.chief_concern){localStorage.setItem("aarogyamitra_latest_handoff",JSON.stringify(server));render(server,s,"server");}}
 catch(e){console.warn("Handoff sync:",e);if(local){const note=document.createElement("div");note.className="handoff-sync-note";note.innerHTML=`<strong>Saved handoff displayed.</strong> Server synchronization is currently unavailable. <button class="btn-ghost btn-sm" id="retryHandoff">Retry</button>`;body.appendChild(note);document.getElementById("retryHandoff")?.addEventListener("click",()=>{note.remove();loadHandoff();});}}
}
document.addEventListener("DOMContentLoaded",()=>{
  const body=document.getElementById("handoffBody");
  const print=document.getElementById("printHandoff");
  if(print) print.addEventListener("click",()=>window.print());
  // Never leave a blank loading state.
  if(body && (!body.textContent.trim() || body.textContent.trim()==="Loading…")){
    body.innerHTML=`<section class="portal-card"><p class="portal-muted">Preparing your Doctor Handoff…</p></section>`;
  }
  loadHandoff();
  setTimeout(()=>{
    const b=document.getElementById("handoffBody");
    if(b && /Preparing your Doctor Handoff|Loading…/.test(b.textContent.trim())){
      b.innerHTML=`<section class="portal-card"><h3>Doctor Handoff could not be loaded</h3><p class="portal-muted">No saved assessment was found or the server is unavailable.</p><div class="followup-buttons"><a class="btn-primary btn-sm" href="assessment.html">Open Assessment</a><button class="btn-ghost btn-sm" onclick="loadHandoff()">Retry</button></div></section>`;
    }
  },5000);
});
