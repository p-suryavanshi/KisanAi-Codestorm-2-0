// KisanAI — Frontend JS
// All API calls go to the FastAPI backend at /api/*

let lang = 'en';
let typing = false;
let recognition = null;
let isRec = false;

// ── INIT ──────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  loadWeather();
  loadMarket();
  loadSchemes();
  addMsg('ai', lang === 'hi'
    ? '🙏 नमस्ते! मैं KisanAI हूँ — आपका AI कृषि सलाहकार।\n\nकुछ भी पूछें — फसल, सिंचाई, खाद, कीट या बाज़ार भाव। मैं हिंदी में जवाब दे सकता हूँ! 🌾'
    : '👋 Welcome to **KisanAI**!\n\nI can help with:\n🌾 Crop-specific advice\n💧 Irrigation & fertilizer\n🐛 Pest identification\n📈 Market prices\n\nTell me about your crops or ask anything!'
  );
});

// ── LANGUAGE ──────────────────────────────────────────────
function setLang(l, btn) {
  lang = l;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const ta = document.getElementById('msgInput');
  if (ta) ta.placeholder = l === 'hi'
    ? 'अपनी फसल के बारे में पूछें...'
    : 'Ask about your crops...';
  toast(l === 'hi' ? '✅ हिंदी मोड चालू' : '✅ Switched to English');
}

// ── WEATHER ───────────────────────────────────────────────
async function loadWeather() {
  const state = document.getElementById('stateSelect')?.value || 'MP';
  const card = document.getElementById('weatherCard');
  const alertEl = document.getElementById('weatherAlert');
  try {
    const r = await fetch(`/api/weather/${state}`);
    const d = await r.json();
    const icons = { sun: '☀️', 'cloud-sun': '⛅', smog: '🌫️', 'cloud-rain': '🌧️' };
    const icon = icons[d.icon] || '🌤️';
    card.innerHTML = `
      <div class="weather-row">
        <div>
          <div class="weather-temp">${d.temp}°C</div>
          <div class="weather-info">${d.desc} · ${state}<br><span style="font-size:10px;opacity:.5">${d.source === 'live' ? '🟢 Live' : '📦 Demo'}</span></div>
        </div>
        <div style="font-size:32px">${icon}</div>
      </div>
      <div class="weather-details">
        <div>Humidity <span>${d.humidity}%</span></div>
        <div>Wind <span>${d.wind} km/h</span></div>
        <div>Rain <span>${d.rain}%</span></div>
        <div>UV <span>${d.uv}</span></div>
      </div>`;
    if (alertEl) alertEl.textContent = d.alert || '';
  } catch {
    if (card) card.innerHTML = '<div class="loading-text">Weather unavailable</div>';
  }
}

// ── MARKET ────────────────────────────────────────────────
async function loadMarket() {
  const list = document.getElementById('marketList');
  if (!list) return;
  try {
    const r = await fetch('/api/market');
    const d = await r.json();
    list.innerHTML = d.prices.map(p => `
      <div class="market-item">
        <div class="m-left">
          <div class="m-icon">${p.icon}</div>
          <div>
            <div class="m-name">${p.crop} / ${p.hindi}</div>
            <div class="m-unit">per ${p.unit}</div>
          </div>
        </div>
        <div style="text-align:right">
          <div class="m-price">₹${p.price.toLocaleString()}</div>
          <div class="m-change ${p.change >= 0 ? 'm-up' : 'm-down'}">${p.change >= 0 ? '+' : ''}₹${p.change}</div>
          ${p.msp ? `<div class="m-msp">MSP ₹${p.msp}</div>` : ''}
        </div>
      </div>`).join('');
  } catch {
    if (list) list.innerHTML = '<div class="loading-text">Market data unavailable</div>';
  }
}

// ── SCHEMES ───────────────────────────────────────────────
async function loadSchemes() {
  const el = document.getElementById('schemesList');
  if (!el) return;
  try {
    const r = await fetch('/api/schemes');
    const d = await r.json();
    el.innerHTML = d.schemes.map(s => `
      <div class="scheme-card">
        <div class="scheme-name">${s.name}</div>
        <div class="scheme-benefit">💰 ${s.benefit}</div>
        <div class="scheme-elig">${s.eligibility}</div>
        <a href="${s.link}" target="_blank" class="scheme-link">Visit portal ↗</a>
      </div>`).join('');
  } catch {
    if (el) el.innerHTML = '<div style="color:var(--mu);font-size:14px">Schemes data unavailable</div>';
  }
}

// ── CHAT ──────────────────────────────────────────────────
function addMsg(role, text) {
  const box = document.getElementById('messages');
  if (!box) return;
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isAI = role === 'ai';
  const fmt = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  const div = document.createElement('div');
  div.className = `msg ${isAI ? 'ai' : 'user'}`;
  div.innerHTML = `
    <div class="msg-av ${isAI ? 'ai' : 'usr'}">${isAI ? '🌾' : 'F'}</div>
    <div>
      <div class="msg-bubble">${fmt}</div>
      <div class="msg-time">${time}</div>
    </div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function showTyping() {
  const box = document.getElementById('messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg ai'; div.id = 'typingEl';
  div.innerHTML = `
    <div class="msg-av ai">🌾</div>
    <div><div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function removeTyping() {
  document.getElementById('typingEl')?.remove();
}

async function sendChat() {
  const ta = document.getElementById('msgInput');
  const msg = ta?.value.trim();
  if (!msg || typing) return;

  addMsg('user', msg);
  ta.value = '';
  ta.style.height = 'auto';
  typing = true;
  const btn = document.getElementById('sendBtn');
  if (btn) btn.disabled = true;

  showTyping();

  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg,
        language: lang,
        crop: document.getElementById('cropSelect')?.value || 'wheat',
        state: document.getElementById('stateSelect')?.value || 'MP',
        soil: document.getElementById('soilSelect')?.value || 'black',
        land: parseFloat(document.getElementById('landInput')?.value || 2.5),
      }),
    });
    const d = await r.json();
    removeTyping();
    addMsg('ai', d.reply || 'Sorry, could not get a response.');
  } catch (e) {
    removeTyping();
    addMsg('ai', `⚠️ Connection error. Is the server running?\n\n${e.message}`);
  }

  typing = false;
  if (btn) btn.disabled = false;
}

function quickSend(btn) {
  const ta = document.getElementById('msgInput');
  if (ta) ta.value = btn.textContent.replace(/^[^\s]+\s/, '');
  sendChat();
}

// ── TABS ──────────────────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  const el = document.getElementById('tab' + name.charAt(0).toUpperCase() + name.slice(1));
  if (el) el.classList.add('active');
  if (name === 'market') loadMarket();
}

// ── PEST DETECTION ────────────────────────────────────────
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('uploadZone')?.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file?.type.startsWith('image/')) uploadPest(file);
}

function handleFile(e) {
  const file = e.target.files[0];
  if (file) uploadPest(file);
}

async function uploadPest(file) {
  const img = document.getElementById('pestImg');
  const hint = document.getElementById('uploadHint');
  const result = document.getElementById('pestResult');

  // Preview
  const reader = new FileReader();
  reader.onload = e => {
    if (img) { img.src = e.target.result; img.style.display = 'block'; }
    if (hint) hint.style.display = 'none';
  };
  reader.readAsDataURL(file);

  if (result) result.style.display = 'none';
  toast('🔬 Analysing image...');

  try {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('language', lang);

    const r = await fetch('/api/pest-detect', { method: 'POST', body: fd });
    const d = await r.json();

    if (result) {
      result.style.display = 'block';
      result.innerHTML = `
        <h4>🔬 ${d.name}</h4>
        <p>${d.description}</p>
        <div class="conf-bar">
          <span style="font-size:11px;color:rgba(250,248,242,.5)">Confidence</span>
          <div class="conf-track"><div class="conf-fill" id="confFill" style="width:0%"></div></div>
          <span style="font-size:11px;color:var(--gp);font-weight:600">${d.confidence}%</span>
        </div>
        <span class="sev-badge sev-${d.severity}">Severity: ${d.severity}</span>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,.08)">
          <p style="font-size:11px;color:rgba(250,248,242,.4);font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px">Recommended Treatment</p>
          <p>${d.treatment}</p>
        </div>
        <div style="margin-top:8px;font-size:10px;color:rgba(250,248,242,.3)">Mode: ${d.mode === 'ai' ? '✅ AI Analysis' : '⚡ Demo'}</div>`;
      setTimeout(() => {
        const fill = document.getElementById('confFill');
        if (fill) fill.style.width = d.confidence + '%';
      }, 100);
    }
    toast('✅ Analysis complete!');
  } catch (e) {
    toast('⚠️ Upload failed: ' + e.message);
  }
}

// ── SOIL ADVISORY ─────────────────────────────────────────
async function getSoilAdvisory() {
  const result = document.getElementById('soilResult');
  if (result) result.innerHTML = '<div class="loading-text">Analysing soil data...</div>';

  try {
    const r = await fetch('/api/soil-advisory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: document.getElementById('cropSelect')?.value || 'wheat',
        state: document.getElementById('stateSelect')?.value || 'MP',
        soil: document.getElementById('soilSelect')?.value || 'black',
        ph: parseFloat(document.getElementById('phInput')?.value || 7.0),
      }),
    });
    const d = await r.json();
    if (result) {
      result.innerHTML = `
        <div class="soil-result-card">
          <h5>🌍 Soil Profile</h5>
          <p>${d.soil_info.description}</p>
          <p style="margin-top:6px"><strong style="color:var(--gp)">Best crops:</strong> ${d.soil_info.crops.join(', ')}</p>
        </div>
        <div class="soil-result-card" style="margin-top:10px">
          <h5>🌱 NPK Recommendation (kg/hectare)</h5>
          <div class="npk-grid">
            <div class="npk-box"><span class="npk-num">${d.npk_recommendation.N}</span><span class="npk-label">Nitrogen (N)</span></div>
            <div class="npk-box"><span class="npk-num">${d.npk_recommendation.P}</span><span class="npk-label">Phosphorus (P)</span></div>
            <div class="npk-box"><span class="npk-num">${d.npk_recommendation.K}</span><span class="npk-label">Potassium (K)</span></div>
          </div>
        </div>
        <div class="soil-result-card" style="margin-top:10px">
          <h5>⚗️ pH & Amendments</h5>
          <p>${d.ph_advice}</p>
          <p style="margin-top:6px">${d.organic_matter}</p>
          <p style="margin-top:4px">${d.micronutrients}</p>
        </div>`;
    }
    toast('✅ Soil advisory ready!');
  } catch (e) {
    if (result) result.innerHTML = `<div class="loading-text">Error: ${e.message}</div>`;
  }
}

// ── VOICE ─────────────────────────────────────────────────
function toggleMic() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    toast('⚠️ Voice not supported in this browser. Use Chrome.');
    return;
  }
  if (isRec) { recognition?.stop(); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  recognition.interimResults = false;
  recognition.onstart = () => {
    isRec = true;
    document.getElementById('micBtn')?.classList.add('rec');
    toast('🎤 Listening...');
  };
  recognition.onresult = e => {
    const transcript = e.results[0][0].transcript;
    const ta = document.getElementById('msgInput');
    if (ta) ta.value = transcript;
    sendChat();
  };
  recognition.onerror = () => toast('⚠️ Could not hear clearly. Try again.');
  recognition.onend = () => {
    isRec = false;
    document.getElementById('micBtn')?.classList.remove('rec');
  };
  recognition.start();
}

// ── TOAST ─────────────────────────────────────────────────
function toast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 3000);
}

// ── SMOOTH SCROLL ─────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href');
    if (href === '#') return;
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
