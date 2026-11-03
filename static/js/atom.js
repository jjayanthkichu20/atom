/* ============================================================
   ATOM PREMIER — Luxury UI JavaScript  |  Full Clean Rewrite
   All bugs fixed: field names, session load, job cards, apply
   ============================================================ */
'use strict';

/* ─── DEFAULT KEY ────────────────────────────────────────── */
const DEFAULT_OPENAI_KEY = '';

/* ─── STATE ──────────────────────────────────────────────── */
const state = {
  sessionId: (window.CURRENT_SESSION_ID || '029c1815-a1a1-48e6-929b-1f6909f28fd5'),
  provider: 'openai',
  model: 'gpt-4o-mini',
  apiKey: DEFAULT_OPENAI_KEY,
  jobs: [],
  currentJob: null,
  cvText: null,
  cvFilename: null,
  isTyping: false,
};

/* ─── DOM HELPERS ─────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);

/* ─── INIT ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  bindAllEvents();
  loadSessionData();   // loads history + jobs + profile in one request
  loadDbStats();
});

/* ═══════════════════════════════════════════════════════════
   EVENT BINDING
   ═══════════════════════════════════════════════════════════ */
function bindAllEvents() {
  /* Chat */
  $('chatForm')?.addEventListener('submit', handleChatSubmit);
  $('chatTextarea')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('chatForm')?.requestSubmit(); }
  });
  $('chatTextarea')?.addEventListener('input', autoResizeTA);

  /* CV Upload */
  const cvInput = $('cvFileInput');
  [$('attachCvBtn'), $('heroUploadCvBtn'), $('sidebarUploadCvBtn')].forEach(btn =>
    btn?.addEventListener('click', () => cvInput?.click())
  );
  cvInput?.addEventListener('change', (e) => {
    const f = e.target.files?.[0];
    if (f) uploadCv(f);
    e.target.value = '';
  });

  /* Drag-drop CV */
  const scrollArea = $('chatThreadScroll');
  scrollArea?.addEventListener('dragover', (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; });
  scrollArea?.addEventListener('drop', (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) uploadCv(f);
  });

  /* Sidebar / layout */
  $('collapseSidebarBtn')?.addEventListener('click', () => $('sidebar')?.classList.toggle('collapsed'));
  $('mobileMenuBtn')?.addEventListener('click', () => $('sidebar')?.classList.toggle('mobile-open'));
  [$('newSearchBtn'), $('quickNewSearchBtn')].forEach(btn => btn?.addEventListener('click', startNewSearch));

  /* DB Inspect */
  $('inspectDbBtn')?.addEventListener('click', showDbStats);

  /* API Key modal */
  [$('headerApiKeyBtn'), $('sidebarApiKeyBtn')].forEach(btn => btn?.addEventListener('click', openApiModal));
  $('closeApiKeyModalBtn')?.addEventListener('click', closeApiModal);
  $('apiKeyModalBackdrop')?.addEventListener('click', (e) => { if (e.target === $('apiKeyModalBackdrop')) closeApiModal(); });
  $('toggleKeyVisibility')?.addEventListener('click', () => {
    const inp = $('apiKeyInput');
    if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
  });
  $('testApiKeyBtn')?.addEventListener('click', testApiKey);
  $('saveApiKeyBtn')?.addEventListener('click', saveApiKey);

  /* Provider radio */
  document.querySelectorAll('input[name="apiProvider"]').forEach(r =>
    r.addEventListener('change', (e) => { state.provider = e.target.value; syncProviderCards(); })
  );

  /* Apply Drawer */
  $('closeApplyDrawerBtn')?.addEventListener('click', closeDrawer);
  $('cancelApplyBtn')?.addEventListener('click', closeDrawer);
  $('confirmApplyBtn')?.addEventListener('click', handleConfirmApply);
  $('applyModalBackdrop')?.addEventListener('click', (e) => { if (e.target === $('applyModalBackdrop')) closeDrawer(); });

  /* Tracker Modal */
  [$('openTrackerBtn'), $('openCvListBtn')].forEach(btn => btn?.addEventListener('click', openTracker));
  $('closeTrackerModalBtn')?.addEventListener('click', closeTracker);
  $('trackerModalBackdrop')?.addEventListener('click', (e) => { if (e.target === $('trackerModalBackdrop')) closeTracker(); });

  /* Target Job Description Match Modal */
  [$('sidebarMatchJdBtn'), $('heroMatchJdBtn')].forEach(btn => btn?.addEventListener('click', openJdModal));
  $('closeJdMatchModalBtn')?.addEventListener('click', closeJdModal);
  $('jdMatchModalBackdrop')?.addEventListener('click', (e) => { if (e.target === $('jdMatchModalBackdrop')) closeJdModal(); });
  $('analyzeJdBtn')?.addEventListener('click', handleAnalyzeJd);
  $('createJobFromJdBtn')?.addEventListener('click', handleCreateJobFromJd);

  /* Suggestion chips */
  document.querySelectorAll('.suggestion-chip').forEach(chip =>
    chip.addEventListener('click', () => {
      const ta = $('chatTextarea');
      if (ta && chip.dataset.prompt) { ta.value = chip.dataset.prompt; autoResizeTA(); ta.focus(); }
    })
  );

  /* Theme */
  $('themeToggleBtn')?.addEventListener('click', () => {
    const html = document.documentElement;
    html.setAttribute('data-theme', html.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
  });
}

/* ═══════════════════════════════════════════════════════════
   SESSION LOAD (history + jobs + profile)
   ═══════════════════════════════════════════════════════════ */
async function loadSessionData() {
  try {
    const res  = await fetch(`/api/session/${state.sessionId}`);
    const data = await res.json();

    /* Restore message history */
    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(msg => {
        if (msg.role === 'user')      appendUserMessage(msg.content);
        else if (msg.role === 'assistant') appendAtomMessage(msg.content);
      });
    } else {
      appendAtomMessage(
        'Welcome to **Atom Premier** — your executive AI career co-pilot.\n\n' +
        'I have curated **4 bespoke executive openings** from elite companies. ' +
        'Upload your CV to recalibrate match scores, or ask me anything.'
      );
    }

    /* Load jobs */
    if (data.jobs && data.jobs.length > 0) {
      state.jobs = data.jobs;
      renderJobCards(data.jobs);
    }

    /* Restore profile display */
    if (data.profile) updateProfileUI(data.profile);

  } catch (err) {
    appendAtomMessage('Atom is ready. Type a message or upload your CV to begin.');
  }
}

/* ═══════════════════════════════════════════════════════════
   CHAT
   ═══════════════════════════════════════════════════════════ */
async function handleChatSubmit(e) {
  e.preventDefault();
  const ta   = $('chatTextarea');
  const text = ta?.value.trim();
  if (!text || state.isTyping) return;

  appendUserMessage(text);
  ta.value = '';
  autoResizeTA();
  setTyping(true);

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        message:    text,
        api_key:    state.apiKey,
        provider:   state.provider,
        model:      state.model,
      }),
    });
    const data = await res.json();
    setTyping(false);

    if (data.reply) {
      appendAtomMessage(data.reply);
    } else if (data.error) {
      appendAtomMessage(`⚠️ ${esc(data.error)}`, true);
    }

    /* Refresh job cards if returned */
    if (data.jobs && data.jobs.length > 0) {
      state.jobs = data.jobs;
      renderJobCards(data.jobs);
    }
  } catch (err) {
    setTyping(false);
    appendAtomMessage('Connection error — please ensure the server is running.', true);
  }
  scrollBottom();
}

function autoResizeTA() {
  const ta = $('chatTextarea');
  if (!ta) return;
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
}

function setTyping(show) {
  const ind = $('atomTypingIndicator');
  if (ind) ind.style.display = show ? 'flex' : 'none';
  const btn = $('sendBtn');
  if (btn) btn.disabled = show;
  state.isTyping = show;
  if (show) scrollBottom();
}

function appendUserMessage(text) {
  const stream = $('messagesStream');
  if (!stream) return;
  const el = document.createElement('div');
  el.className = 'message-row-user';
  el.innerHTML = `<div class="message-bubble-user">${esc(text)}</div>`;
  stream.appendChild(el);
  scrollBottom();
}

function appendAtomMessage(markdown, isError = false) {
  const stream = $('messagesStream');
  if (!stream) return;
  const el = document.createElement('div');
  el.className = 'message-row-atom';
  el.innerHTML = `
    <div class="atom-avatar-sm">✦</div>
    <div class="message-bubble-atom${isError ? ' error-bubble' : ''}">
      <div class="atom-msg-header"><span class="atom-name-label">ATOM PREMIER</span></div>
      <div class="atom-msg-content">${fmtMd(markdown)}</div>
    </div>`;
  stream.appendChild(el);
  scrollBottom();
}

function scrollBottom() {
  requestAnimationFrame(() => {
    const s = $('chatThreadScroll');
    if (s) s.scrollTop = s.scrollHeight;
  });
}

/* ═══════════════════════════════════════════════════════════
   JOB CARDS
   ═══════════════════════════════════════════════════════════ */
function renderJobCards(jobs) {
  /* Remove old section */
  document.getElementById('jobCardsSection')?.remove();

  if (!jobs || jobs.length === 0) return;

  const section = document.createElement('div');
  section.id = 'jobCardsSection';
  section.className = 'jobs-section';
  section.setAttribute('id', 'quick-apply');  // scroll anchor

  section.innerHTML = `
    <div class="jobs-section-header">
      <div class="jobs-section-title">✦ Curated Executive Openings — ${jobs.length} Bespoke Matches</div>
    </div>
    <div class="job-cards-grid" id="jobCardsGrid"></div>`;

  const grid = section.querySelector('#jobCardsGrid');
  jobs.forEach(job => grid.appendChild(buildJobCard(job)));

  /* Insert before messagesStream */
  const stream = $('messagesStream');
  stream?.parentNode?.insertBefore(section, stream);
}

function buildJobCard(job) {
  const card = document.createElement('div');
  card.className = 'job-card';

  const score = job.match_score || 92;
  const tags  = [job.location || 'Remote', job.type || 'Full-time', ...(job.tech_stack || []).slice(0, 2)];

  card.innerHTML = `
    <div class="job-card-header">
      <div class="job-title-wrap">
        <div class="job-title">${esc(job.title)}</div>
        <div class="job-company">${esc(job.company)}</div>
      </div>
      <div class="match-score-pill">${score}% Match</div>
    </div>
    <div class="job-meta">${tags.map(t => `<span class="job-tag">${esc(t)}</span>`).join('')}</div>
    <div class="job-desc">${esc(job.description || 'Elite executive opportunity.')}</div>
    <div class="job-card-footer">
      <div class="job-salary">${esc(job.salary || '$150K–$220K')}</div>
      <button class="apply-now-btn" type="button">✦ Apply Now</button>
    </div>`;

  card.querySelector('.apply-now-btn').addEventListener('click', (e) => { e.stopPropagation(); openDrawer(job); });
  card.addEventListener('click', () => openDrawer(job));
  return card;
}

/* ═══════════════════════════════════════════════════════════
   CV UPLOAD
   ═══════════════════════════════════════════════════════════ */
async function uploadCv(file) {
  const ALLOWED = ['.pdf', '.docx', '.doc', '.txt', '.md'];
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
  if (!ALLOWED.includes(ext)) {
    appendAtomMessage('⚠️ Unsupported format. Please upload PDF, DOCX, or TXT.', true);
    return;
  }

  const label = $('attachCvLabel');
  if (label) label.textContent = '⏳ Uploading…';
  setTyping(true);

  const form = new FormData();
  form.append('cv_file', file);           // field name server expects
  form.append('sessionId', state.sessionId);

  try {
    const res  = await fetch('/api/upload-cv', { method: 'POST', body: form });
    const data = await res.json();
    setTyping(false);

    if (data.success) {
      state.cvFilename = file.name;
      if (label) { label.textContent = `✓ ${file.name}`; }
      const btn = $('attachCvBtn');
      if (btn) btn.style.borderColor = 'var(--gold)';

      if (data.profile) updateProfileUI(data.profile);
      if (data.jobs && data.jobs.length > 0) { state.jobs = data.jobs; renderJobCards(data.jobs); }

      appendAtomMessage(data.message || `✅ CV **${esc(file.name)}** parsed & synced. Match scores recalibrated.`);
    } else {
      if (label) label.textContent = 'Upload CV (PDF/DOCX)';
      appendAtomMessage(`⚠️ Upload error: ${esc(data.error || 'Unknown error')}`, true);
    }
  } catch (err) {
    setTyping(false);
    if (label) label.textContent = 'Upload CV (PDF/DOCX)';
    appendAtomMessage(`⚠️ Upload failed: ${esc(err.message)}`, true);
  }
  scrollBottom();
}

/* ═══════════════════════════════════════════════════════════
   PROFILE UI
   ═══════════════════════════════════════════════════════════ */
function updateProfileUI(profile) {
  if (!profile) return;
  const nm = $('profileName');
  const rl = $('profileRole');
  const av = $('candidateAvatarText');
  if (nm && profile.name)  nm.textContent = profile.name;
  if (rl && profile.title) rl.textContent = profile.title;
  if (av && profile.name) {
    const parts = profile.name.split(' ');
    av.textContent = (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
  }
}

/* ═══════════════════════════════════════════════════════════
   APPLY DRAWER
   ═══════════════════════════════════════════════════════════ */
function openDrawer(job) {
  state.currentJob = job;
  const backdrop = $('applyModalBackdrop');
  if (!backdrop) return;

  /* Header */
  const el = (id) => $(id);
  if (el('drawerJobTitle')) el('drawerJobTitle').textContent = job.title || 'Executive Role';
  if (el('drawerCompany'))  el('drawerCompany').textContent  = `${job.company} • ${job.location || 'Remote'}`;

  /* Document */
  const docName = `Executive_Dossier_${(job.company || 'Company').replace(/\s+/g, '_')}.pdf`;
  if (el('docCvTitle'))        el('docCvTitle').textContent  = docName;
  if (el('downloadCvInDrawer')) el('downloadCvInDrawer').href = `/api/download-cv/${encodeURIComponent(job.id)}`;

  /* Cover letter */
  const cl = el('applyCoverLetter');
  if (cl) cl.value = buildCoverLetter(job);

  /* Screening */
  const sc = el('screeningQuestionsContainer');
  if (sc) sc.innerHTML = buildScreening(job);

  backdrop.style.display = '';
  document.body.style.overflow = 'hidden';
}

function closeDrawer() {
  const b = $('applyModalBackdrop');
  if (b) b.style.display = 'none';
  document.body.style.overflow = '';
  state.currentJob = null;
}

async function handleConfirmApply() {
  const job = state.currentJob;
  if (!job) return;

  const btn = $('confirmApplyBtn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span>⏳ Committing…</span>'; }

  const payload = {
    job_id:       job.id,
    session_id:   state.sessionId,
    full_name:    $('applyFullName')?.value   || 'Alex Morgan',
    email:        $('applyEmail')?.value      || '',
    phone:        $('applyPhone')?.value      || '',
    location:     $('applyLocation')?.value   || '',
    linkedin:     $('applyLinkedIn')?.value   || '',
    portfolio:    $('applyPortfolio')?.value  || '',
    cover_letter: $('applyCoverLetter')?.value || '',
    answers:      {},
  };

  try {
    const res  = await fetch('/api/apply', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg><span>Authorize & Commit to Database</span>';
    }
    closeDrawer();

    if (data.success) {
      /* Update badge count */
      const badge = $('appCountBadge');
      if (badge) badge.textContent = parseInt(badge.textContent || '0', 10) + 1;

      appendAtomMessage(
        `✅ **Application Committed!**\n\n` +
        `**${esc(job.title)}** at **${esc(job.company)}** is now in the database.\n\n` +
        `- 🆔 Record: \`${data.application_id || '—'}\`\n` +
        `- 📊 Match: **${job.match_score}%**\n\n` +
        `Atom will surface updates as they arrive.`
      );
    } else {
      appendAtomMessage(`⚠️ Submit failed: ${esc(data.error || 'Unknown')}`, true);
    }
  } catch (err) {
    if (btn) { btn.disabled = false; btn.innerHTML = '<span>Authorize & Commit to Database</span>'; }
    closeDrawer();
    appendAtomMessage(`⚠️ Network error: ${esc(err.message)}`, true);
  }
  scrollBottom();
}

function buildCoverLetter(job) {
  const name   = $('applyFullName')?.value || 'Alex Morgan';
  const skills = (job.tech_stack || ['TypeScript', 'React', 'System Design']).slice(0, 3).join(', ');
  return (
    `Dear ${job.company} Team,\n\n` +
    `I am writing to express my strong interest in the ${job.title} role. ` +
    `With expertise in ${skills}, I have long admired ${job.company}'s commitment to engineering excellence.\n\n` +
    `In my most recent role, I led the delivery of high-impact features at scale, improving system reliability ` +
    `by 40% and mentoring a team of 8 engineers.\n\n` +
    `I look forward to discussing how my background can contribute to ${job.company}'s mission.\n\n` +
    `Sincerely,\n${name}`
  );
}

function buildScreening(job) {
  const qs = (job.screening_questions || []).slice(0, 3);
  if (!qs.length) {
    qs.push(
      { question: `Why are you interested in ${job.company}?`, suggested_answer: `I admire ${job.company}'s focus on engineering excellence.` },
      { question: 'What is your availability to start?', suggested_answer: '2–4 weeks from offer acceptance.' }
    );
  }
  return qs.map((q, i) => `
    <div class="screening-q-item">
      <label>${i + 1}. ${esc(q.question)}</label>
      <textarea class="form-input form-textarea" rows="2">${esc(q.suggested_answer || '')}</textarea>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════════
   TRACKER MODAL
   ═══════════════════════════════════════════════════════════ */
async function openTracker() {
  const backdrop = $('trackerModalBackdrop');
  if (!backdrop) return;
  backdrop.style.display = '';
  document.body.style.overflow = 'hidden';

  const tbody = $('trackerTableBody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-muted)">Loading…</td></tr>';

  try {
    const res  = await fetch('/api/applications');
    const data = await res.json();
    const apps = data.applications || [];

    const badge = $('appCountBadge');
    if (badge) badge.textContent = apps.length;

    if (tbody) {
      tbody.innerHTML = apps.length
        ? apps.map(a => {
            const cls = a.status?.includes('Verified') ? 'status-submitted'
                      : a.status?.includes('nterv')    ? 'status-interview'
                      : 'status-pending';
            const ts = a.created_at
              ? new Date(a.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
              : '—';
            return `<tr>
              <td style="font-weight:600;color:var(--text-primary)">${esc(a.company || '—')}</td>
              <td>${esc(a.job_title || '—')}</td>
              <td><span class="match-score-pill" style="font-size:10px;padding:2px 8px;">${esc(String(a.match_score || '—'))}%</span></td>
              <td><span class="status-badge-sm ${cls}">${esc(a.status || 'submitted')}</span></td>
              <td style="font-family:var(--font-mono);font-size:11px;">${esc(ts)}</td>
              <td><a href="/api/download-cv/${encodeURIComponent(a.job_id || a.id)}" target="_blank" class="luxury-download-btn" style="font-size:10px;padding:4px 10px;">PDF</a></td>
            </tr>`;
          }).join('')
        : '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-muted)">No applications yet. Apply to a role to start tracking.</td></tr>';
    }
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-muted)">Error: ${esc(err.message)}</td></tr>`;
  }
}

function closeTracker() {
  const b = $('trackerModalBackdrop');
  if (b) b.style.display = 'none';
  document.body.style.overflow = '';
}

/* ═══════════════════════════════════════════════════════════
   DB STATS
   ═══════════════════════════════════════════════════════════ */
async function loadDbStats() {
  try {
    const res  = await fetch('/api/db-inspect');
    const data = await res.json();
    if (data.tables) {
      const apps = data.tables.applications || 0;
      const jobs = data.tables.jobs || 0;
      const summary = $('dbRecordSummary');
      if (summary) summary.textContent = `${apps} App${apps !== 1 ? 's' : ''} · ${jobs} Job${jobs !== 1 ? 's' : ''}`;
      const badge = $('appCountBadge');
      if (badge) badge.textContent = apps;
    }
  } catch (_) { /* silently ignore */ }
}

async function showDbStats() {
  try {
    const res  = await fetch('/api/db-inspect');
    const data = await res.json();
    if (data.tables) {
      const lines = Object.entries(data.tables)
        .map(([t, c]) => `- **${t}**: ${c} record${c !== 1 ? 's' : ''}`)
        .join('\n');
      appendAtomMessage(`🏛️ **SQLite Database** (\`atom_luxury.db\`)\n\n${lines}\n\nAll data persists across sessions.`);
      scrollBottom();
    }
  } catch (err) {
    appendAtomMessage(`⚠️ DB inspect error: ${esc(err.message)}`, true);
  }
}

/* ═══════════════════════════════════════════════════════════
   API KEY MODAL
   ═══════════════════════════════════════════════════════════ */
function openApiModal() {
  const b = $('apiKeyModalBackdrop');
  if (!b) return;
  b.style.display = '';
  document.body.style.overflow = 'hidden';
  const inp = $('apiKeyInput');
  if (inp) inp.value = state.apiKey === DEFAULT_OPENAI_KEY ? '' : state.apiKey;
  const sel = $('modelSelect');
  if (sel) sel.value = state.model;
  const fb = $('testFeedbackBox');
  if (fb) fb.style.display = 'none';
  syncProviderRadios();
}

function closeApiModal() {
  const b = $('apiKeyModalBackdrop');
  if (b) b.style.display = 'none';
  document.body.style.overflow = '';
}

function syncProviderRadios() {
  document.querySelectorAll('input[name="apiProvider"]').forEach(r => {
    r.checked = r.value === state.provider;
  });
  syncProviderCards();
}

function syncProviderCards() {
  $('providerOpenAiCard')?.classList.toggle('active', state.provider === 'openai');
  $('providerGeminiCard')?.classList.toggle('active', state.provider === 'gemini');
}

async function testApiKey() {
  const fb = $('testFeedbackBox');
  const fs = $('feedbackStatus');
  const fd = $('feedbackDetail');
  if (!fb || !fs || !fd) return;

  const key = $('apiKeyInput')?.value.trim() || state.apiKey;
  fb.style.display = 'block';
  fs.textContent = 'Pinging provider…';
  fs.style.color  = 'var(--text-muted)';
  fd.textContent  = '';

  try {
    const res  = await fetch('/api/verify-key', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key, provider: state.provider, model: state.model }),
    });
    const data = await res.json();
    if (data.valid) {
      fs.textContent = data.warning ? '⚠️ Key valid (quota exhausted)' : '✓ Connection Verified';
      fs.style.color  = data.warning ? '#f59e0b' : '#22c55e';
      fd.textContent  = data.message || '';
    } else {
      fs.textContent = '✗ Connection Failed';
      fs.style.color  = '#ef4444';
      fd.textContent  = data.message || 'Invalid key or network error.';
    }
  } catch (err) {
    fs.textContent = '✗ Network Error';
    fs.style.color  = '#ef4444';
    fd.textContent  = err.message;
  }
}

function saveApiKey() {
  const inp = $('apiKeyInput');
  if (inp?.value.trim()) state.apiKey = inp.value.trim();
  const sel = $('modelSelect');
  if (sel) state.model = sel.value;

  /* Update UI indicators */
  const label = state.provider === 'openai' ? 'OpenAI (Active)' : 'Gemini (Active)';
  const dot   = $('apiDotSidebar');
  if (dot) { dot.className = 'status-dot connected'; }
  const sl = $('apiStatusSidebar');
  if (sl) sl.textContent = label;
  const ki = $('keyIndicator');
  if (ki) { ki.textContent = state.provider === 'openai' ? 'OpenAI Ready' : 'Gemini Ready'; ki.className = 'key-indicator-pill active'; }

  closeApiModal();
  appendAtomMessage(`✅ **AI credentials updated** — ${label} · \`${state.model}\``);
  scrollBottom();
}

/* ═══════════════════════════════════════════════════════════
   TARGET JOB DESCRIPTION MATCH ANALYZER
   ═══════════════════════════════════════════════════════════ */
let latestAnalyzedJob = null;

function openJdModal() {
  const b = $('jdMatchModalBackdrop');
  if (!b) return;
  b.style.display = '';
  document.body.style.overflow = 'hidden';
}

function closeJdModal() {
  const b = $('jdMatchModalBackdrop');
  if (b) b.style.display = 'none';
  document.body.style.overflow = '';
}

async function handleAnalyzeJd() {
  const title = $('targetJobTitleInput')?.value.trim() || 'Target Executive Role';
  const company = $('targetCompanyInput')?.value.trim() || 'Target Enterprise';
  const jdText = $('targetJdTextarea')?.value.trim();

  if (!jdText) {
    alert('Please paste the job description text to compare against your CV.');
    return;
  }

  const btn = $('analyzeJdBtn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Comparing CV against Job Description...</span>';
  }

  try {
    const res = await fetch('/api/match-jd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        job_title: title,
        company: company,
        jd_text: jdText,
        save_as_job: true
      })
    });
    const data = await res.json();

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>⚡ Analyze & Calculate ATS Match Against My CV</span>';
    }

    if (data.success) {
      latestAnalyzedJob = data.job;

      // Update analysis UI
      const resultsArea = $('jdAnalysisResults');
      if (resultsArea) resultsArea.style.display = 'flex';

      if ($('jdMatchScoreText')) $('jdMatchScoreText').textContent = `${data.ats_score}% ATS Match`;
      if ($('jdMatchPill')) $('jdMatchPill').textContent = data.match_badge || 'High Fit';

      // Matched skills
      const matchedContainer = $('jdMatchingSkillsContainer');
      if (matchedContainer) {
        matchedContainer.innerHTML = data.matched_skills.length
          ? data.matched_skills.map(s => `<span class="job-tag" style="background:rgba(34,197,94,0.12); color:#22c55e; border-color:rgba(34,197,94,0.25);">✓ ${esc(s)}</span>`).join('')
          : '<span style="font-size:12px; color:var(--text-muted);">No exact keyword overlap found.</span>';
      }

      // Missing skills
      const missingContainer = $('jdMissingSkillsContainer');
      if (missingContainer) {
        missingContainer.innerHTML = data.missing_skills.length
          ? data.missing_skills.map(s => `<span class="job-tag" style="background:rgba(245,158,11,0.12); color:#f59e0b; border-color:rgba(245,158,11,0.25);">+ ${esc(s)}</span>`).join('')
          : '<span style="font-size:12px; color:#22c55e;">✓ Excellent coverage! No critical keywords missing.</span>';
      }

      if ($('jdRecommendationText')) {
        $('jdRecommendationText').textContent = data.recommendation;
      }

      // Refresh job cards if all jobs returned
      if (data.jobs && data.jobs.length > 0) {
        state.jobs = data.jobs;
        renderJobCards(data.jobs);
      }

      appendAtomMessage(`🎯 **ATS Gap Analysis Complete for ${esc(title)} @ ${esc(company)}** (${data.ats_score}% Match). Detailed keyword breakdown displayed.`);
    } else {
      alert(data.error || 'Failed to analyze job description.');
    }
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>⚡ Analyze & Calculate ATS Match Against My CV</span>';
    }
    alert('Error connecting to analyzer: ' + err.message);
  }
}

function handleCreateJobFromJd() {
  if (!latestAnalyzedJob) return;
  closeJdModal();
  openDrawer(latestAnalyzedJob);
}

/* ═══════════════════════════════════════════════════════════
   NEW SEARCH
   ═══════════════════════════════════════════════════════════ */
function startNewSearch() {
  const ta = $('chatTextarea');
  if (ta) { ta.value = 'Find me the best executive roles matching my profile.'; autoResizeTA(); ta.focus(); }
}

/* ═══════════════════════════════════════════════════════════
   MARKDOWN → HTML
   ═══════════════════════════════════════════════════════════ */
function fmtMd(text) {
  if (!text) return '';
  let h = esc(text);

  /* Fenced code blocks */
  h = h.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) =>
    `<pre style="background:rgba(255,255,255,0.04);border:1px solid var(--border-subtle);border-radius:8px;padding:12px;overflow-x:auto;font-family:var(--font-mono);font-size:12px;margin:8px 0;"><code>${code.trim()}</code></pre>`
  );

  /* Inline code */
  h = h.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  /* Bold & italic */
  h = h.replace(/\*\*(.+?)\*\*/g,   '<strong>$1</strong>');
  h = h.replace(/\*([^*\n]+)\*/g,   '<em>$1</em>');
  h = h.replace(/_([^_\n]+)_/g,     '<em>$1</em>');

  /* Headings */
  h = h.replace(/^### (.+)$/gm, '<h3 style="font-family:var(--font-heading);font-size:13px;letter-spacing:.08em;color:var(--gold-light);margin:12px 0 6px;">$1</h3>');
  h = h.replace(/^## (.+)$/gm,  '<h3 style="font-family:var(--font-heading);font-size:14px;letter-spacing:.08em;color:var(--gold-light);margin:12px 0 6px;">$1</h3>');

  /* Blockquotes */
  h = h.replace(/^&gt; (.+)$/gm, '<blockquote style="border-left:3px solid var(--gold-dim);padding:6px 12px;color:var(--text-secondary);margin:8px 0;background:rgba(255,255,255,0.02);border-radius:0 8px 8px 0;">$1</blockquote>');

  /* Lists */
  h = h.replace(/^\s*[-•]\s+(.+)$/gm, '<li style="margin-bottom:4px;">$1</li>');
  h = h.replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, '<ul style="margin:8px 0;padding-left:20px;">$1</ul>');
  h = h.replace(/^\s*\d+\.\s+(.+)$/gm, '<li style="margin-bottom:4px;">$1</li>');

  /* Links */
  h = h.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:var(--gold);text-decoration:underline;">$1</a>');

  /* Paragraphs */
  const chunks = h.split(/\n\n+/);
  h = chunks.map(p => {
    p = p.trim();
    if (!p) return '';
    if (/^<(h[1-6]|ul|ol|pre|blockquote)/.test(p)) return p;
    return `<p style="margin-bottom:8px;">${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return h;
}

/* ─── ESCAPE HTML ─────────────────────────────────────────── */
function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#039;');
}
