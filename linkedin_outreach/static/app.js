// LinkedIn Outreach Agent Frontend Control Center
let contactsData = [];
let activeFilter = 'ALL';
let logEventSource = null;

const PRESETS = {
  'research': {
    intro: `Hi {First Name}, nice to meet you. I'm doing some research in the creative sector and looking for professionals like you to give me a bit of feedback. It's very quick, just a few questions every now and then, either a short form or a 10-minute call. Let me know. Thanks in advance.`,
    followup: `Hi {First Name}, just checking in case my last message got lost - no worries if now isn't a good time. Still looking for a few creative professionals to share some quick thoughts on my research. Totally informal, no pressure. Would you be open to it? Thanks again.`
  },
  'ai-engineer': {
    intro: `Hi {First Name}, nice to connect with you. I'm an AI engineer building agentic systems and multi-agent workflows, and I've been following {Company}'s work. I'm currently gathering perspectives from engineering leaders on multi-agent reliability and retrieval challenges in production. Would you be open to sharing a quick thought or a brief 10-minute chat? Thanks in advance.`,
    followup: `Hi {First Name}, just checking back in case my note was buried. No worries at all if you're slammed right now. Still curious to hear your take on agentic engineering challenges at {Company} whenever you have a moment. Totally informal and low-pressure. Thanks again.`
  },
  'career-chat': {
    intro: `Hi {First Name}, thanks for connecting. I came across your profile while exploring careers in {Title} at {Company}. I'd love to ask a couple of quick questions about your journey and what a typical week looks like on your team. Would you be open to a quick 10-minute chat? No pressure either way.`,
    followup: `Hi {First Name}, just checking in case this got buried in your inbox. No worries at all if your schedule is packed. Would still love to hear a few thoughts on your path into {Title} if you ever have 5-10 minutes. Thanks again.`
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initModals();
  initControls();
  initSSELogs();
  loadStatus();
  loadContacts();
  loadTemplates();

  // Refresh periodic status every 5 seconds
  setInterval(loadStatus, 5000);
});

// TABS
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

function switchToTab(tabId) {
  const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  if (btn) btn.click();
}

// STATUS & METRICS
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const stats = data.stats;

    document.getElementById('val-total').textContent = stats.total;
    document.getElementById('val-blank').textContent = stats.blank;
    document.getElementById('val-invited').textContent = stats.invited;
    document.getElementById('val-msg1').textContent = stats.msg1_sent;
    document.getElementById('val-msg2').textContent = stats.msg2_sent;
    document.getElementById('val-replied').textContent = stats.replied;

    // Filter pills counters
    document.getElementById('pill-all').textContent = stats.total;
    document.getElementById('pill-blank').textContent = stats.blank;
    document.getElementById('pill-invited').textContent = stats.invited;
    document.getElementById('pill-msg1').textContent = stats.msg1_sent;
    document.getElementById('pill-msg2').textContent = stats.msg2_sent;
    document.getElementById('pill-replied').textContent = stats.replied;
    document.getElementById('leads-tab-count').textContent = stats.total;

    // Composio Badge
    if (data.composio_profile && data.composio_profile.name) {
      document.getElementById('composio-account-text').textContent = `Composio: ${data.composio_profile.name}`;
    }

    // Status Badge
    const badge = document.getElementById('agent-status-badge');
    const badgeText = document.getElementById('agent-status-text');
    if (data.is_running) {
      badge.className = 'status-badge running';
      badgeText.textContent = 'Pipeline Running...';
    } else {
      badge.className = 'status-badge';
      badgeText.textContent = 'Agent Ready';
    }
  } catch (err) {
    console.error('Error fetching status:', err);
  }
}

// CONTACTS DATABASE
async function loadContacts() {
  try {
    const res = await fetch('/api/contacts');
    contactsData = await res.json();
    renderContactsTable();
  } catch (err) {
    console.error('Error fetching contacts:', err);
  }
}

function renderContactsTable() {
  const tbody = document.getElementById('leads-table-body');
  const searchQ = document.getElementById('leads-search').value.toLowerCase().trim();

  let filtered = contactsData.filter(c => {
    // Status filter
    const status = (c['LinkedIn Status'] || '').toUpperCase();
    if (activeFilter === 'BLANK' && status !== '') return false;
    if (activeFilter === 'INVITED' && status !== 'INVITED') return false;
    if (activeFilter === 'MSG1_SENT' && status !== 'MSG1_SENT') return false;
    if (activeFilter === 'MSG2_SENT' && status !== 'MSG2_SENT') return false;
    if (activeFilter === 'REPLIED' && status !== 'REPLIED') return false;

    // Search filter
    if (searchQ) {
      const matchName = (c['Full Name'] || '').toLowerCase().includes(searchQ);
      const matchComp = (c['Company'] || '').toLowerCase().includes(searchQ);
      const matchTitle = (c['Title'] || '').toLowerCase().includes(searchQ);
      if (!matchName && !matchComp && !matchTitle) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 30px;">No contacts match the selected filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(c => {
    const status = (c['LinkedIn Status'] || '').toUpperCase();
    let badgeClass = 'blank';
    let badgeLabel = '(blank)';
    if (status === 'INVITED') { badgeClass = 'invited'; badgeLabel = 'INVITED'; }
    else if (status === 'MSG1_SENT') { badgeClass = 'msg1_sent'; badgeLabel = 'MSG1_SENT'; }
    else if (status === 'MSG2_SENT') { badgeClass = 'msg2_sent'; badgeLabel = 'MSG2_SENT'; }
    else if (status === 'REPLIED') { badgeClass = 'replied'; badgeLabel = 'REPLIED'; }

    return `
      <tr>
        <td style="font-weight: 600;">${c['Full Name'] || (c['First Name'] + ' ' + c['Last Name'])}</td>
        <td>${c['Title'] || '-'}</td>
        <td>${c['Company'] || '-'}</td>
        <td>${c['Location'] || '-'}</td>
        <td><span class="status-badge-inline ${badgeClass}">${badgeLabel}</span></td>
        <td style="font-family: var(--font-mono); font-size: 0.78rem;">${c['Invited Date'] || '-'}</td>
        <td style="font-family: var(--font-mono); font-size: 0.78rem;">${c['Connected Date'] || '-'}</td>
        <td><a href="${c['LinkedIn URL']}" target="_blank" class="link-btn">View Profile ↗</a></td>
        <td>
          <button class="action-btn-del" onclick="deleteContact(${c.id})" title="Delete lead">&times;</button>
        </td>
      </tr>
    `;
  }).join('');
}

async function deleteContact(id) {
  if (!confirm('Are you sure you want to delete this lead from contacts.csv?')) return;
  try {
    await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
    await loadContacts();
    await loadStatus();
  } catch (err) {
    alert('Failed to delete lead: ' + err);
  }
}

// TEMPLATES & PREVIEWS
async function loadTemplates() {
  try {
    const res = await fetch('/api/templates');
    const data = await res.json();
    document.getElementById('tpl-intro-text').value = data.intro;
    document.getElementById('tpl-followup-text').value = data.followup;
    updateTemplatePreviews();
  } catch (err) {
    console.error('Error fetching templates:', err);
  }
}

function updateTemplatePreviews() {
  const introText = document.getElementById('tpl-intro-text').value;
  const followupText = document.getElementById('tpl-followup-text').value;

  document.getElementById('intro-char-count').textContent = `${introText.length} chars`;
  document.getElementById('followup-char-count').textContent = `${followupText.length} chars`;

  // Sample lead mock for live preview
  const sample = {
    'First Name': 'John',
    'Company': 'Acme Studio',
    'Title': 'Creative Director',
    'Location': 'London UK'
  };

  const renderSample = (str) => {
    return str
      .replace(/\{First Name\}/gi, sample['First Name'])
      .replace(/\{Company\}/gi, sample['Company'])
      .replace(/\{Title\}/gi, sample['Title'])
      .replace(/\{Location\}/gi, sample['Location'])
      .replace(/—/g, '-');
  };

  document.getElementById('preview-intro-body').textContent = renderSample(introText);
  document.getElementById('preview-followup-body').textContent = renderSample(followupText);
}

// CONTROLS & LISTENERS
function initControls() {
  // Filter pills
  document.querySelectorAll('.pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      renderContactsTable();
    });
  });

  // Search input
  document.getElementById('leads-search').addEventListener('input', renderContactsTable);

  // Template inputs live update
  document.getElementById('tpl-intro-text').addEventListener('input', updateTemplatePreviews);
  document.getElementById('tpl-followup-text').addEventListener('input', updateTemplatePreviews);

  // Preset selector
  document.getElementById('preset-select').addEventListener('change', (e) => {
    const val = e.target.value;
    if (PRESETS[val]) {
      document.getElementById('tpl-intro-text').value = PRESETS[val].intro;
      document.getElementById('tpl-followup-text').value = PRESETS[val].followup;
      updateTemplatePreviews();
    }
  });

  // Save templates button
  document.getElementById('btn-save-templates').addEventListener('click', async () => {
    const intro = document.getElementById('tpl-intro-text').value;
    const followup = document.getElementById('tpl-followup-text').value;
    const statusMsg = document.getElementById('save-status-msg');

    try {
      await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intro, followup })
      });
      statusMsg.textContent = 'Saved successfully!';
      setTimeout(() => { statusMsg.textContent = ''; }, 3000);
    } catch (err) {
      alert('Failed to save templates: ' + err);
    }
  });

  // Connect / Login button
  document.getElementById('btn-login').addEventListener('click', async () => {
    try {
      switchToTab('tab-logs');
      appendLogLine('[System] Launching Chrome LinkedIn Login Assistant...', 'log-info');
      await fetch('/api/browser/login', { method: 'POST' });
    } catch (err) {
      alert('Error: ' + err);
    }
  });

  // Step 6: Test 3 Contacts
  document.getElementById('btn-test-3').addEventListener('click', async () => {
    const dryRun = document.getElementById('chk-dry-run').checked;
    switchToTab('tab-logs');
    appendLogLine(`[System] Starting Step 6 Test Run (3 Contacts, Dry Run: ${dryRun})...`, 'log-info');
    try {
      await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invites: 3, messages: 3, dry_run: dryRun })
      });
    } catch (err) {
      alert('Failed to trigger run: ' + err);
    }
  });

  // Run Full Daily Batch
  document.getElementById('btn-run-full').addEventListener('click', async () => {
    const dryRun = document.getElementById('chk-dry-run').checked;
    if (!confirm(`Start full daily outreach run? (Limit: 20 Invites, 20 Messages, Dry Run: ${dryRun})`)) return;

    switchToTab('tab-logs');
    appendLogLine(`[System] Starting Full Daily Outreach Run (Dry Run: ${dryRun})...`, 'log-info');
    try {
      await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invites: 20, messages: 20, dry_run: dryRun })
      });
    } catch (err) {
      alert('Failed to trigger run: ' + err);
    }
  });

  // Refresh data button
  document.getElementById('btn-refresh').addEventListener('click', () => {
    loadStatus();
    loadContacts();
  });

  // Clear logs button
  document.getElementById('btn-clear-logs').addEventListener('click', () => {
    document.getElementById('console-output').innerHTML = '';
  });
}

// MODAL ADD LEAD
function initModals() {
  const modal = document.getElementById('modal-add-lead');
  const btnOpen = document.getElementById('btn-add-lead');
  const btnClose = document.getElementById('modal-close-btn');
  const btnCancel = document.getElementById('modal-cancel-btn');
  const form = document.getElementById('form-add-lead');

  btnOpen.addEventListener('click', () => modal.classList.add('active'));
  const closeModal = () => modal.classList.remove('active');
  btnClose.addEventListener('click', closeModal);
  btnCancel.addEventListener('click', closeModal);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      first_name: document.getElementById('lead-first-name').value.trim(),
      last_name: document.getElementById('lead-last-name').value.trim(),
      title: document.getElementById('lead-title').value.trim(),
      company: document.getElementById('lead-company').value.trim(),
      location: document.getElementById('lead-location').value.trim(),
      linkedin_url: document.getElementById('lead-url').value.trim(),
      notes: document.getElementById('lead-notes').value.trim()
    };

    try {
      await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      closeModal();
      form.reset();
      loadContacts();
      loadStatus();
    } catch (err) {
      alert('Failed to add lead: ' + err);
    }
  });
}

// SSE LIVE LOG STREAM
function initSSELogs() {
  if (logEventSource) logEventSource.close();

  logEventSource = new EventSource('/api/logs/stream');
  logEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      let cssClass = 'log-info';
      if (data.level === 'ERROR') cssClass = 'log-error';
      else if (data.level === 'WARNING') cssClass = 'log-warning';
      else if (data.level === 'SUCCESS' || data.msg.includes('✔') || data.msg.includes('sent')) cssClass = 'log-success';

      appendLogLine(data.msg, cssClass);
    } catch (e) {
      appendLogLine(event.data, 'log-info');
    }
  };

  logEventSource.onerror = () => {
    // Reconnects automatically
  };
}

function appendLogLine(msg, cssClass) {
  const consoleEl = document.getElementById('console-output');
  const div = document.createElement('div');
  div.className = `log-line ${cssClass}`;
  div.textContent = msg;
  consoleEl.appendChild(div);
  consoleEl.scrollTop = consoleEl.scrollHeight;
}
