function formatAIText(text) {
  const src = String(text ?? "").replace(/\r/g, "").trim();
  if (!src) return "<p>No response was generated.</p>";

  const esc = (v) => {
    const d = document.createElement("div");
    d.textContent = v;
    return d.innerHTML;
  };
  let out = [];
  let inList = false;

  const inline = (v) => {
    return esc(v)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  };

  for (const raw of src.split("\n")) {
    const line = raw.trim();
    if (!line) {
      if (inList) { out.push("</ul>"); inList = false; }
      continue;
    }
    if (/^#{1,3}\s+/.test(line)) {
      if (inList) { out.push("</ul>"); inList = false; }
      const level = Math.min(3, line.match(/^#+/)[0].length);
      out.push(`<h${level + 2}>${inline(line.replace(/^#{1,3}\s+/, ""))}</h${level + 2}>`);
      continue;
    }
    if (/^[-*•]\s+/.test(line) || /^\d+[.)]\s+/.test(line)) {
      if (!inList) { out.push("<ul>"); inList = true; }
      out.push(`<li>${inline(line.replace(/^([-*•]|\d+[.)])\s+/, ""))}</li>`);
      continue;
    }
    if (/^>\s?/.test(line)) {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(`<blockquote>${inline(line.replace(/^>\s?/, ""))}</blockquote>`);
      continue;
    }
    if (inList) { out.push("</ul>"); inList = false; }
    out.push(`<p>${inline(line)}</p>`);
  }
  if (inList) out.push("</ul>");
  return out.join("");
}

document.addEventListener("DOMContentLoaded", async () => {
  const session = requireLogin();
  if (!session) return;

  const box = document.getElementById("chatBox");
  const input = document.getElementById("chatInput");
  const send = document.getElementById("sendBtn");
  const clear = document.getElementById("clearHistoryBtn");
  const voiceBtn = document.getElementById("voiceInputBtn");
  const readBtn = document.getElementById("readAloudBtn");
  let latestAssistantText = "";
  const storageKey = `aarogyamitra_chat_view_${session.user_id}`;
  let view = [];

  try { view = JSON.parse(localStorage.getItem(storageKey) || "[]"); } catch { view = []; }

  function render() {
    box.innerHTML = view.map(m => {
      const user = m.role === "user";
      return `<article class="chat-message-card ${user ? "chat-user" : "chat-ai"}">
        <div class="chat-message-top">
          <span class="chat-sender">${user ? "You" : "AarogyaMitra"}</span>
          <span class="chat-time">${m.time ? new Date(m.time).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}) : ""}</span>
        </div>
        <div class="chat-message-content">${user ? `<p>${escapeHtml(m.content)}</p>` : formatAIText(m.content)}${(!user && m.do_not_delay) ? `<div class="emergency-chat-card"><strong>🚨 Do not delay emergency care.</strong><p>Seek immediate professional medical help. Your emergency escalation has been recorded.</p>${m.emergency_event_id ? `<button class="btn-primary btn-sm acknowledge-emergency" data-event="${m.emergency_event_id}">I understand — I will seek care</button>` : ""}</div>` : ""}${(!user && m.sources?.length) ? `<div class="source-citations"><div class="source-title">Relevant sources</div>${m.sources.map(src=>`<a href="${escapeHtml(src.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(src.title)}</strong><span>${escapeHtml(src.source)}</span></a>`).join('')}</div>` : ''}</div>
      </article>`;
    }).join("");
    box.scrollTop = box.scrollHeight;
  }

  function push(role, content) {
    view.push({ role, content, time: new Date().toISOString() });
  }

  async function loadHistory() {
    try {
      const data = await api(`/history/${encodeURIComponent(session.user_id)}`);
      view = (data.history || []).map(x => ({ role: x.role, content: x.message, sources: [], time: "" }));
      localStorage.setItem(storageKey, JSON.stringify(view));
    } catch (e) {
      console.warn("History load:", e);
    }
    render();
  }

  async function sendMessage(text = null) {
    const message = (text ?? input.value).trim();
    if (!message) return;
    input.value = "";
    push("user", message);
    push("assistant", "Thinking…");
    render();
    try {
      const data = await api("/ask", { method:"POST", body:JSON.stringify({message,user_id:session.user_id}) });
      latestAssistantText = data.response || "I couldn't generate a response.";
      view[view.length - 1] = { role:"assistant", content:latestAssistantText, sources:data.sources||[], time:new Date().toISOString(), do_not_delay:!!data.do_not_delay, emergency_event_id:data.emergency_event_id||null };
    } catch (e) {
      view[view.length - 1] = { role:"assistant", content:"I’m unable to reach AarogyaMitra right now. Please try again shortly.", time:new Date().toISOString() };
    }
    localStorage.setItem(storageKey, JSON.stringify(view));
    render();
  }

  box.addEventListener("click", async (e) => {
    const btn = e.target.closest(".acknowledge-emergency");
    if (!btn) return;
    try {
      const r = await api(`/emergency/acknowledge/${encodeURIComponent(btn.dataset.event)}`, {method:"POST"});
      if (r?.acknowledged) { btn.textContent = "Acknowledged"; btn.disabled = true; }
    } catch { alert("We could not record the acknowledgement. Please seek care now anyway."); }
  });

  send.onclick = () => sendMessage();
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  document.querySelectorAll(".quick-btn").forEach(btn => btn.addEventListener("click", () => sendMessage(btn.dataset.prompt || "")));

  clear.onclick = async () => {
    if (!confirm("Clear your conversation history?")) return;
    try {
      await api(`/history/${encodeURIComponent(session.user_id)}`, { method:"DELETE" });
      view = [];
      localStorage.removeItem(storageKey);
      render();
    } catch { alert("Unable to clear conversation history."); }
  };

  if (readBtn) readBtn.onclick = () => {
    if (!latestAssistantText || !('speechSynthesis' in window)) { alert('Text-to-speech is not available in this browser or no answer is ready.'); return; }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(latestAssistantText);
    const langMap = {Hindi:'hi-IN', Marathi:'mr-IN', Tamil:'ta-IN', Telugu:'te-IN', Bengali:'bn-IN', Gujarati:'gu-IN', Kannada:'kn-IN', Malayalam:'ml-IN', Punjabi:'pa-IN', Odia:'or-IN', Urdu:'ur-IN'};
    const preferred = session.preferred_language || 'English';
    u.lang = langMap[preferred] || 'en-IN';
    window.speechSynthesis.speak(u);
  };
  if (voiceBtn) voiceBtn.onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Voice input is not supported by this browser.'); return; }
    const rec = new SR(); rec.lang = session.preferred_language === 'Hindi' ? 'hi-IN' : session.preferred_language === 'Marathi' ? 'mr-IN' : 'en-IN'; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = e => { input.value = e.results[0][0].transcript; input.focus(); };
    rec.onerror = () => alert('Voice input could not be captured. Please try again.');
    rec.start();
  };

  await loadHistory();
});
