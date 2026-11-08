'use strict';
// Public metadata only: no tokens, inference, or model downloads.
window.LanguageModels = (() => {
  const cache = new Map(),
    pending = new Map(),
    ttl = 30 * 60 * 1000;
  const escape = (value) =>
    String(value ?? '').replace(
      /[&<>"']/g,
      (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
    );
  const reverse = Object.fromEntries(Object.entries(window.HF_ISO_MAP).map(([a, b]) => [b, a]));
  const tasks = [
    ['', 'All tasks'],
    ['text-generation', 'Text generation / LLM'],
    ['translation', 'Translation'],
    ['automatic-speech-recognition', 'Speech recognition'],
    ['text-to-speech', 'Text to speech'],
    ['sentence-similarity', 'Sentence similarity'],
    ['feature-extraction', 'Feature extraction'],
    ['fill-mask', 'Masked language modeling'],
  ];
  function codesFor(node) {
    if (!['language', 'dialect'].includes(node.level) || !/^[a-z]{3}$/.test(node.iso || ''))
      return [];
    return [...new Set([reverse[node.iso], node.iso].filter(Boolean))];
  }
  function modelLink(id) {
    if (typeof id !== 'string' || !/^[\w.-]+\/[\w.-]+$/.test(id)) return null;
    return 'https://huggingface.co/' + id.split('/').map(encodeURIComponent).join('/');
  }
  function selectModels(rows, codes, task) {
    const found = new Map();
    for (const m of rows) {
      const raw = m.cardData?.language,
        languages = (Array.isArray(raw) ? raw : [raw]).filter((x) => typeof x === 'string');
      const matched = languages.filter((x) => codes.includes(x));
      if (!modelLink(m.id) || !matched.length || (task && m.pipeline_tag !== task)) continue;
      const old = found.get(m.id);
      found.set(m.id, {
        ...m,
        languages,
        matched: [...new Set([...(old?.matched || []), ...matched])],
      });
    }
    return [...found.values()].sort((a, b) => (b.downloads || 0) - (a.downloads || 0)).slice(0, 8);
  }
  function hubURL(code, task) {
    const q = new URLSearchParams({ language: code, sort: 'downloads' });
    if (task) q.set('pipeline_tag', task);
    return 'https://huggingface.co/models?' + q;
  }
  async function query(code, task) {
    const key = code + '|' + task,
      hit = cache.get(key);
    if (hit && Date.now() - hit.time < ttl) return hit.rows;
    if (pending.has(key)) return pending.get(key);
    const work = (async () => {
      const ctrl = new AbortController(),
        timer = setTimeout(() => ctrl.abort(), 15000);
      try {
        const q = new URLSearchParams({
          filter: code,
          sort: 'downloads',
          direction: '-1',
          limit: '20',
          full: 'true',
          cardData: 'true',
        });
        if (task) q.set('pipeline_tag', task);
        const res = await fetch('https://huggingface.co/api/models?' + q, {
          signal: ctrl.signal,
          credentials: 'omit',
          referrerPolicy: 'no-referrer',
        });
        if (!res.ok) throw new Error('Hugging Face HTTP ' + res.status);
        const rows = await res.json();
        if (!Array.isArray(rows)) throw new Error('Unexpected model response');
        cache.set(key, { time: Date.now(), rows });
        return rows;
      } finally {
        clearTimeout(timer);
      }
    })();
    pending.set(key, work);
    try {
      return await work;
    } finally {
      pending.delete(key);
    }
  }
  function modelHTML(m) {
    const scope =
      m.languages.includes('multilingual') ||
      m.languages.some((x) => /^[a-z]{2,3}$/.test(x) && !m.matched.includes(x))
        ? 'Multiple language tags'
        : 'Matching language tag';
    const license = m.cardData?.license;
    return `<article class="hf-model"><a href="${escape(modelLink(m.id))}" target="_blank" rel="noopener noreferrer">${escape(m.id)} ↗</a><div class="hf-tags"><span>${escape(m.pipeline_tag || 'Task unspecified')}</span><span>${escape(scope)}</span></div><small>Matched: ${m.matched.map(escape).join(', ')} · ${Number(m.downloads || 0).toLocaleString()} downloads${typeof license === 'string' ? ' · ' + escape(license) : ''}</small></article>`;
  }
  function mount(host, node, options = {}) {
    const codes = codesFor(node);
    host.innerHTML = `<h3>🤗 Hugging Face models</h3>`;
    if (!codes.length) {
      host.insertAdjacentHTML(
        'beforeend',
        `<a class="hf-browse" href="https://huggingface.co/models?search=${encodeURIComponent(node.name)}" target="_blank" rel="noopener noreferrer">Search the name on Hugging Face ↗</a>`,
      );
      return;
    }
    host.insertAdjacentHTML(
      'beforeend',
      `<label class="hf-task-label">Model task<select class="hf-task" aria-label="Hugging Face model task">${tasks.map(([v, label]) => `<option value="${v}">${label}</option>`).join('')}</select></label><div class="hf-links"></div><div class="hf-status" role="status" aria-live="polite"></div><div class="hf-list"></div><button type="button" class="hf-retry" hidden>Retry loading models</button>`,
    );
    const task = host.querySelector('.hf-task'),
      status = host.querySelector('.hf-status'),
      list = host.querySelector('.hf-list'),
      links = host.querySelector('.hf-links'),
      retry = host.querySelector('.hf-retry');
    let revision = 0;
    async function load() {
      const version = ++revision,
        selectedTask = task.value;
      links.innerHTML = codes
        .map(
          (c) =>
            `<a class="hf-browse" href="${escape(hubURL(c, selectedTask))}" target="_blank" rel="noopener noreferrer">All ${escape(c)} models ↗</a>`,
        )
        .join('');
      status.textContent = 'Loading public model metadata from Hugging Face…';
      list.innerHTML = '';
      retry.hidden = true;
      const responses = await Promise.allSettled(codes.map((c) => query(c, selectedTask)));
      if (version !== revision || !host.isConnected) return;
      const good = responses.filter((r) => r.status === 'fulfilled'),
        failed = responses.length - good.length;
      const models = selectModels(
        good.flatMap((r) => r.value),
        codes,
        selectedTask,
      );
      list.innerHTML = models.map(modelHTML).join('');
      if (!good.length)
        status.textContent =
          'Could not reach Hugging Face. Use the links above or retry; this does not mean no models exist.';
      else if (!models.length)
        status.textContent =
          'No exact language-card matches in the returned sample. Other models or missing language metadata may exist; browse the Hub above.';
      else
        status.textContent = `${models.length} matching models · download-sorted sample, not an exhaustive list or quality ranking.`;
      if (failed && good.length)
        status.textContent += ' Some language-tag requests failed; results may be incomplete.';
      if (good.length) status.textContent += ' Loaded ' + new Date().toLocaleString() + '.';
      retry.hidden = !failed;
    }
    if (tasks.some(([v]) => v === options.task)) task.value = options.task;
    task.addEventListener('change', () => {
      if (typeof options.onTask === 'function') options.onTask(task.value);
      load();
    });
    retry.addEventListener('click', load);
    load();
  }
  return { mount, codesFor, selectModels, modelLink };
})();
