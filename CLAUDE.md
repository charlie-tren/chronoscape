# Chronoscape - project context for Claude

Multi-country history timeline. **Static site**, built by `site/build.py`
(Python + Jinja2) from country data checked into `countries/<name>.json`. There is
**no live database** - Supabase was retired 2026-07-03 - and as of `83384d6` there
is **no Streamlit app either**; the migration is complete. Deployed via Cloudflare.

The build is two files: `site/build.py` and `site/validate.py`. `tools/` holds
one-off asset generators that are not part of the build.

## Tests - the gap flagged 07/08/2026 is CLOSED (14/08/2026)

`tests/` covers the pure functions and the validator. 39 tests, plain pytest, no
framework or mocking:

```bash
python -m pytest tests -q
```

They run in CI before the build, so a failure stops the deploy. They are also
mutation-checked: removing the zero-width guard, breaking the global dot ids,
disabling the `width_pct` sum check and removing the position clamp were each
verified to make the suite go red. If you add tests here, do the same - a test
that cannot fail is worse than none, because it buys false confidence.

Two behaviours worth knowing before you touch them:

- **`proportional_position` handles BC years** - negative inputs, ranges that
  straddle zero, and a zero-width range (Republic of Formosa is 1895 to 1895).
  It also clamps out-of-era events to the segment edge, which is what keeps
  the deliberate precursor placements on the strip.
- **`version()` has already shipped a production bug** on Cloudflare's shallow
  clone (fixed `b0a1c38`). All three branches are tested: full clone, shallow
  clone that can unshallow, and shallow clone that cannot and must date-stamp.

Adding a country? `countries/README.md` has the schema and the conventions.

## Conventions and gotchas

- Australian English, hyphens only (no en or em dashes) in anything rendered.
  **The one exception is an event's `source`**, which is a Wikipedia article slug
  and has to match the title exactly - dashes and diacritics included. It is a
  machine identifier, not prose; the reader only ever sees the word "Wikipedia".
- **Every `is_major` event needs a `source`** and the validator enforces it. The
  slug being well-formed is NOT the same as the article existing - check them
  against the Wikipedia API before committing (`countries/README.md` has the
  query). Of the first 290 written, eight were wrong: six missing articles and
  two disambiguation pages.
- **Do not set `is_major` by feel while writing a country.** It was done that way
  for Norway, Italy and Mexico and came out at 65%, 76% and 59% against a 35-45%
  target, each needing a correction pass. Build the list explicitly and assert
  the ratio - `tools`-side generators for those three do exactly that.
- **Never set `display` on a class that can also carry `hidden`.** The browser's
  `[hidden] { display: none }` is a bare attribute selector, so any class rule
  setting `display` outranks it and the element stays on screen with `hidden`
  set. This broke the detail panel on 17/08/2026: `.detail-empty` was given
  `display: flex` to centre the placeholder, which then painted over the real
  event panel. `style.css` now carries a global `[hidden] { display: none
  !important; }` guard - leave it there.
- Default branch is `master`, not `main`.
- **The site is served from `charlietrenorden.com/chronoscape/` and nowhere else**,
  by GitHub Pages, automatically on push. The old
  `chronoscape.charlietrenorden.com` subdomain 301s there and the Cloudflare
  project behind it holds nothing but a `_redirects` file. Never
  `wrangler pages deploy site/dist` to it - that puts a second canonical copy of
  the site online, which is the problem 20/08/2026 fixed.
- CI clones with `fetch-depth: 0` because `version()` reads git history and has
  already shipped a bug on a shallow clone.
- The header block in `TODO.md` is stale post-migration (still describes Streamlit
  Cloud and `db.py`). Fix it there if you are in the file.
