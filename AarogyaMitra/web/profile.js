const API_BASE = window.AAROGYAMITRA_CONFIG?.API_BASE || "https://aarogyamitra-zp8i.onrender.com/";

function getSession(){try{return JSON.parse(localStorage.getItem("aarogyamitra_session")||"null");}catch{return null;}}
function escapeHtml(v){const d=document.createElement("div");d.textContent=String(v??"");return d.innerHTML;}
function requireLogin(){const s=getSession();if(!s?.token||!s?.user_id){location.replace("login.html");return null;}return s;}
async function api(path, options={}, timeoutMs=8000){const s=requireLogin(); if(!s) throw new Error("Login required."); const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),timeoutMs); try{const headers={Accept:"application/json",...(options.headers||{}),Authorization:`Bearer ${s.token}`}; if(options.body&&!headers["Content-Type"]) headers["Content-Type"]="application/json"; const r=await fetch(API_BASE+path,{...options,headers,cache:"no-store",signal:controller.signal}); const raw=await r.text(); let d={}; try{d=raw?JSON.parse(raw):{};}catch{} if(!r.ok){let msg=d.detail||d.error||`Request failed (${r.status})`; if(Array.isArray(d.detail))msg=d.detail.map(x=>x.msg||x.message||"Invalid request").join(", "); throw new Error(msg);} return d;}finally{clearTimeout(timer);}}

document.addEventListener("DOMContentLoaded",async()=>{
 const session=requireLogin(); if(!session)return;
 const $=id=>document.getElementById(id); const msg=$("profileMsg"); const save=$("saveProfile");
 const setMsg=(t,ok=false)=>{if(!msg)return;msg.textContent=t||"";msg.style.color=ok?"var(--green)":"var(--red)";};
 const setBusy=b=>{if(!save)return;save.disabled=b;save.textContent=b?"Saving…":"Save Profile";};
 try{
   const d=await api("/profile",{},8000);
   $("profileName").value=d.name||""; $("profilePhone").value=d.phone||""; $("profileAge").value=d.age??""; $("profileGender").value=d.gender||""; $("profileLocation").value=d.location||""; $("profileLanguage").value=d.preferred_language||"English"; $("profileEmergency").value=d.emergency_contact||""; $("profileAllergies").value=d.allergies||""; $("profileConditions").value=Array.isArray(d.conditions)?d.conditions.join(", "):"";
 }catch(e){setMsg(e.message||"Unable to load profile.");}
 save?.addEventListener("click",async()=>{
   setMsg(""); const ageRaw=$("profileAge").value.trim(); const age=ageRaw===""?"":Number(ageRaw);
   const payload={name:$("profileName").value.trim(),phone:$("profilePhone").value.trim(),age,gender:$("profileGender").value,location:$("profileLocation").value.trim(),preferred_language:$("profileLanguage").value||"English",emergency_contact:$("profileEmergency").value.trim(),allergies:$("profileAllergies").value.trim(),conditions:$("profileConditions").value.split(",").map(x=>x.trim()).filter(Boolean)};
   if(!payload.name){setMsg("Please enter your name.");return;}
   if(age!==""&&(!Number.isInteger(age)||age<1||age>120)){setMsg("Age must be between 1 and 120, or left blank.");return;}
   setBusy(true); try{const updated=await api("/profile",{method:"PUT",body:JSON.stringify(payload)},8000); localStorage.setItem("aarogyamitra_session",JSON.stringify({...getSession(),...updated})); setMsg("Profile saved successfully.",true);}catch(e){setMsg(e.message||"Unable to save profile.");}finally{setBusy(false);}
 });
});
