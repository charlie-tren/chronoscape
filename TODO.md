# TODO - Chronoscape (multi-country history timeline)

Last updated: 2026-07-03
Current branch: `master` (GitHub default branch is also `master`; Streamlit Cloud deploys from master)
GitHub: `charlie-tren/chronoscape`
Deployed: `https://chronoscape.streamlit.app/` (chip-only Taiwan + Iceland; data in `countries/*.json`)

Architecture: **no live database.** Country data is checked into `countries/<name>.json`. `db.py` is a JSON loader that keeps the old query surface. Supabase was retired 2026-07-03 - free-tier project quota was needed for `rochford-news-monitor`, and Chronoscape's data is small and read-only.

---

## Outstanding

### Stack investigation: migrate to Next.js + Vercel before scaling up (2026-07-03)

Chronoscape is heading toward 50+ countries, on-demand Anthropic generation, and user-facing features (search across countries, saved views, share links). Streamlit is fine for the current 2-country read-only shape but doesn't scale where the project is going: CSS scoping fights, no server-side API surface, no real auth story, mobile layout limits.

**Recommended target: Next.js on Vercel** (same pattern as `macro-signals-web`, already live). Fit at scale:
- **Content** - `countries/*.json` files -> SSG per country, ISR for freshness. One page per country (`/taiwan`, `/iceland`, ...). Migrates to a DB-backed source when JSON stops scaling (probably ~50-100 countries as git-committed content).
- **On-demand generation** - API routes on Vercel + a queue for the Anthropic pipeline. Write path needs a real DB back (see below).
- **User features** - NextAuth or Clerk for accounts, saved views, share links. Standard patterns.
- **Perf** - edge caching, static shells, streaming. Handles a traffic spike.
- **Ecosystem** - largest React community, deepest AI-code-gen coverage, react-leaflet for the map, D3 or a lightweight custom SVG for the timeline.

Rejected alternatives (documented so the decision doesn't get relitigated):
- **Astro** - great for read-only static, but loses to Next as dynamic features (generation API, auth, DB queries) enter the picture.
- **Vanilla HTML + D3 + Leaflet** - falls off past a few countries; no component model.
- **Observable Framework** - purpose-built for data storytelling but not for multi-page apps with auth.
- **SvelteKit** - technically a peer of Next but smaller ecosystem and Charlie has no Svelte experience.
- **T3 stack (Next + tRPC + Prisma + NextAuth + Tailwind)** - worth considering if the answer to "will there be user accounts + typed API calls" is a firm yes. Otherwise plain Next is enough.

**Decisions to make before scaffolding:**

1. **DB choice** (relevant once on-demand generation is back or content exceeds ~50 countries):
   - **Neon** - Postgres, no project quota, generous free tier, integrates cleanly with Vercel. Recommended.
   - **Vercel Postgres** - Neon under the hood but billed through Vercel. Simpler auth, less portable.
   - **Supabase** - fine, but the free-tier project quota drama that killed the last go is still there. Only pick if you specifically want their auth / storage / realtime.
   - **Turso (libSQL)** - SQLite-based, edge-native, generous free tier. Interesting if generation is done offline and reads dominate.
2. **Content model at scale** - JSON files in git stop being a good source of truth past ~50-100 countries (commits become noisy, review flow gets in the way). Options: (a) keep JSON but generate + PR them automatically, (b) move to a DB and use JSON only as a seed / export format.
3. **Auth timing** - do you want auth in v3, or defer? Adding it later is fine; deferring means the first Next release is public + read-only, same UX as today.

**Migration checklist:**
- [ ] Fresh `create-next-app --typescript --tailwind` in `~/dev/chronoscape-web` (per [[windows-node-scaffold-gotchas]] - OFF OneDrive; a11y note: `.claude/mcp.json` from Macro Signals is a good starting point).
- [ ] Copy `countries/*.json` across as-is (they're the same shape Next will consume).
- [ ] Set up `app/page.tsx` (landing / chip picker), `app/[country]/page.tsx` (dynamic country routes), `generateStaticParams` for SSG.
- [ ] Port the timeline JS to a React SVG component. Swimlane + dots + click handlers - mostly framework-agnostic. Consider D3 for tick scales, but full D3 is overkill; hand-rolled SVG is fine at this scale.
- [ ] Swap folium for `react-leaflet`. Direct primitive - folium was only a Streamlit-friendly workaround.
- [ ] Reuse the existing dark theme + Inter font + accent cyan. Tailwind can absorb the design tokens from `styles.py DARK_CSS`.
- [ ] Confirm parity on a single country (Taiwan) locally, then a second (Iceland), then flip Vercel to point at the new repo.
- [ ] Keep the Streamlit deploy live during the swap; move DNS / subdomain to Vercel after a week of soak.
- [ ] Once retired, archive the Streamlit repo (or leave master pinned - the JSON files stay useful as a data seed either way).

**When to trigger:** Before the next substantive feature push. Doing more work in the Streamlit shell now creates rework at migration time. If a new country is the next task, migrate first, then add the country in Next.

### If Anthropic-generated countries come back

The old on-demand Wikipedia -> Claude pipeline (`pipeline.py`, `worker.py`) was deleted along with the Supabase backend. To bring it back:

- [ ] Rewrite `pipeline.py` to output a `countries/<name>.json` file instead of writing to Supabase (same schema).
- [ ] Add either a "generate" button in the app that calls the pipeline synchronously and commits/pushes the JSON, OR a local-only CLI (`python pipeline.py Japan`) that Charlie runs by hand and then commits.
- [ ] Add `anthropic` back to `requirements.txt`.
- [ ] Set `ANTHROPIC_API_KEY` in `.env` locally.

For a side project this "generate locally, commit, push" flow is probably fine - the deployed app never needs write access. The Supabase `generating`/`failed`/`retry` UI states and the failed-state retry button are gone with the DB.

### Cleanup on Streamlit Cloud

- [ ] Delete the `SUPABASE_URL` and `SUPABASE_KEY` entries from Streamlit Cloud Secrets - they're no longer read by the app.

---

## Done

### JSON migration (2026-07-03)
- Free-tier Supabase quota was needed for `rochford-news-monitor` (created 20/05/2026), so the History Timeline project was paused. Rather than shuffle quotas indefinitely, moved to flat JSON files.
- Dumped Supabase state -> `countries/taiwan.json` (166 events, 10 eras) + moved `iceland_data.json` -> `countries/iceland.json` (92 events, 10 eras).
- Rewrote `db.py` as a JSON loader (~90 lines, was ~200 lines of Supabase queries). Same public surface (`list_countries`, `load_country_data`) so `app.py` needed only a small edit to drop the try/except DB fallback and remove the generating/failed/retry branches.
- Simplified `app.py`: no worker recovery on startup, no `_build_taiwan_fallback_eras`. Charlie's June UI redesign (Inter font, gradient theme, scoped chip pills, clickable event cards) is preserved.
- `requirements.txt` stripped to `streamlit`, `folium`, `streamlit-folium` (removed supabase, python-dotenv, anthropic).
- Deleted: `pipeline.py`, `worker.py`, `seed_country.py`, `seed_taiwan.py`, `.github/workflows/keep-alive.yml`. Note: the Supabase project (`xbhhdpcbrsgmactfuxlq`) is still on the account but paused - safe to fully delete when Charlie's ready.
- Streamlit Cloud Secrets `SUPABASE_URL` / `SUPABASE_KEY` still set but now unused (see Outstanding).

### UI redesign + bug fixes + DB restore + keep-alive fix (2026-06-21)
- **Sleeker UI** (`styles.py`, `app.py`): Inter font, deeper gradient theme, rounded filter inputs, scoped chip pills (chips no longer wrap), polished detail panel + welcome/loading cards. Live as v2.16.
- **Event list rows are now single clickable card buttons** (dim date over bold title, star for key events, per-era colour stripe down the left edge). FIXES the "card click doesn't select" bug - the whole card selects; removed the redundant "Select event" button.
- **Verified via Claude in Chrome** (local run): chips, event-card click -> detail panel, timeline-dot click, clear selection, detail panel rendering. Map markers respond to hover/tooltip (click path unchanged from prior verification).
- **DB had auto-paused** (down since ~late May) -> restored via Supabase MCP `restore_project` + `NOTIFY pgrst, 'reload schema'` + a Streamlit Cloud reboot (auto-deploy lagged ~10 min).
- **keep-alive cron changed from every-6-days to DAILY** (`0 3 * * *`) - 6 days of slack vs the 7-day pause window. Root cause of the pause: the 6-day cadence had <1 day of slack and GitHub cron delays pushed the gap >7 days. Manual `workflow_dispatch` run succeeded (first green since 2026-05-25). Edited via the GitHub web editor (local `gh` not logged in; tokens lack `workflow` scope).

### Phase 1 - Database Foundation (2026-04-14)
- Created Supabase project `xbhhdpcbrsgmactfuxlq` (us-east-1, free tier).
- Created 4 tables with indexes + FK cascades: countries, eras, events, generation_jobs.
- Built `db.py` with full query wrapper.
- Seeded Taiwan data from existing markdown (166 events, 10 eras, status=ready, centre 23.7/121.0).

### Phase 2 - Code generalisation + verification (2026-04-22, verified 2026-05-19)
- Stripped Taiwan-specific data out of `event_data.py`, `styles.py`, `timeline_component.py`, `map_component.py`.
- Added runtime-config pattern: `set_era_config(eras)` populates `_era_color_map` / `_era_short_map`.
- 15-colour `ERA_PALETTE` for dynamic assignment.
- Universal category list (added Social, Scientific, Religious; kept Aboriginal as alias to Indigenous).
- `render_timeline()` now takes `eras_config` param, `render_map()` takes `country_config`.
- `app.py` rewritten with country search bar at top, dynamic header + filters + colour key, loading/error state UI.
- **Verified end-to-end (2026-05-19)** via Claude in Chrome: Taiwan loads from DB (166 events, 10 eras, all renderers work), Iceland loads from DB (92 events, 10 eras), country-switch via search bar works, event selection via list works, detail panel populates, map markers render with tooltip-encoded IDs.

### Iceland seeded (2026-05-19)
- Hand-extracted 92 events / 10 eras from the Wikipedia History of Iceland article (Charlie pasted the text in chat).
- Pre-Settlement -> Settlement Age (874-930) -> Commonwealth (930-1262) -> Norwegian Rule -> Kalmar Union -> Danish Rule and Trade Monopoly -> Path to Independence -> Kingdom of Iceland -> Cold War Republic -> Modern Republic.
- 32 major events, 25 with map coordinates, centre 64.96 / -19.02, zoom 6.
- Created `iceland_data.json` (raw structured data) and generic `seed_country.py` (loads a JSON of this shape and inserts into Supabase) - the latter is the storage-layer prototype that Phase 4 `pipeline.py` will reuse.

### Phase 4 - Data pipeline shipped (2026-05-19)
- `pipeline.py` with `fetch_wikipedia()` (4-5 articles, 1 req/sec, 80k char cap), `extract_with_claude()` (claude-sonnet-4-6, structured output via `output_config.format` with full JSON schema enforcement, thinking disabled, max_tokens 16000), `store_results()` (reuses save_eras / save_events from db.py), `run_pipeline()` orchestrator with full job tracking in `generation_jobs` (input_tokens, output_tokens, cost_usd, wiki_pages, error_message).
- `worker.py` with `generate_in_background()` (threading.Thread daemon, dedupe via `_active_threads` so duplicate clicks don't spawn parallel workers), `recover_stuck_jobs()` (resets `status='generating'` rows older than 10min to `'failed'` so UI offers retry).
- `app.py` calls `recover_stuck_jobs()` once per Streamlit process on first load (gated by session_state flag, doesn't block on failure).
- Per-country cost ~$0.25 (Sonnet 4.6 pricing). 50-country monthly refresh ~$13.
- **Untested end-to-end** because ANTHROPIC_API_KEY is still empty in `.env` - that's the only blocker.

### Hardening (2026-05-19)
- **RLS enabled** on all 4 tables. anon + authenticated roles get SELECT only; service_role bypasses for writes. Future seeds and `pipeline.py` writes need the service_role key locally.
- **db.py updated** to prefer `SUPABASE_SERVICE_ROLE_KEY` if set, else fall back to `SUPABASE_KEY`. No app code changes required.
- **Service role key added to local `.env`** as `SUPABASE_SERVICE_ROLE_KEY`. Verified writes work.
- **GitHub Actions keep-alive cron** added (`.github/workflows/keep-alive.yml`) - hits Supabase REST API every 6 days to stop free-tier 7-day auto-pause.
- **GitHub repo secrets** `SUPABASE_URL` and `SUPABASE_ANON_KEY` added via `gh secret set` so the cron actually works.
- One-off discovery: the project had auto-paused. Restore took ~2 minutes via `restore_project`. PostgREST schema cache had to be reloaded post-restore (`NOTIFY pgrst, 'reload schema';`) before writes worked again. Worth noting for future restores.

### Deploy + Rename (2026-05-19)
- **Merged `multi-country-refactor` -> `master` -> pushed to GitHub `master`.** Streamlit Cloud auto-deploys from master. (Originally pushed to `main`; the `main` branch was deleted 19/05/2026 once we realised Streamlit Cloud was wired to master.)
- **Repo renamed**: `taiwan-history-timeline` -> `country-timelines` -> `chronoscape` (final). Local remote updated. GitHub redirects old URLs.
- **Repo description** updated to reflect multi-country scope.

### Infrastructure
- `.env` file for local secrets (gitignored).
- `.gitignore` updated (.env, __pycache__, .claude).
- `requirements.txt` updated: +supabase, +python-dotenv, +anthropic, +folium, +streamlit-folium, +branca.
- `PLAN.md` saved in project root.
