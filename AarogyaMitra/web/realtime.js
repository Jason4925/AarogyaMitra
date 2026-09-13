(function(){
  const cfg=window.AAROGYAMITRA_CONFIG||{};
  window.startAarogyaRealtime=function(onSignal){
    if(!cfg.SUPABASE_URL || !cfg.SUPABASE_PUBLISHABLE_KEY || !window.supabase) return null;
    try{
      const client=window.supabase.createClient(cfg.SUPABASE_URL,cfg.SUPABASE_PUBLISHABLE_KEY);
      const channel=client.channel('aarogyamitra-admin-signals')
        .on('postgres_changes',{event:'INSERT',schema:'public',table:'dashboard_signals'},payload=>{if(typeof onSignal==='function')onSignal(payload.new)})
        .subscribe();
      window.__aarogyaRealtime={client,channel};
      return channel;
    }catch(e){console.warn('Realtime unavailable:',e);return null;}
  };
})();
