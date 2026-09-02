const API_BASE = localStorage.getItem('orca_api_base') || 'http://127.0.0.1:8000';
let conversationId = localStorage.getItem('orca_conversation_id') || `conv_${crypto.randomUUID().slice(0, 10)}`;
let lastResult = null;
let map, locationMarker, pfzLayer, hazardLayer, routeLayer, geofenceLayer;

const $ = (id) => document.getElementById(id);

function setStatus(ok, text) {
  const el = $('apiStatus');
  el.classList.toggle('ok', ok);
  el.querySelector('span').textContent = text;
}

async function pingBackend() {
  try {
    const r = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
    if (!r.ok) throw new Error('backend offline');
    setStatus(true, 'Backend online');
  } catch {
    setStatus(false, 'Backend offline');
  }
}

function initMap() {
  map = L.map('map', { zoomControl: true, worldCopyJump: true }).setView([20.5937, 78.9629], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map);
  pfzLayer = L.layerGroup().addTo(map);
  hazardLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);
  geofenceLayer = L.layerGroup().addTo(map);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function addMessage(role, text, meta='') {
  const stream = $('chatStream');
  const empty = stream.querySelector('.empty-chat');
  if (empty) empty.remove();
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  wrap.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? 'U' : 'O'}</div>
    <div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-meta">${escapeHtml(meta)}</div>
    </div>`;
  stream.appendChild(wrap);
  stream.scrollTop = stream.scrollHeight;
}

function renderTyping() {
  const stream = $('chatStream');
  const el = document.createElement('div');
  el.className = 'msg';
  el.id = 'typingMsg';
  el.innerHTML = `<div class="msg-avatar">O</div><div><div class="msg-bubble">ORCA is coordinating marine agents…</div><div class="msg-meta">Planner → data agents → fusion → intelligence</div></div>`;
  stream.appendChild(el); stream.scrollTop = stream.scrollHeight;
}
function removeTyping(){ $('typingMsg')?.remove(); }

function pointValue(p) {
  if (!p || p.value === null || p.value === undefined) return '—';
  const v = Number(p.value);
  return Number.isFinite(v) ? `${Number(v.toFixed(2))}${p.unit ? ` ${p.unit}` : ''}` : '—';
}

function statusClass(value){
  const x = String(value || '').toLowerCase();
  if (x.includes('high') || x.includes('insufficient')) return 'danger';
  if (x.includes('moderate') || x.includes('caution')) return 'warn';
  if (x.includes('low') || x.includes('normal')) return 'good';
  return '';
}

function renderMetrics(ocean, weather) {
  const items = [
    ['Sea surface temperature', ocean?.sea_surface_temperature, 'sea_surface_temperature'],
    ['Wave height', ocean?.wave_height, 'wave_height'],
    ['Wave period', ocean?.wave_period, 'wave_period'],
    ['Current speed', ocean?.current_speed, 'current_speed'],
    ['Wind speed', weather?.wind_speed, 'wind_speed'],
    ['Sea level', ocean?.sea_level, 'sea_level'],
  ];
  $('metricGrid').innerHTML = items.map(([label, point]) => {
    const unavailable = !point || point.value === null || point.value === undefined;
    const cls = statusClass(point?.status);
    return `<div class="metric ${unavailable ? 'empty' : cls}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(pointValue(point))}</strong>
      <small>${unavailable ? 'Unavailable' : `${escapeHtml(point.source || 'Unknown source')} · ${point.source_type === 'observation' ? 'Observation' : 'Model'}`}</small>
    </div>`;
  }).join('');
}

function sourceLabel(src) {
  const name = src?.name || src?.source || 'Source';
  const type = src?.type || src?.source_type || '';
  const url = src?.url || src?.source_url || '';
  return `<div class="source-item">
    <div class="source-name">${escapeHtml(name)} <span class="source-type">${escapeHtml(type)}</span></div>
    ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>` : ''}
    ${src?.note ? `<small>${escapeHtml(src.note)}</small>` : ''}
  </div>`;
}

function renderSources(result) {
  const sources = Array.isArray(result?.sources) ? result.sources : [];
  $('sourceCount').textContent = sources.length;
  $('sourceList').innerHTML = sources.length ? sources.map(sourceLabel).join('') : '<div class="source-empty">No source metadata returned.</div>';
}

function renderTrace(result) {
  const steps = document.querySelectorAll('.trace-step');
  steps.forEach(s => s.classList.remove('done'));
  steps.forEach((s, i) => { if (i < 5) s.classList.add('done'); });
}

function clearMapLayers(){
  pfzLayer.clearLayers(); hazardLayer.clearLayers(); routeLayer.clearLayers(); geofenceLayer.clearLayers();
}

function renderMap(result) {
  clearMapLayers();
  const loc = result?.location;
  if (!loc?.latitude || !loc?.longitude) return;
  const latlng = [loc.latitude, loc.longitude];
  if (locationMarker) map.removeLayer(locationMarker);
  locationMarker = L.circleMarker(latlng, { radius: 8, weight: 2, color: '#75e4ff', fillColor: '#75e4ff', fillOpacity: .75 })
    .addTo(map).bindPopup(`<b>${escapeHtml(loc.name || 'Selected location')}</b><br>${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`);
  map.setView(latlng, 8, { animate: true });

  (result.pfz || []).forEach(p => {
    if (p.latitude == null || p.longitude == null) return;
    L.circleMarker([p.latitude, p.longitude], { radius: 7, weight: 1, color: '#6ce4a4', fillColor: '#6ce4a4', fillOpacity: .75 })
      .addTo(pfzLayer).bindPopup(`<b>Potential Fishing Zone</b><br>${escapeHtml(p.sector || '')}<br>${p.distance_km != null ? `${p.distance_km.toFixed(1)} km away` : ''}`);
  });

  (result.hazards || []).forEach(h => {
    const center = latlng;
    if (h.location?.latitude && h.location?.longitude) {
      L.circleMarker([h.location.latitude, h.location.longitude], { radius: 7, weight: 1, color: '#ff8a97', fillColor: '#ff8a97', fillOpacity: .8 }).addTo(hazardLayer).bindPopup(`<b>${escapeHtml(h.name)}</b><br>${escapeHtml(h.details || h.severity || '')}`);
    }
  });

  const route = result.route;
  if (route?.points?.length) {
    L.polyline(route.points.map(p => [p.latitude, p.longitude]), { color: '#7fe1f7', weight: 4, opacity: .9 }).addTo(routeLayer);
  }

  (result.geofencing || []).forEach(g => {
    if (!g) return;
    const ring = L.circle(latlng, { radius: Math.max(100, Number(g.distance_km || 0) * 1000), color: g.inside ? '#ff7f8d' : '#f5c75c', weight: 1, fillOpacity: .05 });
    ring.addTo(geofenceLayer).bindPopup(`<b>${escapeHtml(g.name || 'Geofence')}</b><br>${g.inside ? 'Inside zone' : `${Number(g.distance_km).toFixed(1)} km away`}`);
  });

  const pfzCount = (result.pfz || []).length;
  $('mapOverlay').textContent = `${loc.name || 'Location'} · ${(result.hazards || []).length} hazards · ${pfzCount} PFZ records`;
}

function renderResult(result) {
  lastResult = result;
  const loc = result.location || {};
  const assessment = result.risks || {};
  const quality = result.data_quality || {};

  $('conversationId').textContent = result.conversation_id || conversationId;
  $('languageLabel').textContent = (result.language || 'en').toUpperCase();
  $('locationTitle').textContent = loc.name || 'Selected marine location';
  $('locationMeta').textContent = `${Number(loc.latitude).toFixed(4)}, ${Number(loc.longitude).toFixed(4)} · ${result.intent?.time_range || 'current'}`;

  const answer = result.answer || {};
  addMessage('assistant', `${answer.summary || 'ORCA returned a marine assessment.'}\n\n${(answer.observations || []).slice(0, 3).map(x => `• ${x}`).join('\n')}`, `Status: ${answer.status || 'unknown'} · ${result.request_id || ''}`);

  renderMetrics(result.ocean || {}, result.weather || {});
  const overall = assessment.safety_assessment || assessment.overall_status || answer.status || 'unknown';
  $('overallStatus').className = `status-pill ${String(overall).toLowerCase().includes('insufficient') ? 'insufficient_data_for_safety_assessment' : String(overall).toLowerCase()}`;
  $('overallStatus').textContent = String(overall).replaceAll('_',' ').toUpperCase();
  $('safetyState').textContent = String(overall).replaceAll('_', ' ');
  $('safetyCopy').textContent = answer.summary || 'Assessment unavailable.';

  const pct = Math.max(0, Math.min(100, Number(quality.completeness_percent || 0)));
  $('coverageValue').textContent = `${pct}%`;
  $('coverageBar').style.width = `${pct}%`;
  $('pfzValue').textContent = `${(result.pfz || []).length}`;
  $('hazardValue').textContent = `${(result.hazards || []).length}`;
  $('geoValue').textContent = `${(result.geofencing || []).filter(x => x?.inside).length}`;
  $('confidenceValue').textContent = assessment.confidence != null ? `${Math.round(Number(assessment.confidence) * 100)}%` : '—';
  renderSources(result);
  renderMap(result);
  renderTrace(result);
}

async function sendMessage(text, location = null) {
  const message = text.trim();
  if (!message) return;
  addMessage('user', message, new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}));
  renderTyping();
  $('latencyLabel').textContent = 'Working…';
  const t0 = performance.now();
  try {
    const r = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message, conversation_id: conversationId, location })
    });
    if (!r.ok) throw new Error(await r.text());
    const result = await r.json();
    conversationId = result.conversation_id || conversationId;
    localStorage.setItem('orca_conversation_id', conversationId);
    renderResult(result);
    $('messageInput').value = '';
    $('latencyLabel').textContent = `${Math.round(performance.now() - t0)} ms`;
    setStatus(true, 'Backend online');
  } catch (err) {
    addMessage('assistant', `I couldn't reach the ORCA backend.\n\n${err.message}`, 'Connection error');
    $('latencyLabel').textContent = 'Error';
    setStatus(false, 'Backend unavailable');
  } finally {
    removeTyping();
  }
}

function autoGrow(el){ el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 110) + 'px'; }

$('chatForm').addEventListener('submit', e => { e.preventDefault(); sendMessage($('messageInput').value); });
$('messageInput').addEventListener('input', e => autoGrow(e.target));
$('messageInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('chatForm').requestSubmit(); } });

document.querySelectorAll('.prompt-chip').forEach(btn => btn.addEventListener('click', () => sendMessage(btn.dataset.query)));

$('newSessionBtn').addEventListener('click', () => {
  conversationId = `conv_${crypto.randomUUID().slice(0, 10)}`;
  localStorage.setItem('orca_conversation_id', conversationId);
  $('conversationId').textContent = conversationId;
  $('chatStream').innerHTML = `<div class="empty-chat"><div class="wave-icon">≈</div><h3>New marine session</h3><p>Ask ORCA about a location, hazard, PFZ or sea condition.</p></div>`;
});

$('locateBtn').addEventListener('click', () => {
  if (!navigator.geolocation) return addMessage('assistant', 'Geolocation is not available in this browser.', 'Location');
  navigator.geolocation.getCurrentPosition(
    pos => {
      const loc = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, name: 'My location' };
      map.setView([loc.latitude, loc.longitude], 9);
      sendMessage('What are the current sea conditions at my location?', loc);
    },
    err => addMessage('assistant', `Location access failed: ${err.message}`, 'Location')
  );
});

$('themeBtn').addEventListener('click', () => document.body.classList.toggle('light-mode'));

initMap();
pingBackend();
setInterval(pingBackend, 15000);
$('conversationId').textContent = conversationId;
