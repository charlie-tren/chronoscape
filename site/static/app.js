/* Chronoscape static site.
 *
 * The timeline below is the EXISTING timeline_files/index.html logic with the
 * Streamlit component protocol removed - no Streamlit.setComponentValue, no
 * RENDER_EVENT listener, no iframe. Selecting a dot now calls select() directly
 * instead of round-tripping to a Python server.
 */

// MapLibre v6 dropped the UMD build and is ESM-only, so it is imported here
// rather than loaded via a plain <script src>. This is native browser ESM -
// no bundler, no build step. Note v6 exposes NAMED exports (Map,
// AttributionControl, ...) with no default export, hence the namespace import.
import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.1.0/dist/maplibre-gl.mjs';

const DATA = JSON.parse(document.getElementById('payload').textContent);
const EVENTS = new Map(DATA.events.map(e => [e.id, e]));

let selectedId = null;
let visible = new Set(DATA.events.map(e => e.id));

/* ---------------- Timeline (ported from timeline_files/index.html) --------- */

function buildTimeline() {
  const ribbon = document.getElementById('tl-ribbon');
  const height = 160;
  ribbon.innerHTML = '';
  ribbon.style.width = DATA.totalWidth + 'px';
  ribbon.style.height = (height - 20) + 'px';
  const barTop = Math.floor((height - 20) * 0.5);

  DATA.segments.forEach(seg => {
    const segWidth = Math.floor(DATA.totalWidth * seg.width_pct / 100);
    const era = document.createElement('div');
    era.className = 'tl-era';
    era.style.width = segWidth + 'px';
    era.style.height = '100%';

    const bg = document.createElement('div');
    bg.className = 'tl-era-bg';
    bg.style.background = seg.color + '06';
    bg.style.borderLeft = '1px solid ' + seg.color + '40';
    era.appendChild(bg);

    const bar = document.createElement('div');
    bar.className = 'tl-era-bar';
    bar.style.top = barTop + 'px';
    bar.style.background = seg.color + '30';
    era.appendChild(bar);

    const name = document.createElement('div');
    name.className = 'tl-era-name';
    name.style.color = seg.color;
    name.textContent = seg.era_label;
    era.appendChild(name);

    const dateLabel = document.createElement('div');
    dateLabel.className = 'tl-date-label';
    dateLabel.style.color = seg.color + 'aa';
    dateLabel.textContent = seg.date_label;
    era.appendChild(dateLabel);

    const dots = document.createElement('div');
    dots.className = 'tl-era-dots';

    seg.dots.forEach(dot => {
      const d = document.createElement('button');
      d.className = 'tl-dot';
      d.dataset.id = dot.id;
      d.type = 'button';
      d.setAttribute('role', 'option');
      d.setAttribute('aria-label', dot.tooltip);
      d.setAttribute('aria-selected', 'false');
      d.tabIndex = -1;              // roving tabindex; container holds focus
      d.title = dot.tooltip;

      let size = dot.major ? 16 : 8;
      const color = dot.major ? '#4fc3f7' : seg.color;
      let opacity = dot.major ? '1' : '0.6';
      let glow = dot.major ? 'box-shadow:0 0 10px #4fc3f7;' : '';
      d.style.cssText =
        `left:${dot.left}%;width:${size}px;height:${size}px;background:${color};opacity:${opacity};${glow}`;
      dots.appendChild(d);
    });

    era.appendChild(dots);
    ribbon.appendChild(era);
  });

  wireTimeline();
}

function wireTimeline() {
  const container = document.getElementById('tl-container');
  const tooltip = document.getElementById('tl-tooltip');
  let isDown = false, startX = 0, scrollLeft = 0, dragged = false;

  container.addEventListener('pointerdown', e => {
    if (e.target.classList.contains('tl-dot')) return;
    isDown = true; dragged = false;
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });
  container.addEventListener('pointerleave', () => { isDown = false; });
  container.addEventListener('pointerup', () => { isDown = false; });
  container.addEventListener('pointermove', e => {
    if (!isDown) return;
    e.preventDefault();
    dragged = true;
    container.scrollLeft = scrollLeft - ((e.pageX - container.offsetLeft) - startX) * 1.5;
  });
  container.addEventListener('wheel', e => {
    if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;
    e.preventDefault();
    container.scrollLeft += e.deltaY * 2;
  }, { passive: false });

  container.querySelectorAll('.tl-dot').forEach(dot => {
    dot.addEventListener('mouseenter', () => {
      tooltip.textContent = dot.title;
      tooltip.style.display = 'block';
    });
    dot.addEventListener('mousemove', e => {
      tooltip.style.left = (e.clientX + 14) + 'px';
      tooltip.style.top = (e.clientY - 35) + 'px';
    });
    dot.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
    dot.addEventListener('click', e => {
      e.stopPropagation();
      if (dragged) return;                  // a drag is not a click
      select(parseInt(dot.dataset.id, 10)); // was Streamlit.setComponentValue
    });
  });

  // Keyboard: arrows walk the visible dots, and the browser scrolls them
  // into view for free, which pans the strip.
  container.addEventListener('keydown', e => {
    const dots = [...container.querySelectorAll('.tl-dot')].filter(d => d.style.display !== 'none');
    if (!dots.length) return;
    let i = dots.findIndex(d => parseInt(d.dataset.id, 10) === selectedId);
    if (e.key === 'ArrowRight') i = Math.min(dots.length - 1, i + 1);
    else if (e.key === 'ArrowLeft') i = Math.max(0, i < 0 ? 0 : i - 1);
    else if (e.key === 'Home') i = 0;
    else if (e.key === 'End') i = dots.length - 1;
    else return;
    e.preventDefault();
    const dot = dots[i];
    select(parseInt(dot.dataset.id, 10));
    dot.scrollIntoView({ block: 'nearest', inline: 'center' });
  });
}

/* ---------------- Map (MapLibre + OpenFreeMap) ----------------------------- */

let map = null;

function buildMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.openfreemap.org/styles/dark',
    center: DATA.center,
    zoom: DATA.zoom,
    // Do NOT add customAttribution here. The dark style's `openmaptiles` source
    // carries no inline attribution - it points at tiles.openfreemap.org/planet, and
    // MapLibre fetches THAT TileJSON asynchronously, which does supply the OpenFreeMap /
    // OpenMapTiles / OpenStreetMap credit. An earlier attempt concluded the control
    // rendered empty without customAttribution; it was reading the DOM before the
    // TileJSON resolved. Adding it back simply prints the same string twice, which is
    // what the control showed on 07/08/2026. Crediting OpenStreetMap is a licence
    // condition, so if this ever does render empty, fix the source rather than
    // concatenating a second copy.
    attributionControl: { compact: true }
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

  map.on('load', () => {
    map.addSource('events', { type: 'geojson', data: DATA.geojson });
    // One GPU-drawn layer for every marker, not N DOM nodes.
    map.addLayer({
      id: 'events',
      type: 'circle',
      source: 'events',
      paint: {
        'circle-radius': ['case', ['get', 'major'], 7, 5],
        'circle-color': ['get', 'color'],
        'circle-opacity': 0.85,
        'circle-stroke-width': ['case', ['==', ['get', 'id'], ['literal', -1]], 2, 0.5],
        'circle-stroke-color': '#0c0f16'
      }
    });
    map.addLayer({
      id: 'events-selected',
      type: 'circle',
      source: 'events',
      filter: ['==', ['get', 'id'], -1],
      paint: {
        'circle-radius': 11,
        'circle-color': '#4fc3f7',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff'
      }
    });

    map.on('click', 'events', e => {
      if (e.features && e.features.length) select(e.features[0].properties.id);
    });
    map.on('mouseenter', 'events', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'events', () => { map.getCanvas().style.cursor = ''; });
    applyFilters();
  });
}

/* ---------------- Selection + filtering ------------------------------------ */

function select(id, opts = {}) {
  selectedId = id;
  const ev = EVENTS.get(id);
  if (!ev) return;

  // Deep link. replaceState rather than pushState so clicking through 166
  // events doesn't bury the back button.
  if (!opts.fromHash) {
    history.replaceState(null, '', '#event-' + id);
  }

  document.getElementById('detail-empty').hidden = true;
  document.getElementById('detail-body').hidden = false;
  document.getElementById('detail-date').textContent = ev.date;
  document.getElementById('detail-title').textContent = ev.title;
  document.getElementById('detail-desc').textContent = ev.description;

  const tags = document.getElementById('detail-tags');
  tags.innerHTML = '';
  const eraTag = document.createElement('span');
  eraTag.className = 'era-tag';
  eraTag.style.background = ev.eraColor + '35';
  eraTag.style.color = ev.eraColor;
  eraTag.textContent = ev.eraShort;
  tags.appendChild(eraTag);
  ev.categories.forEach(c => {
    const t = document.createElement('span');
    t.className = 'cat-tag';
    t.textContent = c;
    tags.appendChild(t);
  });
  if (ev.major) {
    const b = document.createElement('span');
    b.className = 'major-badge';
    b.textContent = 'PIVOTAL EVENT';
    tags.appendChild(b);
  }

  document.querySelectorAll('.event-card').forEach(c => {
    c.classList.toggle('selected', parseInt(c.dataset.id, 10) === id);
  });
  document.querySelectorAll('.tl-dot').forEach(d => {
    const on = parseInt(d.dataset.id, 10) === id;
    d.classList.toggle('tl-dot-selected', on);
    d.setAttribute('aria-selected', on ? 'true' : 'false');
  });

  const card = document.querySelector(`.event-card[data-id="${id}"]`);
  if (card) card.scrollIntoView({ block: 'nearest' });

  if (map && map.getLayer('events-selected')) {
    map.setFilter('events-selected', ['==', ['get', 'id'], id]);
    if (ev.lat != null && ev.lng != null) {
      map.easeTo({ center: [ev.lng, ev.lat], zoom: Math.max(map.getZoom(), 7), duration: 500 });
    }
  }
}

function clearSelection() {
  selectedId = null;
  if (location.hash) history.replaceState(null, '', location.pathname + location.search);
  document.getElementById('detail-empty').hidden = false;
  document.getElementById('detail-body').hidden = true;
  document.querySelectorAll('.event-card').forEach(c => c.classList.remove('selected'));
  document.querySelectorAll('.tl-dot').forEach(d => {
    d.classList.remove('tl-dot-selected');
    d.setAttribute('aria-selected', 'false');
  });
  if (map && map.getLayer('events-selected')) {
    map.setFilter('events-selected', ['==', ['get', 'id'], -1]);
    map.easeTo({ center: DATA.center, zoom: DATA.zoom, duration: 500 });
  }
}

function applyFilters() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const era = document.getElementById('era-filter').value;
  const cat = document.getElementById('cat-filter').value;
  const keyOnly = document.getElementById('key-only').checked;

  visible = new Set();
  DATA.events.forEach(ev => {
    if (era && ev.era !== era) return;
    if (cat && !ev.categories.includes(cat)) return;
    if (keyOnly && !ev.major) return;
    if (q && !(ev.title.toLowerCase().includes(q) || ev.description.toLowerCase().includes(q))) return;
    visible.add(ev.id);
  });

  document.querySelectorAll('.event-item').forEach(li => {
    li.style.display = visible.has(parseInt(li.dataset.id, 10)) ? '' : 'none';
  });
  document.querySelectorAll('.tl-dot').forEach(d => {
    d.style.display = visible.has(parseInt(d.dataset.id, 10)) ? '' : 'none';
  });
  document.getElementById('event-count').textContent = visible.size;

  if (map && map.getLayer('events')) {
    map.setFilter('events', ['in', ['get', 'id'], ['literal', [...visible]]]);
  }
}

/* ---------------- Wiring --------------------------------------------------- */

document.querySelectorAll('.event-card').forEach(card => {
  card.addEventListener('click', () => select(parseInt(card.dataset.id, 10)));
});
['search', 'era-filter', 'cat-filter', 'key-only'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener(el.tagName === 'INPUT' && el.type === 'search' ? 'input' : 'change', applyFilters);
});
document.getElementById('clear-selection').addEventListener('click', clearSelection);

// Deep link support: /taiwan/#event-42 opens with that event selected.
function selectFromHash(opts) {
  const m = /^#event-(\d+)$/.exec(location.hash);
  if (!m) return false;
  const id = parseInt(m[1], 10);
  if (!EVENTS.has(id)) return false;
  select(id, opts);
  return true;
}

window.addEventListener('hashchange', () => {
  if (!selectFromHash({ fromHash: true })) clearSelection();
});

buildTimeline();
buildMap();
applyFilters();
selectFromHash({ fromHash: true });
