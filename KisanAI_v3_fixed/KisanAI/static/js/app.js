// KisanAI v3 — Fixed Frontend (all bugs resolved)
'use strict';
let lang = 'en', busy = false, recog = null, isRec = false;

// ── BOOT ──────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  loadWeather();
  loadMarket();
  loadNews();
  loadSchemes();
  animateCounters();
  addMsg('ai', '👋 Welcome to **KisanAI v3**!\n\nI can help with:\n🌾 Crop advice for ANY crop (type your own!)\n💧 Irrigation & fertilizer schedules\n🔬 Pest detection via photo upload\n📈 Live mandi prices\n📅 Crop calendar & yield estimates\n\nTell me your crop and problem!');
});

// ── STATE / CROP HELPERS ──────────────────────────────────
function getProfile() {
  const crop = getCrop();
  const state = document.getElementById('stateEl')?.value || 'MP';
  return {
    crop,
    state,
    soil:  document.getElementById('soilEl')?.value  || 'black',
    land:  parseFloat(document.getElementById('landEl')?.value || 2.5),
    city:  document.getElementById('cityEl')?.value  || '',
    language: lang
  };
}

// FIX: Support both dropdown + custom crop text input
function getCrop() {
  const customEl = document.getElementById('customCropEl');
  const dropEl   = document.getElementById('cropEl');
  const custom = customEl?.value.trim();
  if (custom && custom.length > 0) return custom.toLowerCase();
  return dropEl?.value || 'wheat';
}

// Toggle custom crop input visibility
function toggleCustomCrop(val) {
  const box = document.getElementById('customCropBox');
  if (!box) return;
  if (val === '__custom__') {
    box.style.display = 'block';
    document.getElementById('customCropEl').focus();
  } else {
    box.style.display = 'none';
    document.getElementById('customCropEl').value = '';
    // Reload planner for new crop selection
    if (document.getElementById('panePlanner')?.classList.contains('on')) loadPlanner();
  }
}

// ── COUNTER ANIMATION ─────────────────────────────────────
function animateCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    const label  = el.dataset.label || '';  // FIX: use data-label not DOM traversal
    let count = 0;
    const step = Math.max(1, Math.ceil(target / 50));
    const t = setInterval(() => {
      count = Math.min(count + step, target);
      el.textContent = count + label;
      if (count >= target) clearInterval(t);
    }, 28);
  });
}

// ── LANGUAGE ──────────────────────────────────────────────
function setLang(l, btn) {
  lang = l;
  document.querySelectorAll('.lo').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  const ta = document.getElementById('chatTa');
  if (ta) ta.placeholder = l === 'hi' ? 'अपनी फसल के बारे में पूछें...' : 'Ask about your crops or problem...';
  toast(l === 'hi' ? '✅ हिंदी मोड चालू' : '✅ English mode on');
}

// ── TABS ──────────────────────────────────────────────────
// FIX: showPane now properly finds the active tab button
function showPane(name, btn) {
  document.querySelectorAll('.ptab').forEach(b => b.classList.remove('on'));
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('on'));
  btn.classList.add('on');
  const paneId = 'pane' + name.charAt(0).toUpperCase() + name.slice(1);
  const pane = document.getElementById(paneId);
  if (pane) pane.classList.add('on');
  // Lazy-load only when tab is opened
  if (name === 'market')  loadMarket();
  if (name === 'news')    loadNews();
  if (name === 'planner') loadPlanner();
  if (name === 'water')   resetWater();
}

// ── WEATHER ───────────────────────────────────────────────
async function loadWeather() {
  const state = document.getElementById('stateEl')?.value || 'MP';
  const city  = document.getElementById('cityEl')?.value || '';
  const card  = document.getElementById('wwCard');
  const alertEl = document.getElementById('wwAlert');
  try {
    const r = await fetch(`/api/weather/${encodeURIComponent(state)}?city=${encodeURIComponent(city)}`);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const weatherIcons = { 'Partly Cloudy':'⛅','Clear':'☀️','Foggy':'🌫️','Hot & Dry':'🌞','Sunny & Hot':'🌞','Humid':'🌦️','Warm':'🌤️','Pleasant':'🌤️','Cloudy':'☁️','Hazy':'🌫️','Hot & Humid':'🌦️','Sunny':'☀️' };
    const ico = weatherIcons[d.desc] || '🌤️';
    card.innerHTML = `
      <div class="ww-top">
        <div>
          <div class="ww-temp">${d.temp}°C</div>
          <div class="ww-feels">Feels like ${d.feels || d.temp}°C</div>
          <div class="ww-desc">${d.desc}${d.city ? ' · ' + d.city : ''}</div>
        </div>
        <div class="ww-icon">${ico}</div>
      </div>
      <div class="ww-grid">
        <div class="ww-cell">Humidity <span>${d.humidity}%</span></div>
        <div class="ww-cell">Wind <span>${d.wind} km/h</span></div>
        <div class="ww-cell">Rain <span>${d.rain}%</span></div>
        <div class="ww-cell">UV <span>${d.uv}</span></div>
      </div>
      <div class="ww-fc">${(d.forecast||[]).map(f=>`<div class="ww-day"><div class="ww-day-n">${f.day}</div><div class="ww-day-i">${f.icon}</div><div class="ww-day-t">${f.high}°</div></div>`).join('')}</div>
      <div class="ww-src">${d.source==='live'?'🟢 Live data':'📦 Demo data'}</div>`;
    if (alertEl && d.alert) { alertEl.textContent = '⚠ ' + d.alert; alertEl.style.display = 'flex'; }
    else if (alertEl) alertEl.style.display = 'none';
  } catch (e) {
    if (card) card.innerHTML = '<div class="lph">⚠ Weather unavailable</div>';
  }
}

// ── MARKET ────────────────────────────────────────────────
async function loadMarket() {
  const list = document.getElementById('mktList');
  const ts   = document.getElementById('mktTs');
  if (!list) return;
  try {
    const r = await fetch('/api/market');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    if (ts) ts.textContent = d.updated || '';
    list.innerHTML = d.prices.map(p => {
      // FIX: determine sparkline color per item, not globally
      const isUp = p.change >= 0;
      const trend = p.trend || [];
      const maxH = Math.max(...trend, 1);
      const minH = Math.min(...trend, 0);
      const range = maxH - minH || 1;
      const bars = trend.map((v, i) => {
        const h = Math.round(((v - minH) / range) * 18) + 2;
        const isLast = i === trend.length - 1;
        const col = isUp ? (isLast ? '#52b788' : 'rgba(82,183,136,0.4)') : (isLast ? '#f4a261' : 'rgba(244,162,97,0.4)');
        return `<div class="sb" style="height:${h}px;background:${col}"></div>`;
      }).join('');
      return `<div class="mi">
        <div class="mi-l">
          <div class="mi-ico">${p.icon}</div>
          <div>
            <div class="mi-name">${p.crop} / ${p.hindi}</div>
            <div class="mi-sub">per quintal · AgMarkNet</div>
          </div>
        </div>
        <div class="mi-r">
          <div class="mi-price">₹${p.price.toLocaleString('en-IN')}</div>
          <div class="mi-chg ${isUp?'c-up':'c-dn'}">${isUp?'+':''}₹${p.change}</div>
          ${p.msp?`<div class="mi-msp">MSP ₹${p.msp.toLocaleString('en-IN')}</div>`:''}
          <div class="sparkline">${bars}</div>
        </div>
      </div>`;
    }).join('');
  } catch (e) {
    if (list) list.innerHTML = `<div class="lph">⚠ Market data unavailable: ${e.message}</div>`;
  }
}

// ── PLANNER ───────────────────────────────────────────────
async function loadPlanner() {
  const body = document.getElementById('plannerBody');
  if (!body) return;
  const p = getProfile();
  body.innerHTML = '<div class="lph">⏳ Loading crop calendar...</div>';
  try {
    const [calR, yldR] = await Promise.all([
      fetch(`/api/crop-calendar/${encodeURIComponent(p.crop)}`),
      fetch(`/api/yield-estimate?crop=${encodeURIComponent(p.crop)}&soil=${p.soil}&land=${p.land}&irrigation=4`)
    ]);
    const cal = await calR.json();
    const yld = await yldR.json();
    const noteHtml = cal.note ? `<div class="tip-line" style="margin-bottom:10px">ℹ️ ${cal.note}</div>` : '';
    const yldNote = yld.note ? `<div class="tip-line" style="margin-top:8px;font-size:11px">ℹ️ ${yld.note}</div>` : '';
    body.innerHTML = `
      ${noteHtml}
      <p style="font-size:13px;font-weight:600;color:var(--g5);margin-bottom:12px;text-transform:capitalize">📅 ${p.crop.charAt(0).toUpperCase()+p.crop.slice(1)} Growing Calendar</p>
      <div class="cphase-grid">
        <div class="cphase sow"><div class="cphase-icon">🌱</div><div class="cphase-lbl">Sowing</div><div class="cphase-val">${cal.sow}</div></div>
        <div class="cphase grow"><div class="cphase-icon">🌿</div><div class="cphase-lbl">Growing</div><div class="cphase-val">${cal.grow}</div></div>
        <div class="cphase harv"><div class="cphase-icon">🌾</div><div class="cphase-lbl">Harvest</div><div class="cphase-val">${cal.harvest}</div></div>
      </div>
      <div class="var-box" style="margin-top:12px">
        <h5>Best Varieties</h5>
        <p>${cal.bestVariety}</p>
        <p style="margin-top:6px;color:rgba(250,248,242,.4);font-size:11px">Duration: ${cal.duration} · Seasons: ${(cal.seasons||[]).join(', ')} · Irrigations: ${cal.irrigations}</p>
      </div>
      <div class="yield-cards">
        <div class="yc"><span class="yc-n">${yld.yield_per_acre} q</span><span class="yc-l">Yield/acre</span></div>
        <div class="yc"><span class="yc-n">${yld.total_yield} q</span><span class="yc-l">Total (${p.land} acres)</span></div>
        <div class="yc"><span class="yc-n">₹${(yld.estimated_revenue/1000).toFixed(0)}K</span><span class="yc-l">Est. Revenue</span></div>
        <div class="yc"><span class="yc-n">₹${(yld.price_per_quintal).toLocaleString('en-IN')}</span><span class="yc-l">Rate/quintal</span></div>
      </div>
      ${yldNote}`;
  } catch (e) {
    body.innerHTML = `<div class="lph">⚠ Could not load planner: ${e.message}</div>`;
  }
}

// ── SOIL ──────────────────────────────────────────────────
async function doSoil() {
  const out = document.getElementById('soilOut');
  if (out) out.innerHTML = '<div class="lph">🔬 Analysing soil...</div>';
  const p = getProfile();
  const ph = parseFloat(document.getElementById('phEl')?.value || 7.0);
  if (isNaN(ph) || ph < 0 || ph > 14) {
    if (out) out.innerHTML = '<div class="lph" style="color:#f4a261">⚠ Enter a valid pH between 0 and 14</div>';
    return;
  }
  try {
    const r = await fetch('/api/soil-advisory', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ crop: p.crop, state: p.state, soil: p.soil, ph })
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const noteHtml = d.note ? `<div class="tip-line" style="margin-bottom:10px">ℹ️ ${d.note}</div>` : '';
    out.innerHTML = `
      ${noteHtml}
      <div class="soil-score">
        <div class="score-num">${d.score}</div>
        <div class="score-info">
          <p style="font-size:12px;font-weight:600;color:var(--g5);margin-bottom:4px">Soil Quality Score / 100</p>
          <p>${d.soil_profile.desc}</p>
          <div class="info-tags">
            <span class="itag">pH Range: ${d.soil_profile.ph_range}</span>
            <span class="itag">OM: ${d.soil_profile.om}</span>
            <span class="itag">Drainage: ${d.soil_profile.drainage}</span>
          </div>
          <p style="font-size:11px;color:rgba(250,248,242,.4);margin-top:6px">Best for: ${d.soil_profile.best_for}</p>
        </div>
      </div>
      <p style="font-size:11px;font-weight:700;color:var(--g5);text-transform:uppercase;letter-spacing:.06em;margin:14px 0 8px">NPK Recommendation (kg/hectare)</p>
      <div class="npk-row">
        <div class="nbox"><span class="nbox-ltr">Nitrogen</span><span class="nbox-val">${d.npk.N}</span><span class="nbox-unit">kg/ha</span></div>
        <div class="nbox"><span class="nbox-ltr">Phosphorus</span><span class="nbox-val">${d.npk.P}</span><span class="nbox-unit">kg/ha</span></div>
        <div class="nbox"><span class="nbox-ltr">Potassium</span><span class="nbox-val">${d.npk.K}</span><span class="nbox-unit">kg/ha</span></div>
      </div>
      <div class="tip-line" style="margin-top:10px"><strong>pH:</strong> ${d.ph_advice}</div>
      <div class="tip-line"><strong>Organic:</strong> ${d.organic}</div>
      <div class="tip-line"><strong>Micronutrients:</strong> ${d.micro}</div>`;
    toast('✅ Soil analysis complete!');
  } catch (e) {
    if (out) out.innerHTML = `<div class="lph">⚠ Error: ${e.message}</div>`;
  }
}

// ── WATER ─────────────────────────────────────────────────
function resetWater() {
  const out = document.getElementById('waterOut');
  if (out) out.innerHTML = '';
}

async function doWater() {
  const out = document.getElementById('waterOut');
  if (out) out.innerHTML = '<div class="lph">💧 Calculating...</div>';
  const p = getProfile();
  const stage = document.getElementById('stageEl')?.value || 'tillering';
  if (!p.land || p.land <= 0) {
    if (out) out.innerHTML = '<div class="lph" style="color:#f4a261">⚠ Enter a valid land area in your farm profile</div>';
    return;
  }
  try {
    const r = await fetch('/api/water-calculator', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ crop: p.crop, stage, area: p.land, soil: p.soil })
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const noteHtml = d.note ? `<div class="tip-line" style="margin-bottom:10px">ℹ️ ${d.note}</div>` : '';
    out.innerHTML = `
      ${noteHtml}
      <div class="wresult">
        <div class="wcard hl"><span class="wcard-n">${d.water_per_acre} cm</span><span class="wcard-l">Water per acre</span></div>
        <div class="wcard hl"><span class="wcard-n">${d.total_for_farm} cm</span><span class="wcard-l">Total for ${p.land} acres</span></div>
        <div class="wcard"><span class="wcard-n">${d.duration_hrs} hrs</span><span class="wcard-l">Est. irrigation time</span></div>
        <div class="wcard"><span class="wcard-n">~${d.next_irrigation_days}d</span><span class="wcard-l">Next irrigation due</span></div>
      </div>
      <div style="margin-top:10px;background:rgba(45,106,79,.15);border-radius:10px;padding:12px;font-size:12px;color:rgba(250,248,242,.6)">
        <strong style="color:var(--g5)">Crop:</strong> ${d.crop} &nbsp;|&nbsp;
        <strong style="color:var(--g5)">Stage:</strong> ${d.stage} &nbsp;|&nbsp;
        <strong style="color:var(--g5)">Seasonal total:</strong> ${d.total_seasonal_mm} mm
      </div>
      <div class="tip-line" style="margin-top:8px">💡 ${d.tip}</div>`;
    toast('✅ Water calculation done!');
  } catch (e) {
    if (out) out.innerHTML = `<div class="lph">⚠ Calculation failed: ${e.message}</div>`;
  }
}

// ── NEWS ──────────────────────────────────────────────────
async function loadNews() {
  const list = document.getElementById('newsList');
  if (!list) return;
  try {
    const r = await fetch('/api/news');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    list.innerHTML = d.news.map(n => `
      <div class="ni">
        <div class="ni-ico ${n.category}">${n.icon}</div>
        <div class="ni-content">
          <div class="ni-title">${n.title}</div>
          <div class="ni-meta"><span class="ni-cat">${n.category}</span><span class="ni-time">${n.time}</span></div>
        </div>
      </div>`).join('');
  } catch (e) {
    if (list) list.innerHTML = `<div class="lph">⚠ News unavailable</div>`;
  }
}

// ── SCHEMES ───────────────────────────────────────────────
async function loadSchemes() {
  const grid = document.getElementById('schemesGrid');
  if (!grid) return;
  try {
    const r = await fetch('/api/schemes');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    grid.innerHTML = d.schemes.map(s => `
      <div class="sch-card">
        <div class="sch-head">
          <div class="sch-ico" style="background:${s.color}22">${s.icon}</div>
          <div class="sch-name">${s.name}</div>
        </div>
        <div class="sch-ben">${s.benefit}</div>
        <div class="sch-el">${s.eligibility}</div>
        <a href="${s.link}" target="_blank" rel="noopener" class="sch-lnk">Visit portal ↗</a>
      </div>`).join('');
  } catch (e) {
    if (grid) grid.innerHTML = '<div style="color:var(--mu);font-size:14px">Could not load schemes</div>';
  }
}

// ── CHAT ──────────────────────────────────────────────────
function addMsg(role, text) {
  const box = document.getElementById('chatBody');
  if (!box) return;
  const time = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  const isAI = role === 'ai';
  // Format: bold, line breaks, preserve simple tables
  const fmt = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
  const div = document.createElement('div');
  div.className = `msg ${isAI?'ai':'u'}`;
  div.innerHTML = `
    <div class="mav ${isAI?'ai':'usr'}">${isAI?'🌾':'F'}</div>
    <div><div class="bbl">${fmt}</div><div class="mmeta">${time}</div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function showTyping() {
  const box = document.getElementById('chatBody');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg ai'; div.id = 'typEl';
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
  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn) sendBtn.disabled = true;
  showTyping();
  const p = getProfile();
  try {
    const r = await fetch('/api/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message: msg, language: lang, ...p })
    });
    if (!r.ok) throw new Error(`Server error ${r.status}`);
    const d = await r.json();
    document.getElementById('typEl')?.remove();
    addMsg('ai', d.reply || 'Sorry, no response received.');
  } catch (e) {
    document.getElementById('typEl')?.remove();
    addMsg('ai', `⚠️ **Connection error**\n\n${e.message}\n\nMake sure the server is running: \`python main.py\``);
  }
  busy = false;
  if (sendBtn) sendBtn.disabled = false;
}

// FIX: qs() now switches to chat pane before sending
function qs(btn) {
  // Switch to chat tab
  const chatTabBtn = document.querySelector('.ptab.on') || document.querySelector('.ptab');
  const allPtabs = document.querySelectorAll('.ptab');
  // Find and click the chat tab
  allPtabs.forEach(t => { if (t.textContent.includes('Chat')) t.click(); });
  const ta = document.getElementById('chatTa');
  if (ta) {
    // Strip emoji prefix from quick prompt text
    ta.value = btn.textContent.replace(/^[\u{1F300}-\u{1F9FF}\s]+/u, '').replace(/\?$/, '') + '?';
  }
  setTimeout(sendChat, 100); // small delay to let tab switch render
}

// ── PEST DETECTION ────────────────────────────────────────
function doDrop(e) {
  e.preventDefault();
  document.getElementById('upZone')?.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if (!f) return;
  if (!f.type.startsWith('image/')) { toast('⚠️ Please upload an image file (JPG, PNG, WEBP)'); return; }
  uploadPest(f);
}

function doFile(e) {
  const f = e.target.files[0];
  if (f) uploadPest(f);
  e.target.value = ''; // reset so same file can be re-uploaded
}

async function uploadPest(file) {
  if (file.size > 10 * 1024 * 1024) { toast('⚠️ File too large. Max 10MB.'); return; }
  const prev = document.getElementById('upPrev');
  const hint = document.getElementById('upHint');
  const card = document.getElementById('pestCard');
  const reader = new FileReader();
  reader.onload = e => {
    if (prev) { prev.src = e.target.result; prev.style.display = 'block'; }
    if (hint) hint.style.display = 'none';
  };
  reader.readAsDataURL(file);
  if (card) card.style.display = 'none';
  toast('🔬 Analysing image...');
  try {
    const p = getProfile();
    const fd = new FormData();
    fd.append('file', file);
    fd.append('language', lang);
    fd.append('crop', p.crop);
    const r = await fetch('/api/pest-detect', {method:'POST', body:fd});
    if (!r.ok) {
      const err = await r.json().catch(() => ({detail:'Unknown error'}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    const d = await r.json();
    if (card) {
      card.style.display = 'block';
      // FIX: Use consistent class name 'cbar-fill' everywhere
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
        ${d.error ? `<p style="font-size:10px;color:rgba(250,248,242,.25);margin-top:6px">AI fallback used: ${d.error}</p>` : ''}
        <div style="margin-top:6px;font-size:10px;color:rgba(250,248,242,.25)">Mode: ${d.mode==='ai'?'✅ GPT-4 Vision':'⚡ Demo'} · Crop context: ${d.crop_context||'general'}</div>`;
      setTimeout(() => { const f = document.getElementById('cbarFill'); if (f) f.style.width = d.confidence + '%'; }, 100);
    }
    toast('✅ Analysis complete!');
  } catch (e) {
    toast('⚠️ Upload failed: ' + e.message);
    if (card) { card.style.display = 'block'; card.innerHTML = `<p style="color:#f4a261;font-size:13px">⚠ ${e.message}</p>`; }
  }
}

// ── VOICE ─────────────────────────────────────────────────
function toggleMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast('⚠️ Voice not supported. Please use Chrome browser.'); return; }
  if (isRec) { recog?.stop(); return; }
  recog = new SR();
  recog.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  recog.interimResults = false;
  recog.maxAlternatives = 1;
  recog.onstart = () => { isRec = true; document.getElementById('micBtn')?.classList.add('rec'); toast('🎤 Listening... speak now'); };
  recog.onresult = e => {
    const transcript = e.results[0][0].transcript;
    const ta = document.getElementById('chatTa');
    if (ta) { ta.value = transcript; ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 110) + 'px'; }
    sendChat();
  };
  recog.onerror = ev => {
    const msgs = { 'no-speech':'No speech detected. Try again.', 'audio-capture':'Microphone not available.', 'not-allowed':'Microphone permission denied. Allow mic in browser settings.' };
    toast('⚠️ ' + (msgs[ev.error] || 'Voice error: ' + ev.error));
  };
  recog.onend = () => { isRec = false; document.getElementById('micBtn')?.classList.remove('rec'); };
  try { recog.start(); } catch (e) { toast('⚠️ Could not start voice: ' + e.message); }
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
document.addEventListener('click', e => {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  const href = a.getAttribute('href');
  if (href === '#' || !href) return;
  const target = document.querySelector(href);
  if (!target) return;
  e.preventDefault();
  target.scrollIntoView({behavior:'smooth', block:'start'});
});
