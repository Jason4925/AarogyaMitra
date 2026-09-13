(function () {
  const LIMIT = 5;
  const TABLE_TARGETS = [
    '#evaluationsTable', '#symptomTable', '#symptoms', '#locations',
    '#usersTable', '#aiEventsTable', '#eventsTable', '#auditTable',
    '#reportsTable'
  ];
  const LIST_TARGETS = [
    '#historyPanel', '#emergencyPanel', '#recordTimeline',
    '#publicHealthGrid', '#outbreakSignals', '#signals', '#chatBox'
  ];

  function buttonFor(target, hiddenCount, expanded) {
    let btn = target.parentElement?.querySelector(`.view-more-btn[data-target-id="${CSS.escape(target.id)}"]`);
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'view-more-btn';
      btn.dataset.targetId = target.id;
      target.insertAdjacentElement('afterend', btn);
    }
    btn.textContent = expanded ? 'Show less ↑' : `View more (${hiddenCount}) ↓`;
    btn.setAttribute('aria-expanded', String(expanded));
    return btn;
  }

  function prepareList(target) {
    const id = target.id;
    if (!id) return;

    let items = Array.from(target.children).filter(el => !el.classList.contains('view-more-skip'));
    if (!items.length) return;

    // Some cards include placeholder/error content. Don't collapse a single placeholder.
    if (items.length <= LIMIT) {
      items.forEach(el => el.classList.remove('view-more-hidden'));
      const old = target.parentElement?.querySelector(`.view-more-btn[data-target-id="${CSS.escape(id)}"]`);
      old?.remove();
      return;
    }

    const expanded = target.dataset.viewMoreExpanded === 'true';
    items.forEach((el, index) => {
      el.classList.toggle('view-more-hidden', !expanded && index >= LIMIT);
    });

    const hiddenCount = items.length - LIMIT;
    const btn = buttonFor(target, hiddenCount, expanded);
    btn.onclick = () => {
      target.dataset.viewMoreExpanded = expanded ? 'false' : 'true';
      prepareList(target);
    };
  }

  function prepareTable(tbody) {
    if (!tbody.id) return;
    const rows = Array.from(tbody.querySelectorAll(':scope > tr'));
    if (rows.length <= LIMIT) {
      rows.forEach(row => row.classList.remove('view-more-hidden'));
      tbody.parentElement?.parentElement?.querySelector(`.view-more-btn[data-target-id="${CSS.escape(tbody.id)}"]`)?.remove();
      return;
    }

    const expanded = tbody.dataset.viewMoreExpanded === 'true';
    rows.forEach((row, index) => {
      row.classList.toggle('view-more-hidden', !expanded && index >= LIMIT);
    });

    const parent = tbody.closest('table') || tbody.parentElement;
    let btn = parent.parentElement?.querySelector(`.view-more-btn[data-target-id="${CSS.escape(tbody.id)}"]`);
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'view-more-btn';
      btn.dataset.targetId = tbody.id;
      parent.insertAdjacentElement('afterend', btn);
    }

    btn.textContent = expanded ? 'Show less ↑' : `View more (${rows.length - LIMIT}) ↓`;
    btn.setAttribute('aria-expanded', String(expanded));
    btn.onclick = () => {
      tbody.dataset.viewMoreExpanded = expanded ? 'false' : 'true';
      prepareTable(tbody);
    };
  }

  function apply() {
    TABLE_TARGETS.forEach(selector => {
      const el = document.querySelector(selector);
      if (el) prepareTable(el);
    });

    LIST_TARGETS.forEach(selector => {
      const el = document.querySelector(selector);
      if (el) prepareList(el);
    });
  }

  let timer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(apply, 80);
  });

  function start() {
    apply();
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
