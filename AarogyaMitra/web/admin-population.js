const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "https://aarogyamitra-zp8i.onrender.com";

function getAdminSession(){
  try { return JSON.parse(localStorage.getItem("aarogyamitra_session") || "null"); }
  catch { return null; }
}

function esc(value){
  const d=document.createElement("div");
  d.textContent=String(value ?? "");
  return d.innerHTML;
}

async function requestJSON(path, timeoutMs=8000){
  const session=getAdminSession();
  if(!session?.token) throw new Error("Admin login required.");
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(), timeoutMs);
  try{
    const response=await fetch(API_BASE+path,{
      method:"GET",
      headers:{Accept:"application/json",Authorization:`Bearer ${session.token}`},
      cache:"no-store",
      signal:controller.signal
    });
    const raw=await response.text();
    let data={};
    try{data=raw?JSON.parse(raw):{};}catch{}
    if(!response.ok){
      let msg=data.detail||data.error||`Request failed (${response.status})`;
      if(Array.isArray(data.detail)) msg=data.detail.map(x=>x.msg||x.message||"Invalid request").join(", ");
      throw new Error(msg);
    }
    return data;
  }finally{clearTimeout(timer);}
}

function renderPopulation(data){
  const cards=document.getElementById("cards");
  const symptoms=document.getElementById("symptoms");
  const locations=document.getElementById("locations");
  if(cards){
    const dist=data.risk_distribution||{};
    cards.innerHTML=[
      ["Users", data.total_users ?? 0],
      ["Reports", data.total_reports ?? 0],
      ["High-priority rate", `${data.high_priority_rate ?? 0}%`],
      ["High/Critical", (dist.High||0)+(dist.Critical||0)]
    ].map(x=>`<div class="analytics-card"><div class="stat-label">${esc(x[0])}</div><div class="stat-value">${esc(x[1])}</div></div>`).join("");
  }
  if(symptoms){
    symptoms.innerHTML=(data.top_symptoms||[]).map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.count)}</td><td>${esc(x.share)}%</td></tr>`).join("")||'<tr><td colspan="3">No aggregated symptom data yet.</td></tr>';
  }
  if(locations){
    locations.innerHTML=(data.top_locations||[]).map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.count)}</td></tr>`).join("")||'<tr><td colspan="2">No location data yet.</td></tr>';
  }
}

function renderOutbreak(data){
  const signals=document.getElementById("signals");
  if(!signals)return;
  signals.innerHTML=(data.signals||[]).map(x=>`<div class="signal-card"><strong>⚠️ ${esc(x.signal)}</strong><p class="portal-muted">${esc(x.count)} current reports · previous ${esc(x.previous_count)} · ${esc(x.change_percent===null?"baseline unavailable":x.change_percent+"% vs previous 7 days")} · ${esc(x.confidence)} confidence</p><span class="readiness-status planned">${esc(x.status)}</span></div>`).join("")||'<div class="signal-card"><strong>No current signal</strong><p class="portal-muted">No configured symptom-cluster threshold was reached.</p></div>';
}

async function load(){
  const status=document.getElementById("status");
  if(!getAdminSession()?.token){location.replace("admin-login.html");return;}
  status.textContent="Loading population analytics…";
  const [population,outbreak]=await Promise.allSettled([
    requestJSON("/admin/population-analytics"),
    requestJSON("/admin/outbreak-signals")
  ]);
  let loaded=0;
  if(population.status==="fulfilled"){
    renderPopulation(population.value);
    loaded++;
  }else{
    const msg=population.reason?.name==="AbortError"?"Population analytics request timed out.":population.reason?.message||"Population analytics unavailable.";
    status.innerHTML=`<strong>Population analytics unavailable.</strong><p class="portal-muted">${esc(msg)}</p>`;
    document.getElementById("cards").innerHTML='<div class="analytics-card"><div class="stat-label">Status</div><div class="stat-value">Unavailable</div></div>';
    document.getElementById("symptoms").innerHTML='<tr><td colspan="3">Population data unavailable.</td></tr>';
    document.getElementById("locations").innerHTML='<tr><td colspan="2">Population data unavailable.</td></tr>';
  }
  if(outbreak.status==="fulfilled"){renderOutbreak(outbreak.value);loaded++;}
  else{document.getElementById("signals").innerHTML='<div class="signal-card"><strong>Outbreak signals unavailable</strong><p class="portal-muted">'+esc(outbreak.reason?.message||"Try again shortly.")+'</p></div>';}
  if(loaded>0 && population.status==="fulfilled") status.innerHTML=`<strong>Data generated:</strong> ${esc(population.value.generated_at||"")} · ${esc(population.value.disclaimer||"")}`;
  if(population.status!=="fulfilled" && outbreak.status!=="fulfilled") status.innerHTML='<strong>Population analytics unavailable.</strong><p class="portal-muted">Please confirm the backend is running and that the admin session is valid.</p>';
}

document.addEventListener("DOMContentLoaded",()=>{
  document.getElementById("logout")?.addEventListener("click",async()=>{
    const session=getAdminSession();
    localStorage.removeItem("aarogyamitra_session");
    try{if(session?.token) await fetch(API_BASE+"/logout",{method:"POST",headers:{Authorization:`Bearer ${session.token}`},keepalive:true});}catch{}
    location.replace("admin-login.html");
  });
  load().catch(e=>{const status=document.getElementById("status"); if(status)status.innerHTML=`<strong>Population analytics unavailable.</strong><p class="portal-muted">${esc(e.message||"Unexpected error")}</p>`;});
});
