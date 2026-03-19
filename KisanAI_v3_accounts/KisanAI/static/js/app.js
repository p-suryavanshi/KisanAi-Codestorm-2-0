// KisanAI v2 — Advanced Frontend
let lang = 'en', busy = false, recog = null, isRec = false;

// ── BOOT ──────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  loadWeather();
  loadMarket();
  loadNews();
  loadSchemes();
  loadPlanner();
  animateCounters();
  addMsg('ai', lang === 'hi'
    ? '🙏 नमस्ते! मैं KisanAI v2 हूँ।\n\n**नई सुविधाएं:**\n• 🌱 Crop Planner — बुवाई से कटाई तक\n• 💧 Precision Water Calculator\n• 📰 Live Agriculture News\n• 🧪 Soil Health Lab\n• 📈 Market Sparklines\n\nकोई भी सवाल पूछें!'
    : '👋 Welcome to **KisanAI v2** — your complete AI farming platform!\n\n**What\'s new:**\n• 🌱 Crop Planner with yield estimates\n• 💧 Precision water calculator\n• 📰 Live agriculture news feed\n• 🧪 Advanced soil health lab\n• 📈 Market trend sparklines\n\nAsk me anything about your farm!'
  );
});

// ── COUNTER ANIMATION ─────────────────────────────────────
function animateCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count);
    const suffix = el.parentElement.querySelector('.hstat-l')?.textContent.includes('Million') ? 'M+' :
                   el.parentElement.querySelector('.hstat-l')?.textContent.includes('%') ? '%' : '';
    let count = 0;
    const step = Math.ceil(target / 50);
    const t = setInterval(() => {
      count = Math.min(count + step, target);
      el.textContent = count + suffix;
      if (count >= target) clearInterval(t);
    }, 30);
  });
}

// ── LANG ──────────────────────────────────────────────────
function setLang(l, btn) {
  lang = l;
  document.querySelectorAll('.lo').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  const ta = document.getElementById('chatTa');
  if (ta) ta.placeholder = l === 'hi' ? 'अपनी फसल के बारे में पूछें...' : 'Ask about your crops...';
  toast(l === 'hi' ? '✅ हिंदी मोड चालू' : '✅ Switched to English');
}

// ── TABS ──────────────────────────────────────────────────
function showPane(name, btn) {
  document.querySelectorAll('.ptab').forEach(b => b.classList.remove('on'));
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById('pane' + name.charAt(0).toUpperCase() + name.slice(1))?.classList.add('on');
  if (name === 'market') loadMarket();
  if (name === 'news') loadNews();
  if (name === 'planner') loadPlanner();
}

// ── WEATHER ───────────────────────────────────────────────
async function loadWeather() {
  const state = document.getElementById('stateEl')?.value || 'MP';
  try {
    const r = await fetch(`/api/weather/${state}`);
    const d = await r.json();
    const icons = { sun:'☀️', 'cloud-sun':'⛅', smog:'🌫️', 'cloud-rain':'🌧️', default:'🌤️' };
    const ico = icons[d.icon] || icons.default;
    document.getElementById('wwCard').innerHTML = `
      <div class="ww-top">
        <div>
          <div class="ww-temp">${d.temp}°C</div>
          <div class="ww-feels">Feels like ${d.feels || d.temp + 2}°C</div>
          <div class="ww-desc">${d.desc} · ${state}</div>
        </div>
        <div class="ww-icon">${ico}</div>
      </div>
      <div class="ww-grid">
        <div class="ww-cell">Humidity <span>${d.humidity}%</span></div>
        <div class="ww-cell">Wind <span>${d.wind} km/h</span></div>
        <div class="ww-cell">Rain chance <span>${d.rain}%</span></div>
        <div class="ww-cell">UV Index <span>${d.uv}</span></div>
      </div>
      <div class="ww-fc">
        ${(d.forecast || []).map(f => `<div class="ww-day"><div class="ww-day-n">${f.day}</div><div class="ww-day-i">${f.icon}</div><div class="ww-day-t">${f.high}°</div></div>`).join('')}
      </div>
      <div class="ww-src">${d.source === 'live' ? '🟢 Live weather data' : '📦 Demo data'}</div>`;
    const alertEl = document.getElementById('wwAlert');
    if (alertEl && d.alert) { alertEl.style.display = 'flex'; alertEl.textContent = '⚠ ' + d.alert; }
  } catch { document.getElementById('wwCard').innerHTML = '<div class="lph">Weather unavailable</div>'; }
}

// ── MARKET ────────────────────────────────────────────────
async function loadMarket() {
  const list = document.getElementById('mktList');
  const ts = document.getElementById('mktTs');
  try {
    const r = await fetch('/api/market');
    const d = await r.json();
    if (ts) ts.textContent = d.updated || 'Updated now';
    if (list) list.innerHTML = d.prices.map(p => {
      const up = p.change >= 0;
      const maxH = Math.max(...p.trend); const minH = Math.min(...p.trend);
      const bars = p.trend.map(v => {
        const h = maxH === minH ? 10 : Math.round(((v - minH) / (maxH - minH)) * 18) + 2;
        const c = up ? 'rgba(82,183,136,0.5)' : 'rgba(244,162,97,0.5)';
        return `<div class="sb" style="height:${h}px;background:${c}"></div>`;
      }).join('');
      return `<div class="mi">
        <div class="mi-l">
          <div class="mi-ico">${p.icon}</div>
          <div><div class="mi-name">${p.crop} / ${p.hindi}</div><div class="mi-sub">per quintal</div></div>
        </div>
        <div class="mi-r">
          <div class="mi-price">₹${p.price.toLocaleString()}</div>
          <div class="mi-chg ${up ? 'c-up' : 'c-dn'}">${up ? '+' : ''}₹${p.change}</div>
          ${p.msp ? `<div class="mi-msp">MSP ₹${p.msp}</div>` : ''}
          <div class="sparkline">${bars}</div>
        </div>
      </div>`;
    }).join('');
  } catch { if (list) list.innerHTML = '<div class="lph">Market data unavailable</div>'; }
}

// ── PLANNER ───────────────────────────────────────────────
async function loadPlanner() {
  const body = document.getElementById('plannerBody');
  if (!body) return;
  const crop = document.getElementById('cropEl')?.value || 'wheat';
  const land = parseFloat(document.getElementById('landEl')?.value || 2.5);
  const soil = document.getElementById('soilEl')?.value || 'black';
  body.innerHTML = '<div class="lph">⏳ Loading...</div>';
  try {
    const [calR, yldR] = await Promise.all([
      fetch(`/api/crop-calendar/${crop}`),
      fetch(`/api/yield-estimate?crop=${crop}&soil=${soil}&land=${land}&irrigation=4`)
    ]);
    const cal = await calR.json();
    const yld = await yldR.json();
    body.innerHTML = `
      <div style="color:var(--cr)">
        <p style="font-size:13px;font-weight:600;color:var(--g5);margin-bottom:12px;text-transform:capitalize">📅 ${crop} Growing Calendar</p>
        <div class="cphase-grid">
          <div class="cphase sow"><div class="cphase-icon">🌱</div><div class="cphase-lbl">Sowing</div><div class="cphase-val">${cal.sow}</div></div>
          <div class="cphase grow"><div class="cphase-icon">🌿</div><div class="cphase-lbl">Growing</div><div class="cphase-val">${cal.grow}</div></div>
          <div class="cphase harv"><div class="cphase-icon">🌾</div><div class="cphase-lbl">Harvest</div><div class="cphase-val">${cal.harvest}</div></div>
        </div>
        <div class="var-box" style="margin-top:12px">
          <h5>Best Varieties</h5>
          <p>${cal.bestVariety}</p>
          <p style="margin-top:6px;color:rgba(250,248,242,.4)">Duration: ${cal.duration} · Seasons: ${(cal.seasons || []).join(', ')} · Irrigations needed: ${cal.irrigations}</p>
        </div>
        <div class="yield-cards">
          <div class="yc"><span class="yc-n">${yld.yield_per_acre} q</span><span class="yc-l">Yield/acre</span></div>
          <div class="yc"><span class="yc-n">${yld.total_yield} q</span><span class="yc-l">Total (${land} acres)</span></div>
          <div class="yc"><span class="yc-n">₹${(yld.estimated_revenue/1000).toFixed(0)}K</span><span class="yc-l">Est. Revenue</span></div>
          <div class="yc"><span class="yc-n">₹${yld.price_per_quintal}</span><span class="yc-l">Market Rate/q</span></div>
        </div>
      </div>`;
  } catch { body.innerHTML = '<div class="lph">Could not load planner</div>'; }
}

// ── SOIL ──────────────────────────────────────────────────
async function doSoil() {
  const out = document.getElementById('soilOut');
  if (out) out.innerHTML = '<div class="lph">🔬 Analysing...</div>';
  try {
    const r = await fetch('/api/soil-advisory', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ crop: document.getElementById('cropEl')?.value || 'wheat',
        state: document.getElementById('stateEl')?.value || 'MP',
        soil: document.getElementById('soilEl')?.value || 'black',
        ph: parseFloat(document.getElementById('phEl')?.value || 7.0) })
    });
    const d = await r.json();
    if (out) out.innerHTML = `
      <div class="soil-score"><div class="score-num">${d.score}</div><div class="score-info"><p style="font-size:12px;font-weight:600;color:var(--g5);margin-bottom:4px">Soil Quality Score / 100</p><p>${d.soil_profile.desc}</p><div class="info-tags"><span class="itag">pH Range: ${d.soil_profile.ph_range}</span><span class="itag">OM: ${d.soil_profile.om}</span><span class="itag">Drainage: ${d.soil_profile.drainage}</span></div></div></div>
      <p style="font-size:11px;font-weight:700;color:var(--g5);text-transform:uppercase;letter-spacing:.06em;margin:14px 0 8px">NPK Recommendation (kg/ha)</p>
      <div class="npk-row">
        <div class="nbox"><span class="nbox-ltr">Nitrogen</span><span class="nbox-val">${d.npk.N}</span><span class="nbox-unit">kg/ha</span></div>
        <div class="nbox"><span class="nbox-ltr">Phosphorus</span><span class="nbox-val">${d.npk.P}</span><span class="nbox-unit">kg/ha</span></div>
        <div class="nbox"><span class="nbox-ltr">Potassium</span><span class="nbox-val">${d.npk.K}</span><span class="nbox-unit">kg/ha</span></div>
      </div>
      <div class="tip-line" style="margin-top:10px"><strong>pH:</strong> ${d.ph_advice}</div>
      <div class="tip-line"><strong>Organic:</strong> ${d.organic}</div>
      <div class="tip-line"><strong>Micronutrients:</strong> ${d.micro}</div>`;
    toast('✅ Soil analysis complete!');
  } catch { if (out) out.innerHTML = '<div class="lph">Error loading soil data</div>'; }
}

// ── WATER ─────────────────────────────────────────────────
async function doWater() {
  const out = document.getElementById('waterOut');
  if (out) out.innerHTML = '<div class="lph">💧 Calculating...</div>';
  try {
    const r = await fetch('/api/water-calculator', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ crop: document.getElementById('cropEl')?.value || 'wheat',
        stage: document.getElementById('stageEl')?.value || 'tillering',
        area: parseFloat(document.getElementById('landEl')?.value || 2.5),
        soil: document.getElementById('soilEl')?.value || 'black' })
    });
    const d = await r.json();
    if (out) out.innerHTML = `
      <div class="wresult">
        <div class="wcard hl"><span class="wcard-n">${d.water_per_acre} cm</span><span class="wcard-l">Water/acre</span></div>
        <div class="wcard hl"><span class="wcard-n">${d.total_for_farm} cm</span><span class="wcard-l">Total for farm</span></div>
        <div class="wcard"><span class="wcard-n">${d.duration_hrs} hrs</span><span class="wcard-l">Irrigation time</span></div>
        <div class="wcard"><span class="wcard-n">${d.next_irrigation_days}d</span><span class="wcard-l">Next irrigation</span></div>
      </div>
      <div style="margin-top:10px;background:rgba(45,106,79,.15);border-radius:10px;padding:12px;font-size:12px;color:rgba(250,248,242,.6)"><strong style="color:var(--g5)">Stage:</strong> ${d.stage} &nbsp;|&nbsp; <strong style="color:var(--g5)">Seasonal total:</strong> ${d.total_seasonal} mm</div>
      <div class="tip-line" style="margin-top:8px">💡 ${d.tip}</div>`;
    toast('✅ Water calculation done!');
  } catch { if (out) out.innerHTML = '<div class="lph">Calculation error</div>'; }
}

// ── NEWS ──────────────────────────────────────────────────
async function loadNews() {
  const list = document.getElementById('newsList');
  if (!list) return;
  try {
    const r = await fetch('/api/news');
    const d = await r.json();
    list.innerHTML = d.news.map(n => `
      <div class="ni">
        <div class="ni-ico ${n.category}">${n.icon}</div>
        <div class="ni-content">
          <div class="ni-title">${n.title}</div>
          <div class="ni-meta"><span class="ni-cat">${n.category}</span><span class="ni-time">${n.time}</span></div>
        </div>
      </div>`).join('');
  } catch { if (list) list.innerHTML = '<div class="lph">News unavailable</div>'; }
}

// ── SCHEMES ───────────────────────────────────────────────
async function loadSchemes() {
  const grid = document.getElementById('schemesGrid');
  if (!grid) return;
  try {
    const r = await fetch('/api/schemes');
    const d = await r.json();
    grid.innerHTML = d.schemes.map(s => `
      <div class="sch-card">
        <div class="sch-head">
          <div class="sch-ico" style="background:${s.color}22">${s.icon}</div>
          <div class="sch-name">${s.name}</div>
        </div>
        <div class="sch-ben">${s.benefit}</div>
        <div class="sch-el">${s.eligibility}</div>
        <a href="${s.link}" target="_blank" class="sch-lnk">Visit portal ↗</a>
      </div>`).join('');
  } catch { if (grid) grid.innerHTML = '<div style="color:var(--mu);font-size:14px">Could not load schemes</div>'; }
}

// ── CHAT ──────────────────────────────────────────────────
function addMsg(role, text) {
  const box = document.getElementById('chatBody');
  if (!box) return;
  const time = new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
  const isAI = role === 'ai';
  const fmt = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>')
    .replace(/\|(.+?)\|/g, m => m) // basic table passthrough
    .replace(/•\s/g, '• ');
  const div = document.createElement('div');
  div.className = `msg ${isAI ? 'ai' : 'u'}`;
  div.innerHTML = `
    <div class="mav ${isAI ? 'ai' : 'usr'}">${isAI ? '🌾' : 'F'}</div>
    <div><div class="bbl">${fmt}</div><div class="mmeta">${time}</div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function showTyping() {
  const box = document.getElementById('chatBody');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg ai'; div.id = 'typingEl';
  div.innerHTML = `<div class="mav ai">🌾</div><div><div class="bbl"><div class="typr"><span></span><span></span><span></span></div></div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendChat() {
  const ta = document.getElementById('chatTa');
  const msg = ta?.value.trim();
  if (!msg || busy) return;
  addMsg('user', msg);
  ta.value = ''; ta.style.height = 'auto';
  busy = true;
  document.getElementById('sendBtn').disabled = true;
  showTyping();
  try {
    const r = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: msg, language: lang,
        crop: document.getElementById('cropEl')?.value || 'wheat',
        state: document.getElementById('stateEl')?.value || 'MP',
        soil: document.getElementById('soilEl')?.value || 'black',
        land: parseFloat(document.getElementById('landEl')?.value || 2.5) })
    });
    const d = await r.json();
    document.getElementById('typingEl')?.remove();
    addMsg('ai', d.reply || 'Sorry, no response received.');
  } catch (e) {
    document.getElementById('typingEl')?.remove();
    addMsg('ai', `⚠️ Connection error — is the server running?\n\n${e.message}`);
  }
  busy = false;
  document.getElementById('sendBtn').disabled = false;
}

function qs(btn) {
  const ta = document.getElementById('chatTa');
  if (ta) ta.value = btn.textContent.replace(/^[^\s]+\s/, '').replace(/\?$/, '?');
  showPane('chat', document.querySelector('.ptab.on') || document.querySelector('.ptab'));
  sendChat();
}

// ── PEST ──────────────────────────────────────────────────
function doDrop(e) {
  e.preventDefault();
  document.getElementById('upZone')?.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if (f?.type.startsWith('image/')) uploadPest(f);
}
function doFile(e) { const f = e.target.files[0]; if (f) uploadPest(f); }

async function uploadPest(file) {
  const prev = document.getElementById('upPrev');
  const hint = document.getElementById('upHint');
  const card = document.getElementById('pestCard');
  const reader = new FileReader();
  reader.onload = e => { if (prev) { prev.src = e.target.result; prev.style.display = 'block'; } if (hint) hint.style.display = 'none'; };
  reader.readAsDataURL(file);
  if (card) card.style.display = 'none';
  toast('🔬 Analysing image with AI...');
  try {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('language', lang);
    const r = await fetch('/api/pest-detect', { method:'POST', body:fd });
    const d = await r.json();
    if (card) {
      card.style.display = 'block';
      card.innerHTML = `
        <h4>🔬 ${d.name}</h4>
        <p>${d.description}</p>
        <div class="cbar-row">
          <span style="font-size:11px;color:rgba(250,248,242,.4)">Confidence</span>
          <div class="cbar-track"><div class="cbar-fill" id="cbarFill" style="width:0%"></div></div>
          <span style="font-size:11px;color:var(--g5);font-weight:700">${d.confidence}%</span>
        </div>
        <span class="sev sev-${d.severity}">Severity: ${d.severity}</span>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,.07)">
          <p style="font-size:10px;color:rgba(250,248,242,.35);text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-bottom:6px">Chemical Treatment</p>
          <p>${d.treatment}</p>
        </div>
        ${d.organic ? `<div class="organic-tip"><span>🌿 Organic Alternative</span><p>${d.organic}</p></div>` : ''}
        <div style="margin-top:8px;font-size:10px;color:rgba(250,248,242,.25)">Mode: ${d.mode === 'ai' ? '✅ GPT-4 Vision' : '⚡ Demo'}</div>`;
      setTimeout(() => { document.getElementById('cbarFill')?.style.setProperty('width', d.confidence + '%'); }, 100);
    }
    toast('✅ Analysis complete!');
  } catch (e) { toast('⚠️ Upload failed: ' + e.message); }
}

// ── VOICE ─────────────────────────────────────────────────
function toggleMic() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    toast('⚠️ Voice not supported. Use Chrome.'); return;
  }
  if (isRec) { recog?.stop(); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recog = new SR();
  recog.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  recog.interimResults = false;
  recog.onstart = () => { isRec = true; document.getElementById('micBtn')?.classList.add('rec'); toast('🎤 Listening...'); };
  recog.onresult = e => { const t = e.results[0][0].transcript; const ta = document.getElementById('chatTa'); if (ta) ta.value = t; sendChat(); };
  recog.onerror = () => toast('⚠️ Could not hear. Try again.');
  recog.onend = () => { isRec = false; document.getElementById('micBtn')?.classList.remove('rec'); };
  recog.start();
}

// ── TOAST ─────────────────────────────────────────────────
function toast(msg) {
  const el = document.getElementById('toastEl');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 3200);
}

// ── SMOOTH SCROLL ─────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const h = a.getAttribute('href');
    if (h === '#') return;
    e.preventDefault();
    document.querySelector(h)?.scrollIntoView({ behavior:'smooth', block:'start' });
  });
});
