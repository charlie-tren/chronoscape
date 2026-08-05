# Static-site spike

Proves the proposed post-Streamlit stack: **Python + Jinja2 -> static HTML**, no JS
toolchain, no server, free always-on hosting.

```bash
python spike/build.py            # build all countries
python spike/build.py taiwan     # build one
python -m http.server 8503 -d spike/dist
```

## What it demonstrates

- **Build is instant.** Three countries (388 events) in ~0.45s. 200 countries would
  still be seconds - nowhere near Vercel/Cloudflare's 45-min build ceiling.
- **The event list is server-rendered.** All 166 Taiwan events are real HTML in the
  page source, with a proper `<title>` and meta description. That is the SEO win
  Streamlit structurally cannot deliver (one indexable page, no DOM control).
- **The timeline is the EXISTING code.** `static/app.js` is `timeline_files/index.html`
  with the Streamlit component protocol deleted - no `Streamlit.setComponentValue`,
  no RENDER_EVENT, no iframe. Clicking a dot calls `select()` directly.
- **Interactions are instant** - filtering, selection and map sync are local state.
  No rerun, no round-trip, no cold start.
- **Real responsive layout** via CSS media queries at 1100px and 760px. `st.columns`
  has no breakpoint API (open request since 2022).
- **Map is MapLibre + OpenFreeMap**, which also fixes the CARTO licensing problem.

## Gotchas found while building it

- **MapLibre v6 is ESM-only** - it dropped the UMD build, so `<script src>` 404s on
  `dist/maplibre-gl.js`. Use `<script type="module">` + import `dist/maplibre-gl.mjs`.
  Still no build step; this is native browser ESM.
- **v6 has no default export.** Use `import * as maplibregl from '...'`.
- **OpenFreeMap sets `attribution: null`** on both sources, so the credit must be
  supplied via `customAttribution`. Configure it *inline* in the `Map` options -
  adding a second `AttributionControl` renders the attribution twice.
- Sprite warnings (`Image "circle-11" could not be loaded`) come from OpenFreeMap's
  own style and are harmless.

## Mobile

Both breakpoints (1100px and 760px) were confirmed parsed by the browser and
targeting the right selectors, and the 760px declarations were applied directly
to check the result: header stacks, chips wrap, filters go full-width one per
row, legend wraps, map drops to 340px, layout collapses to a single column.

Caveat on method: the automation viewport is pinned at 1280px regardless of
window size, so this was verified by applying the rules rather than by resizing.
Worth one look on a real phone before trusting it completely.

## Not done (it is a spike)

Accounts, share links, per-event URLs, sitemap, Cloudflare Pages deploy.
