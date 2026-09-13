document.addEventListener('DOMContentLoaded', async () => {
  const s = requireLogin('admin');
  if (!s) return;

  const $ = id => document.getElementById(id);
  const usersTable = $('usersTable');
  const eventsTable = $('eventsTable');
  const reportsTable = $('reportsTable');
  const aiEventsTable = $('aiEventsTable');
  const auditTable = $('auditTable');
  const search = $('userSearch');
  let users = [];

  const renderUsers = () => {
    const q = (search?.value || '').trim().toLowerCase();
    const rows = users.filter(u => !q ||
      (u.name || '').toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q)
    );
    usersTable.innerHTML = rows.map(u => `
      <tr>
        <td>${escapeHtml(u.name)}</td>
        <td>${escapeHtml(u.email)}</td>
        <td>${escapeHtml(u.phone || '—')}</td>
        <td>${escapeHtml(u.created_at || '—')}</td>
        <td><button class="btn-ghost btn-sm view-user" data-id="${escapeHtml(u.user_id)}">View</button></td>
      </tr>`).join('') || '<tr><td colspan="5">No users found.</td></tr>';
    document.querySelectorAll('.view-user').forEach(b => {
      b.onclick = () => location.href = `admin-user.html?id=${encodeURIComponent(b.dataset.id)}`;
    });
  };

  const renderAiEvents = rows => {
    aiEventsTable.innerHTML = (rows || []).map(x => `
      <tr>
        <td>${escapeHtml(x.created_at || '—')}</td>
        <td><span class="badge ${String(x.event_type || '').includes('failure') || String(x.event_type || '').includes('emergency') ? 'badge-red' : 'badge-green'}">${escapeHtml(x.event_type || '—')}</span></td>
        <td>${escapeHtml(x.user_id || '—')}</td>
        <td>${escapeHtml(JSON.stringify(x.details || {}))}</td>
      </tr>`).join('') || '<tr><td colspan="4">No AI safety events.</td></tr>';
  };

  async function loadEvaluations() {
    try {
      const d = await api('/admin/evaluations', {}, 5000);
      const rows = d.evaluations || [];
      const pass = rows.filter(x => x.passed).length;
      $('evaluationSummary').textContent = rows.length ? `${pass}/${rows.length} recent evaluation runs passed.` : 'No evaluations run yet.';
      $('evaluationsTable').innerHTML = rows.map(x => `<tr><td>${escapeHtml(x.scenario_id)}</td><td class="${x.passed ? 'evaluation-pass' : 'evaluation-fail'}">${x.passed ? 'PASS' : 'FAIL'}</td><td>${escapeHtml((x.issues || []).join(', ') || '—')}</td><td>${escapeHtml(x.created_at || '—')}</td></tr>`).join('') || '<tr><td colspan="4">No evaluation results.</td></tr>';
    } catch {
      $('evaluationSummary').textContent = 'Evaluation data unavailable.';
      $('evaluationsTable').innerHTML = '<tr><td colspan="4">Evaluation data unavailable.</td></tr>';
    }
  }

  async function runEvaluations() {
    const b = $('runAllEvaluations');
    b.disabled = true; b.textContent = 'Running…';
    try {
      const sc = (await api('/admin/evaluation-scenarios', {}, 5000)).scenarios || [];
      for (const x of sc) {
        try { await api('/admin/evaluations/run', {method:'POST', body:JSON.stringify({scenario_id:x.id})}, 15000); } catch {}
      }
      await loadEvaluations();
    } finally {
      b.disabled = false; b.textContent = 'Run All Tests';
    }
  }

  async function loadPopulation() {
    try {
      const d = await api('/admin/population-analytics', {}, 5000);
      const dist = d.risk_distribution || {};
      $('populationCards').innerHTML = [['Reports', d.total_reports || 0], ['High risk', dist.High || 0], ['Moderate risk', dist.Moderate || 0], ['Low risk', dist.Low || 0]].map(x => `<div class="analytics-card"><div class="stat-label">${x[0]}</div><div class="stat-value">${x[1]}</div></div>`).join('');
      $('symptomTable').innerHTML = (d.top_symptoms || []).map(x => `<tr><td>${escapeHtml(x.name)}</td><td>${escapeHtml(x.count)}</td></tr>`).join('') || '<tr><td colspan="2">No aggregated symptom data yet.</td></tr>';
    } catch {
      $('populationCards').innerHTML = '<div class="portal-card"><p class="portal-muted">Population analytics unavailable.</p></div>';
      $('symptomTable').innerHTML = '<tr><td colspan="2">Population data unavailable.</td></tr>';
    }
  }

  async function loadOutbreaks() {
    try {
      const d = await api('/admin/outbreak-signals', {}, 5000);
      $('outbreakSignals').innerHTML = (d.signals || []).map(x => `<div class="signal-card"><strong>⚠️ ${escapeHtml(x.signal)}</strong><p class="portal-muted">${escapeHtml(x.count)} reports in the last ${escapeHtml(x.window_days)} days · ${escapeHtml(x.confidence)} confidence · ${escapeHtml(x.status)}</p></div>`).join('') || '<div class="signal-card"><strong>No current signal</strong><p class="portal-muted">No simple symptom-cluster threshold has been reached in the last 7 days.</p></div>';
    } catch {
      $('outbreakSignals').innerHTML = '<div class="signal-card">Early-warning data unavailable.</div>';
    }
  }

  async function safe(path, timeout=6000) {
    try { return {ok:true, data:await api(path, {}, timeout)}; }
    catch (error) { console.warn(`Admin request failed: ${path}`, error); return {ok:false,error}; }
  }

  async function loadReadiness() {
    const render = (containerId, statusId, rows, emptyText) => {
      const container = $(containerId);
      const status = $(statusId);
      if (!container || !status) return;
      if (!rows.length) {
        container.innerHTML = `<div class="readiness-card"><p class="readiness-notes">${escapeHtml(emptyText)}</p></div>`;
        status.textContent = 'No data';
        return;
      }
      const active = rows.filter(x => x.status === 'active').length;
      status.textContent = `${active}/${rows.length} active`;
      container.innerHTML = rows.map(x => `
        <article class="readiness-card">
          <div class="readiness-meta"><span>${escapeHtml(x.owner || 'AarogyaMitra')}</span><span class="readiness-status ${escapeHtml(x.status || 'planned')}">${escapeHtml(x.status || 'planned')}</span></div>
          <h4>${escapeHtml(x.name)}</h4>
          <p class="readiness-notes">${escapeHtml(x.notes || '')}</p>
          <div class="readiness-meta" style="margin-top:10px;margin-bottom:0"><span>Last reviewed</span><span>${escapeHtml(x.last_reviewed || '—')}</span></div>
        </article>`).join('');
    };
    try {
      const d = await api('/admin/readiness', {}, 5000);
      const rows = d.items || [];
      render('intelligenceGrid','intelligenceReadiness',rows.filter(x => x.category === 'intelligence'),'Intelligence data unavailable.');
      render('evidenceGrid','evidenceReadiness',rows.filter(x => x.category === 'evidence'),'Evidence/readiness data unavailable.');
    } catch (error) {
      console.warn('Readiness data failed', error);
      render('intelligenceGrid','intelligenceReadiness',[], 'Intelligence readiness could not be loaded.');
      render('evidenceGrid','evidenceReadiness',[], 'Evidence and scale readiness could not be loaded.');
    }
  }

  async function load() {
    // Reset status without implying zero data while requests are in flight.
    for (const id of ['userCount','messageCount','reportCount','eventCount','successCalls','failedCalls','aiConversations','aiEscalations','aiUncertain','safeEmergency','safeLowConfidence','safeUnsupported','safeHuman','safeApi']) {
      if ($(id)) $(id).textContent = '…';
    }

    const [analytics, usersRes, emergencies, reports, aiEvents, db, audit] = await Promise.all([
      safe('/admin/analytics'), safe('/admin/users'), safe('/admin/emergencies'), safe('/admin/reports'), safe('/admin/ai-events'), safe('/admin/database/status'), safe('/admin/audit-logs')
    ]);
    const adminStatus=$('adminDataStatus');
    const failures=[analytics,usersRes,emergencies,reports,aiEvents,db,audit].filter(x=>!x.ok);
    if(adminStatus) adminStatus.textContent=failures.length ? `${failures.length} admin data service(s) unavailable. Values below are shown only for services that responded.` : `All admin data services connected · ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`;

    if (analytics.ok) {
      const a = analytics.data;
      const ai = a.ai || {};
      const se = ai.safety_events || {};
      for (const [id,v] of [
        ['userCount',a.registered_users],['messageCount',a.conversation_messages],['reportCount',a.health_reports],['eventCount',a.emergency_events],['successCalls',a.successful_calls],['failedCalls',a.failed_calls],
        ['aiConversations',ai.total_conversations],['aiCompletion',`${ai.assessment_completion ?? 0}%`],['aiFallback',`${ai.fallback_responses ?? 0}%`],['aiCorrections',`${ai.user_corrections ?? 0}%`],['aiEscalations',ai.safety_escalations],['aiUncertain',ai.uncertain_responses],
        ['safeEmergency',se.emergency_detected],['safeLowConfidence',se.low_confidence],['safeUnsupported',se.unsupported_question],['safeHuman',se.human_escalation],['safeApi',se.api_failure]
      ]) if ($(id) && v !== undefined) $(id).textContent = v;
      const total=(a.successful_calls||0)+(a.failed_calls||0), sp=total?Math.round((a.successful_calls||0)/total*100):0;
      if($('successPct'))$('successPct').textContent=sp+'%';
      if($('failedPct'))$('failedPct').textContent=(100-sp)+'%';
      if($('successBar'))$('successBar').style.width=sp+'%';
      if($('failedBar'))$('failedBar').style.width=(100-sp)+'%';
    } else {
      for (const id of ['userCount','messageCount','reportCount','eventCount','successCalls','failedCalls','aiConversations','aiCompletion','aiFallback','aiCorrections','aiEscalations','aiUncertain','safeEmergency','safeLowConfidence','safeUnsupported','safeHuman','safeApi']) if($(id)) $(id).textContent = 'Unavailable';
    }

    if (usersRes.ok) { users=usersRes.data.users||[]; renderUsers(); }
    else { users=[]; usersTable.innerHTML='<tr><td colspan="5">User data unavailable.</td></tr>'; }

    if (emergencies.ok) {
      const rows=emergencies.data.events||[];
      eventsTable.innerHTML=rows.map(x=>`<tr><td>${escapeHtml(x.timestamp||'')}</td><td>${escapeHtml(x.user_name||x.user_id||'—')}</td><td>${escapeHtml(x.channel||'—')}</td><td>${escapeHtml(x.reason||'—')}</td><td><span class="badge ${x.call_success?'badge-green':'badge-red'}">${x.call_success?'Successful':'Failed'}</span></td><td>${escapeHtml(x.call_sid||'—')}</td></tr>`).join('')||'<tr><td colspan="6">No emergency events.</td></tr>';
    } else eventsTable.innerHTML='<tr><td colspan="6">Emergency data unavailable.</td></tr>';

    if (reports.ok) {
      const rows=reports.data.reports||[];
      reportsTable.innerHTML=rows.map(x=>`<tr><td>${escapeHtml(x.user_name||x.user_id||'')}</td><td>${escapeHtml(x.mainProblem||'—')}</td><td>${escapeHtml(x.severity||'—')}</td><td>${escapeHtml(x.created_at||'—')}</td></tr>`).join('')||'<tr><td colspan="4">No reports.</td></tr>';
    } else reportsTable.innerHTML='<tr><td colspan="4">Report data unavailable.</td></tr>';

    if (aiEvents.ok) renderAiEvents(aiEvents.data.events||[]);
    else aiEventsTable.innerHTML='<tr><td colspan="4">AI event data unavailable.</td></tr>';

    if (db.ok) {
      const d=db.data;
      if($('dbStatus')){$('dbStatus').textContent=d.connected?`Connected · ${d.database} · ${d.driver}`:'Database unavailable';$('dbStatus').style.color=d.connected?'var(--green)':'var(--red)';}
      if($('dbCounts'))$('dbCounts').textContent=Object.entries(d.counts||{}).map(([k,v])=>`${k}: ${v}`).join(' · ') || 'No records yet.';
    } else {
      if($('dbStatus')){$('dbStatus').textContent='Database status unavailable';$('dbStatus').style.color='var(--red)';}
      if($('dbCounts'))$('dbCounts').textContent='Could not read database counters.';
    }

    const posture = await safe('/admin/security/posture');
    if ($('securityPosture')) {
      if (posture.ok) { const d=posture.data; $('securityPosture').textContent=`DB ${d.database?.connected?'connected':'unavailable'} · Active sessions ${d.active_sessions??0} · Recent failed logins ${d.recent_failed_logins??0} · Revoked tokens ${d.revoked_tokens??0}`; }
      else $('securityPosture').textContent='Security posture unavailable.';
    }

    if (audit.ok) {
      const rows=audit.data.events||[];
      auditTable.innerHTML=rows.map(x=>`<tr><td>${escapeHtml(x.created_at||'')}</td><td>${escapeHtml(x.action||'')}</td><td>${escapeHtml((x.resource_type||'')+' / '+(x.resource_id||''))}</td><td>${escapeHtml(x.result||'')}</td></tr>`).join('')||'<tr><td colspan="4">No audit events.</td></tr>';
    } else auditTable.innerHTML='<tr><td colspan="4">Audit data unavailable.</td></tr>';

    await Promise.all([loadEvaluations(),loadPopulation(),loadOutbreaks(),loadReadiness()]);
    const rt=$('realtimeStatus'); if(rt) rt.innerHTML='<span class="status-dot-small"></span>Updated '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  }

  async function runBenchmark(){
    const box=$('benchmarkSummary'), results=$('benchmarkResults');
    if(box) box.textContent='Running benchmark…';
    if(results) results.innerHTML='';
    const r=await safe('/admin/benchmark', {}, 30000);
    if(!r.ok){ if(box) box.textContent='Benchmark unavailable.'; return; }
    const d=r.data; if(box) box.textContent=`Score ${d.score}% · ${d.passed}/${d.total} tests passed · ${d.generated_at}`;
    if(results) results.innerHTML=(d.results||[]).map(x=>`<div class="signal-card"><strong>${x.passed?'✅':'❌'} ${escapeHtml(x.title)}</strong><p class="portal-muted">${escapeHtml((x.issues||[]).join(', ')||'No safety issues reported')}</p></div>`).join('');
  }
  $('runBenchmark')?.addEventListener('click',runBenchmark);
  search?.addEventListener('input',renderUsers);
  $('refreshAdmin')?.addEventListener('click',load);
  $('runAllEvaluations')?.addEventListener('click',runEvaluations);
  $('adminLogout')?.addEventListener('click', async () => {
    const token=s.token;
    // Clear browser session immediately so logout never depends on API latency.
    localStorage.removeItem('aarogyamitra_session');
    try {
      await fetch(API_BASE + '/logout', {method:'POST',headers:{Authorization:`Bearer ${token}`},keepalive:true});
    } catch {}
    location.replace('admin-login.html?logged_out=1');
  });

  await load();
  if(window.startAarogyaRealtime){
    const ch=window.startAarogyaRealtime(()=>load());
    if(ch && $('realtimeStatus')) $('realtimeStatus').innerHTML='<span class="status-dot-small"></span>Realtime connected';
  }
  setInterval(load,30000);
});
