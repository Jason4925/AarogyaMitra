document.addEventListener('DOMContentLoaded',async()=>{
  const el=document.getElementById('publicHealthGrid');
  const lang=document.getElementById('publicLanguage');
  const render=items=>{
    el.innerHTML=(items||[]).map(x=>`<article class="public-health-card"><div class="intel-kicker">${escapeHtml(x.category)}</div><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.text)}</p>${x.source?`<a class="public-health-source" href="${escapeHtml(x.source.url)}" target="_blank" rel="noopener noreferrer">Source: ${escapeHtml(x.source.name)}</a>`:''}<span class="public-health-action">${escapeHtml(x.action)}</span></article>`).join('') || '<div class="portal-card"><p class="portal-muted">No public-health items available.</p></div>';
  };
  try{const initial=getSession()?.preferred_language||localStorage.getItem('aarogyamitra_public_language')||'English'; const d=await api('/public-health?language='+encodeURIComponent(initial),{},5000);render(d.items||[]);}catch(e){el.innerHTML='<div class="portal-card"><p class="portal-muted">Public-health content is temporarily unavailable. Please try again shortly.</p></div>';}
  if(lang){
    const saved=getSession()?.preferred_language||localStorage.getItem('aarogyamitra_public_language')||'English';
    lang.value=[...lang.options].some(o=>o.value===saved)?saved:'English';
    lang.addEventListener('change',async()=>{localStorage.setItem('aarogyamitra_public_language',lang.value);try{const d=await api('/public-health?language='+encodeURIComponent(lang.value),{},5000);render(d.items||[]);}catch{}});
  }
});