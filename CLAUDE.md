# Chronoscape - project context for Claude

Multi-country history timeline. **Static site**, built by `site/build.py`
(Python + Jinja2) from country data checked into `countries/<name>.json`. There is
**no live database** - Supabase was retired 2026-07-03 - and as of `83384d6` there
is **no Streamlit app either**; the migration is complete. Deployed via Cloudflare.

The entire Python surface is two files: `site/build.py` and `site/validate.py`.

## Test coverage - KNOWN GAP (flagged 07/08/2026, estate-wide test audit)

**No test suite.** It is partly guarded - `validate.py` runs from `build.py` before
anything renders, so a malformed country fails the build rather than shipping. That
covers the data. Nothing covers the code.

Post-migration this is a *small* gap, which is the argument for closing it rather
than deferring it again: five pure functions and a validator, no framework, no
mocking, no network.

**If you are changing `build_segments`, `proportional_position`, `match_era` or
`validate`, add tests for what you touch before you finish.** Two specifics worth
knowing:

- **`proportional_position` handles BC years**, so it takes negative inputs and a
  range that can be zero-width. Those are the cases that break it, and they are
  the ones a happy-path test misses.
- **`version()` has already shipped a production bug** on Cloudflare's shallow
  clone (fixed `b0a1c38`). If you touch it, test the shallow-repo branch - that
  is the path that actually broke.

See `TODO.md` for the tracked item.

## Conventions and gotchas

- Australian English, hyphens only (no en or em dashes) in anything rendered.
- Default branch is `master`, not `main`.
- Cloudflare builds are **shallow clones** - any code reading git history must
  handle that.
- `charlietrenorden.com/chronoscape` is a static redirect only.
- The header block in `TODO.md` is stale post-migration (still describes Streamlit
  Cloud and `db.py`). Fix it there if you are in the file.
