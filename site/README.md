# Chronoscape static site

**Python + Jinja2 -> static HTML.** No JS toolchain, no server, no database.
Free always-on hosting on Cloudflare Pages.

```bash
pip install -r ../requirements-build.txt
python site/build.py            # build all countries
python site/build.py taiwan     # build one (still validates all)
python site/validate.py         # check the data without building

python -m http.server 8503 -d site/dist
```

## How it works

`countries/<slug>.json` -> validated -> one static page per country at `/<slug>/`.

- The **event list is rendered server-side** - real HTML in the source, with a
  title, meta description, canonical and Open Graph tags. That is the SEO the
  Streamlit version structurally could not do (one indexable page, no DOM control).
- The **timeline** is the original `timeline_files/index.html` with the Streamlit
  component protocol removed. Clicking a dot calls `select()` directly instead of
  round-tripping to Python. No iframe.
- The **map** is MapLibre + OpenFreeMap, markers as a single GeoJSON circle layer
  rather than N DOM nodes. This also resolves the CARTO licensing problem.
- **Interactions are local state** - filtering, selection and map sync never touch
  a server.
- **Deep links**: `/taiwan/#event-80` opens with that event selected. Uses
  `replaceState`, so clicking through 166 events doesn't bury the back button.

**The country page is the indexable unit, not the event.** One page per event would
be ~26,000 URLs at 200 countries, for a paragraph each. Events get hash links.

## Validation

`validate.py` runs as a gate in `build.py` - bad data fails the build rather than
shipping quietly. It splits **errors** (fail) from **warnings** (report and carry on):

- Errors: missing required fields, an `era_name` matching no era, unknown category,
  half-set or out-of-range coordinates, duplicate titles, era widths not summing to
  100, eras out of order.
- Warnings: an event whose `sort_year` falls outside its era, and an excessive
  share of `is_major`.

The era-window check is deliberately only a warning, because placing a precursor
event in the era it belongs to *narratively* is a legitimate editorial choice -
Iceland's pre-874 voyages sit in the Settlement Age, and Taiwan's events about
Koxinga's father sit in the Koxinga era. Six such warnings are expected today.

Note `sort_year` carries a fractional part to order events within a year (1944.4 is
May 1944), so the era check compares whole years.

## Deploying (Cloudflare Pages)

Cloudflare's build image ships Python 3.13, so this builds natively - no GitHub
Actions workflow file needed.

| Setting | Value |
|---|---|
| Build command | `pip install -r requirements-build.txt && python site/build.py` |
| Output directory | `site/dist` |
| Python version | pinned by `.python-version` |

`SITE_URL` overrides the canonical origin for preview builds; it defaults to
`https://chronoscape.charlietrenorden.com`.

## Gotchas worth keeping

- **MapLibre v6 is ESM-only** - no UMD build, so `dist/maplibre-gl.js` 404s. Use
  `<script type="module">` with `dist/maplibre-gl.mjs`. Native browser ESM, still
  no build step.
- **v6 has no default export** - `import * as maplibregl from '...'`.
- **OpenFreeMap sets `attribution: null`** on both sources, so the credit comes from
  `customAttribution`, configured *inline* in the `Map` options. Adding a second
  `AttributionControl` renders it twice.
- Sprite warnings (`Image "circle-11" could not be loaded`) come from OpenFreeMap's
  own style and are harmless.
- Stop the local `http.server` before renaming the directory - Windows keeps a lock
  on it and `git mv` fails with "Permission denied".

## Mobile

Breakpoints at 1100px and 760px. Verified by applying the 760px declarations
directly: header stacks, chips wrap, filters go full-width one per row, legend
wraps, map drops to 340px, single column. Caveat: the automation viewport is pinned
at 1280px whatever the window is set to, so this was checked by applying the rules
rather than a genuine resize. Worth one look on a real phone.

## Not done yet

`og:image` (needs an actual image per country), a real favicon rather than an
emoji data URI, and the Cloudflare Pages project itself.
