/**
 * AI Assistant — Premium Chat Interface
 * Django Expense Tracker
 */

const AI_API = '/api/v1/ai/assistant';
const EXPENSE_API = '/api/v1/expenses/';

// ── State ───────────────────────────────────────────────────────────
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingTimer = null;
let recordingSeconds = 0;

// ── DOM Refs ─────────────────────────────────────────────────────────
const feed = document.getElementById('aiFeed');
const welcome = document.getElementById('aiWelcome');
const textarea = document.getElementById('aiTextarea');
const sendBtn = document.getElementById('aiSendBtn');
const uploadInput = document.getElementById('aiUploadInput');
const voiceOverlay = document.getElementById('aiVoiceOverlay');
const voiceTimer = document.getElementById('aiVoiceTimer');
const voiceStatus = document.getElementById('aiVoiceStatus');

// ── Auto-grow textarea ────────────────────────────────────────────────
if (textarea) {
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  });

  textarea.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

// ── Suggestions ───────────────────────────────────────────────────────
document.querySelectorAll('.ai-suggestion').forEach(card => {
  card.addEventListener('click', () => {
    const text = card.dataset.prompt;
    if (textarea) {
      textarea.value = text;
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    }
    sendMessage();
  });
});

// ── Send Message ──────────────────────────────────────────────────────
if (sendBtn) {
  sendBtn.addEventListener('click', sendMessage);
}

async function sendMessage(overrideText) {
  const text = overrideText || (textarea ? textarea.value.trim() : '');
  if (!text) return;

  hideWelcome();
  appendUserMessage(text);
  if (textarea) {
    textarea.value = '';
    textarea.style.height = 'auto';
  }

  const typingEl = showTyping();
  scrollToBottom();

  const formData = new FormData();
  formData.append('text', text);

  try {
    const res = await fetch(AI_API, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: formData,
    });
    const data = await res.json();
    typingEl.remove();

    if (data.success && data.data) {
      const d = data.data;
      appendAiMessage(null, d);
    } else {
      appendAiMessage(data.message || 'Sorry, I could not process that. Please try again.');
    }
  } catch (err) {
    typingEl.remove();
    appendAiMessage('⚠️ Network error. Please check your connection and try again.');
  }

  scrollToBottom();
}

// ── Message Rendering ────────────────────────────────────────────────
function hideWelcome() {
  if (welcome) {
    welcome.style.opacity = '0';
    welcome.style.transition = 'opacity 0.3s';
    setTimeout(() => { welcome.style.display = 'none'; }, 300);
  }
}

function appendUserMessage(text) {
  const now = formatTime(new Date());
  const el = document.createElement('div');
  el.className = 'ai-msg user';
  el.innerHTML = `
    <div class="ai-msg-avatar">${getUserInitials()}</div>
    <div class="ai-msg-content">
      <div class="ai-bubble">${escapeHtml(text)}</div>
      <div class="ai-msg-meta">
        <span class="ai-msg-time">${now}</span>
      </div>
    </div>`;
  feed.appendChild(el);
}

function appendAiMessage(text, extractedData) {
  const now = formatTime(new Date());
  const el = document.createElement('div');
  el.className = 'ai-msg assistant';

  let bubbleContent = '';
  let extraContent = '';

  if (extractedData) {
    bubbleContent = `✅ I've detected an expense from your input. Please review and confirm the details below before saving.`;
    extraContent = buildExpenseCard(extractedData);
  } else {
    bubbleContent = renderMarkdown(text || '');
  }

  el.innerHTML = `
    <div class="ai-msg-avatar">
      <svg class="ai-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <path d="M12 2a5 5 0 0 0-5 5v2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5Z"/>
        <path d="M9 10V7a3 3 0 0 1 6 0v3"/>
      </svg>
    </div>
    <div class="ai-msg-content">
      <div class="ai-bubble">${bubbleContent}</div>
      ${extraContent ? `<div class="ai-msg-extra">${extraContent}</div>` : ''}
      <div class="ai-msg-meta">
        <span class="ai-msg-time">${now}</span>
        <button class="ai-copy-btn" onclick="copyText(this, '${escapeAttr(text || bubbleContent)}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          Copy
        </button>
      </div>
    </div>`;
  feed.appendChild(el);
}

function buildExpenseCard(d) {
  const id = 'ec_' + Date.now();
  return `
  <div class="expense-card" id="${id}">
    <div class="expense-card-header">
      <span class="ai-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/></svg></span>
      <h4>Expense Detected</h4>
      <span class="expense-card-badge">Review Required</span>
    </div>
    <div class="expense-card-body">
      <div class="expense-field">
        <label>Expense Title</label>
        <input type="text" id="${id}_title" value="${escapeAttr(d.title || '')}" placeholder="e.g. Grocery Shopping">
      </div>
      <div class="expense-field-row">
        <div class="expense-field">
          <label>Amount (₹)</label>
          <input type="number" id="${id}_amount" value="${d.amount || ''}" placeholder="0.00">
        </div>
        <div class="expense-field">
          <label>Category</label>
          <select id="${id}_category">
            ${['Food','Transport','Shopping','Entertainment','Utilities','Health','Education','Other']
              .map(c => `<option value="${c}" ${c === d.category ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="expense-field-row">
        <div class="expense-field">
          <label>Date</label>
          <input type="date" id="${id}_date" value="${(d.expense_date || '').slice(0,10) || today()}">
        </div>
        <div class="expense-field">
          <label>Payment Method</label>
          <select id="${id}_method">
            ${['Cash','Credit Card','Debit Card','UPI','Bank Transfer','Auto Pay','Other']
              .map(m => `<option value="${m}" ${m === d.payment_method ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        </div>
      </div>
      ${d.notes ? `<div class="expense-field"><label>Notes</label><input type="text" id="${id}_notes" value="${escapeAttr(d.notes)}"></div>` : ''}
    </div>
    <div class="expense-card-actions">
      <button class="btn-save" onclick="saveExpenseCard('${id}')"><span class="ai-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 12.5 10.5 16 17 8"/><path d="M5 5h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z"/></svg></span> Save Expense</button>
      <button class="btn-cancel" onclick="document.getElementById('${id}').remove()">Cancel</button>
    </div>
  </div>`;
}

async function saveExpenseCard(id) {
  const title = document.getElementById(`${id}_title`).value.trim();
  const amount = document.getElementById(`${id}_amount`).value;
  const category = document.getElementById(`${id}_category`).value;
  const date = document.getElementById(`${id}_date`).value;
  const method = document.getElementById(`${id}_method`).value;
  const notesEl = document.getElementById(`${id}_notes`);
  const notes = notesEl ? notesEl.value : '';

  if (!title || !amount) {
    alert('Please fill in Title and Amount.');
    return;
  }

  const btn = document.querySelector(`#${id} .btn-save`);
  btn.textContent = 'Saving...';
  btn.disabled = true;

  const payload = {
    title, amount: parseFloat(amount),
    category, payment_method: method,
    expense_date: new Date(date).toISOString(),
    notes
  };

  try {
    const res = await fetch(EXPENSE_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({
        title: payload.title,
        amount: payload.amount,
        category: payload.category,
        paymentMethod: payload.payment_method,
        expenseDate: payload.expense_date,
        notes: payload.notes
      })
    });
    const data = await res.json();
    if (data.success || res.ok) {
      document.getElementById(id).innerHTML = `
        <div style="padding:16px 18px; display:flex; align-items:center; gap:10px; color:var(--accent-success); font-weight:700;">
          <span class="ai-icon" style="width:20px;height:20px;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg></span>
          Expense "<strong>${escapeHtml(title)}</strong>" saved successfully!
        </div>`;
    } else {
      btn.textContent = '💾 Save Expense';
      btn.disabled = false;
      alert(data.message || 'Failed to save expense. Please try again.');
    }
  } catch (err) {
    btn.textContent = '💾 Save Expense';
    btn.disabled = false;
    alert('Network error. Please try again.');
  }
}

// ── Receipt Upload ────────────────────────────────────────────────────
if (document.getElementById('aiUploadBtn')) {
  document.getElementById('aiUploadBtn').addEventListener('click', () => {
    document.getElementById('aiUploadInput').click();
  });
}
if (document.getElementById('aiHeaderUploadBtn')) {
  document.getElementById('aiHeaderUploadBtn').addEventListener('click', () => {
    document.getElementById('aiUploadInput').click();
  });
}

if (uploadInput) {
  uploadInput.addEventListener('change', async () => {
    const file = uploadInput.files[0];
    if (!file) return;
    hideWelcome();
    uploadInput.value = '';

    appendUserMessage(`📎 Uploading receipt: ${file.name}`);
    const typingEl = showTyping();
    scrollToBottom();

    const formData = new FormData();
    formData.append('image', file);

    try {
      const res = await fetch(AI_API, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
        body: formData,
      });
      const data = await res.json();
      typingEl.remove();

      if (data.success && data.data) {
        const d = data.data;
        // Show receipt preview then expense card
        appendReceiptMessage(file, d);
      } else {
        appendAiMessage(data.message || 'Could not read this receipt. Please try a clearer image.');
      }
    } catch (err) {
      typingEl.remove();
      appendAiMessage('⚠️ Network error. Please try again.');
    }
    scrollToBottom();
  });
}

function appendReceiptMessage(file, d) {
  const now = formatTime(new Date());
  const id = 'rc_' + Date.now();
  const imgUrl = URL.createObjectURL(file);
  const el = document.createElement('div');
  el.className = 'ai-msg assistant';
  el.innerHTML = `
    <div class="ai-msg-avatar">🤖</div>
    <div class="ai-msg-content">
      <div class="ai-bubble">📄 I've analyzed your receipt. Here's what I found:</div>
      <div class="ai-msg-extra">
        <div class="receipt-card" id="${id}">
          <div class="receipt-header">
            <div class="receipt-icon">🧾</div>
            <div class="receipt-header-info">
              <h4>${escapeHtml(d.title || 'Receipt')}</h4>
              <p>Detected from uploaded image</p>
            </div>
            <div class="receipt-confidence">~90% confidence</div>
          </div>
          <img class="receipt-img-preview" src="${imgUrl}" alt="Receipt">
          <div class="receipt-body">
            <div class="receipt-item"><span class="receipt-item-name">Category</span><span class="receipt-item-price">${escapeHtml(d.category || 'Other')}</span></div>
            <div class="receipt-item"><span class="receipt-item-name">Payment</span><span class="receipt-item-price">${escapeHtml(d.payment_method || 'Cash')}</span></div>
            <div class="receipt-total"><span>Total Amount</span><span>₹${d.amount || '0.00'}</span></div>
          </div>
          <div class="receipt-actions">
            <button class="btn-save" onclick="confirmReceiptExpense('${id}', ${JSON.stringify(d).replace(/'/g, '&#39;')})">💾 Save Expense</button>
            <button class="btn-discard" onclick="document.getElementById('${id}').remove()">Discard</button>
          </div>
        </div>
      </div>
      <div class="ai-msg-meta"><span class="ai-msg-time">${now}</span></div>
    </div>`;
  feed.appendChild(el);
}

function confirmReceiptExpense(id, d) {
  // Replace receipt card with expense confirmation card
  const card = document.getElementById(id);
  if (card) {
    const wrapper = card.parentElement;
    wrapper.innerHTML = buildExpenseCard(d);
  }
}

// ── Voice Recording ───────────────────────────────────────────────────
function openVoice() {
  if (voiceOverlay) voiceOverlay.classList.add('active');
  startRecording();
}

function closeVoice() {
  if (voiceOverlay) voiceOverlay.classList.remove('active');
  stopRecording(true);
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      if (!isRecording) return; // Cancelled
      const mimeType = mediaRecorder.mimeType || 'audio/webm';
      const blob = new Blob(audioChunks, { type: mimeType });
      closeVoice();
      processAudio(blob, mimeType);
    };
    mediaRecorder.start();
    isRecording = true;
    recordingSeconds = 0;
    if (voiceTimer) voiceTimer.textContent = '0:00';
    if (voiceStatus) voiceStatus.textContent = 'Listening...';
    recordingTimer = setInterval(() => {
      recordingSeconds++;
      const m = Math.floor(recordingSeconds / 60);
      const s = recordingSeconds % 60;
      if (voiceTimer) voiceTimer.textContent = `${m}:${s.toString().padStart(2, '0')}`;
      if (recordingSeconds >= 60) stopRecording(false);
    }, 1000);
  } catch (err) {
    closeVoice();
    alert('Microphone access denied. Please enable it in your browser settings.');
  }
}

function stopRecording(cancel) {
  clearInterval(recordingTimer);
  if (cancel) {
    isRecording = false;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      const origOnStop = mediaRecorder.onstop;
      mediaRecorder.onstop = null;
      mediaRecorder.stop();
    }
    return;
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
}

async function processAudio(blob, mimeType) {
  hideWelcome();
  appendUserMessage('🎤 Voice message recorded');
  const typingEl = showTyping();
  scrollToBottom();

  const formData = new FormData();
  let ext = 'webm';
  if (mimeType && mimeType.includes('mp4')) ext = 'mp4';
  else if (mimeType && mimeType.includes('ogg')) ext = 'ogg';
  
  formData.append('audio', blob, `recording.${ext}`);

  try {
    const res = await fetch(AI_API, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: formData,
    });
    const data = await res.json();
    typingEl.remove();

    if (data.success && data.data) {
      appendAiMessage(null, data.data);
    } else {
      appendAiMessage(data.message || 'Could not process voice input. Please try again.');
    }
  } catch (err) {
    typingEl.remove();
    appendAiMessage('⚠️ Network error. Please try again.');
  }
  scrollToBottom();
}

// ── New Chat ──────────────────────────────────────────────────────────
function newChat() {
  while (feed.children.length > 0) feed.removeChild(feed.lastChild);
  if (welcome) {
    welcome.style.display = '';
    welcome.style.opacity = '1';
  }
}

// ── Typing Indicator ─────────────────────────────────────────────────
function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'ai-msg assistant';
  wrap.innerHTML = `
    <div class="ai-msg-avatar">🤖</div>
    <div class="ai-msg-content">
      <div class="ai-typing">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  feed.appendChild(wrap);
  return wrap;
}

// ── Dashboard Preview ─────────────────────────────────────────────────
async function showDashboard() {
  hideWelcome();
  appendUserMessage('📊 Show me my dashboard');
  const typingEl = showTyping();
  scrollToBottom();

  // Fetch real KPI data
  let kpiData = null;
  try {
    const r = await fetch('/api/v1/analytics/kpis');
    const j = await r.json();
    if (j.success) kpiData = j.data;
  } catch (e) {}

  typingEl.remove();

  const now = formatTime(new Date());
  const total = kpiData ? formatCurrency(kpiData.totalExpenses || 0) : '₹0';
  const budget = kpiData ? formatCurrency(kpiData.totalBudget || 0) : '₹0';
  const remaining = kpiData ? formatCurrency((kpiData.totalBudget || 0) - (kpiData.totalExpenses || 0)) : '₹0';
  const topCat = kpiData ? (kpiData.topCategory || 'N/A') : 'N/A';

  const el = document.createElement('div');
  el.className = 'ai-msg assistant';
  el.innerHTML = `
    <div class="ai-msg-avatar">🤖</div>
    <div class="ai-msg-content">
      <div class="ai-bubble">📊 Here's your financial overview for this month:</div>
      <div class="ai-msg-extra">
        <div class="ai-dashboard-cards">
          <div class="ai-dash-card">
            <div class="ai-dash-card-label">Total Expenses</div>
            <div class="ai-dash-card-value">${total}</div>
            <div class="ai-dash-card-sub">This month</div>
          </div>
          <div class="ai-dash-card emerald">
            <div class="ai-dash-card-label">Remaining Budget</div>
            <div class="ai-dash-card-value">${remaining}</div>
            <div class="ai-dash-card-sub">of ${budget} budget</div>
          </div>
          <div class="ai-dash-card">
            <div class="ai-dash-card-label">Monthly Budget</div>
            <div class="ai-dash-card-value">${budget}</div>
            <div class="ai-dash-card-sub">Configured</div>
          </div>
          <div class="ai-dash-card">
            <div class="ai-dash-card-label">Top Category</div>
            <div class="ai-dash-card-value" style="font-size:16px;">${topCat}</div>
            <div class="ai-dash-card-sub">Highest spending</div>
          </div>
        </div>
        <div style="margin-top:10px;">
          <a href="/" style="display:inline-flex;align-items:center;gap:6px;color:var(--ai-emerald);font-size:13px;font-weight:600;text-decoration:none;">
            View full dashboard →
          </a>
        </div>
      </div>
      <div class="ai-msg-meta"><span class="ai-msg-time">${now}</span></div>
    </div>`;
  feed.appendChild(el);
  scrollToBottom();
}

// ── Utilities ─────────────────────────────────────────────────────────
function getUserInitials() {
  const name = document.body.dataset.username || 'U';
  return name.charAt(0).toUpperCase();
}

function scrollToBottom() {
  if (feed) {
    setTimeout(() => { feed.scrollTop = feed.scrollHeight; }, 50);
  }
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function formatTime(d) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(n) {
  return '₹' + parseFloat(n).toLocaleString('en-IN', { minimumFractionDigits: 0 });
}

function escapeHtml(t) {
  return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function escapeAttr(t) {
  return String(t || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^### (.*)/gm, '<h3>$1</h3>')
    .replace(/^## (.*)/gm, '<h3>$1</h3>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
    setTimeout(() => {
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
    }, 1500);
  });
}

function getCsrf() {
  const name = 'csrftoken';
  for (const c of document.cookie.split(';')) {
    const [k, v] = c.trim().split('=');
    if (k === name) return decodeURIComponent(v);
  }
  const el = document.querySelector('[name=csrfmiddlewaretoken]');
  return el ? el.value : '';
}
