# TODO - Taiwan Timeline (Multi-Country Refactor)

Last updated: 2026-05-19
Current branch: `multi-country-refactor`
Deployed (Streamlit Cloud): still on old single-country `master` / `main` code

---

## Outstanding

### Manual one-off (do once, then forget)

- [ ] **Grab Supabase service_role key** from https://supabase.com/dashboard/project/xbhhdpcbrsgmactfuxlq/settings/api-keys, add to local `.env` as `SUPABASE_SERVICE_ROLE_KEY=eyJ...`. Required for `seed_country.py` and future `pipeline.py` to write to the DB now that RLS is on. Existing `SUPABASE_KEY` (anon) stays put for read-only fallback. **Never commit this key** - service_role bypasses RLS entirely.
- [ ] **Add GitHub repo secrets** at https://github.com/charlierochfordgroup/country-timelines/settings/secrets/actions for the keep-alive cron: `SUPABASE_URL` and `SUPABASE_ANON_KEY` (the anon key only - the cron just needs to ping a read endpoint).

### Phase 2 verification (blocker for everything else)

- [ ] **End-to-end visual test of multi-country app shell.** Server crashed on every attempt in last session (port conflicts, background bash lifecycle). Start fresh on a clean port and click through:
  - Type "Taiwan" in the country search box -> should load from Supabase (166 events, 10 eras) identically to how the old markdown version rendered
  - Type "Iceland" -> should switch to Iceland's 92 events / 10 eras / centre 64.96 / -19.02 / zoom 6. Confirms multi-country switching actually works.
  - Verify timeline, colour key, event list, map, detail panel all work
  - Verify filters (search, era, category, key-events toggle) all work
  - Verify "Clear selection" button still works
  - Check `get_era_color()` / `get_era_short()` lookups work via `set_era_config()` (runtime populated, not hardcoded)
- [ ] **Debug any Phase 2 bugs** surfaced by the test above. Likely suspects: `_match_era` fuzzy logic, styles fallback when no runtime config set, coord None handling.

### Phase 3 - Multi-country app shell polish

- [ ] Loading state UI (currently just `st.info + sleep(5) + st.rerun()`) - make it nicer with a progress indicator / stage description.
- [ ] Error state UI with retry button - test the failed-generation path works.
- [ ] Empty state / welcome screen on first load (already in app.py, but visually polish).
- [ ] Country autocomplete from existing DB entries (`list_countries()` already in db.py, just wire it up).

### Phase 4 - Data pipeline (not started)

- [ ] **Add `ANTHROPIC_API_KEY` to `.env`.** Currently empty. Needed before any of the below will work.
- [ ] Write `pipeline.py`:
  - `fetch_wikipedia(country_name)` - pulls 4-5 articles ("History of X", "X", "Timeline of X history", auto-discovered 1-2 long sub-articles). Rate limit 1 req/sec. Truncate combined to 80k chars.
  - `extract_with_claude(country_name, wiki_text)` - Claude Sonnet, structured JSON prompt. Target: 80-200 events, 5-15 eras, 10-25 major events, lat/lng inline. Universal categories.
  - `store_results(country_id, extraction)` - delete old eras/events for country, insert new ones. Log-scaled `width_pct = log10(year_span + 1)` with 5% minimum. Assign era colours from palette.
  - `run_pipeline(country_name)` - orchestrator with error handling + status updates.
- [ ] Write `worker.py`:
  - `generate_in_background(country_name)` - `threading.Thread(daemon=True)` running `run_pipeline`.
  - Recovery: on app startup, re-queue any country stuck in `generating` for >10 min.
- [ ] End-to-end test: type "Japan", wait 30-60s, verify timeline renders.

### Phase 5 - Polish

- [ ] Stale-data refresh logic: if `refreshed_at` > 14 days, serve stale + queue background refresh.
- [ ] Cost tracking: populate `generation_jobs.input_tokens`, `output_tokens`, `cost_usd` after each pipeline run.
- [ ] Feature flag: only refresh countries viewed in the past month to cap monthly cost.

### Deployment

- [ ] Add Streamlit Cloud Secrets (TOML format): `SUPABASE_URL`, `SUPABASE_KEY` (anon - reads only), `ANTHROPIC_API_KEY`. **Do NOT put the service_role key in Streamlit Cloud Secrets** until you've decided whether the worker stays in-process or moves out-of-band - see Phase 4 note.
- [ ] Merge `multi-country-refactor` -> `master` -> push to `main` on GitHub only AFTER full Phase 2 test passes.
- [ ] Consider renaming repo `country-timelines` -> `history-timeline` when multi-country goes live.
- [ ] Tag v2.0 release.

### Phase 4 architectural decision (when you start the pipeline)

The deployed Streamlit Cloud app currently uses the anon key (reads only - safe). When Phase 4's worker.py lands, writes are needed to create new countries and seed extracted data. Two paths:
- **Option A**: put `SUPABASE_SERVICE_ROLE_KEY` in Streamlit Cloud Secrets and let the in-process worker write directly. Simple but the key sits on a hosted service.
- **Option B (cleaner)**: move the worker out-of-band - e.g. a GitHub Actions workflow triggered by polling `countries.status='generating'` rows. Streamlit Cloud keeps anon-only.
- Decide before merging Phase 4 to main.

---

## Done

### Phase 1 - Database Foundation (2026-04-14)
- Created Supabase project `xbhhdpcbrsgmactfuxlq` (us-east-1, free tier).
- Created 4 tables with indexes + FK cascades: countries, eras, events, generation_jobs.
- Built `db.py` with full query wrapper.
- Seeded Taiwan data from existing markdown (166 events, 10 eras, status=ready, center 23.7/121.0).
- Verified `load_country_data('Taiwan')` returns valid data (166 events, 10 eras, 21 major, 45 with coords).

### Phase 2 - Code generalisation (code only, not tested)
- Stripped Taiwan-specific data out of `event_data.py`, `styles.py`, `timeline_component.py`, `map_component.py`.
- Added runtime-config pattern: `set_era_config(eras)` populates `_era_color_map` / `_era_short_map`.
- 15-colour `ERA_PALETTE` for dynamic assignment.
- Universal category list (added Social, Scientific, Religious; kept Aboriginal as alias to Indigenous).
- `render_timeline()` now takes `eras_config` param, `render_map()` takes `country_config`.
- `app.py` rewritten with country search bar at top, dynamic header + filters + colour key, loading/error state UI.

### Infrastructure
- `.env` file for local secrets (gitignored).
- `.gitignore` updated (.env, __pycache__, .claude).
- `requirements.txt` updated: +supabase, +python-dotenv, +anthropic.
- Branch `multi-country-refactor` pushed to GitHub (not merged to main yet).
- `PLAN.md` saved in project root.

### Iceland seeded (2026-05-19)
- Hand-extracted 92 events / 10 eras from the Wikipedia History of Iceland article (Charlie pasted the text).
- Pre-Settlement → Settlement Age (874-930) → Commonwealth (930-1262) → Norwegian Rule → Kalmar Union → Danish Rule and Trade Monopoly → Path to Independence → Kingdom of Iceland → Cold War Republic → Modern Republic.
- 32 major events, 25 with map coordinates, centre 64.96 / -19.02, zoom 6.
- Created `iceland_data.json` (raw structured data) and generic `seed_country.py` (loads a JSON of this shape and inserts into Supabase) - the latter is the storage-layer prototype that Phase 4 `pipeline.py` will reuse.

### Hardening (2026-05-19)
- **RLS enabled** on all 4 tables. anon + authenticated roles get SELECT only; service_role bypasses for writes. Future seeds and `pipeline.py` writes need the service_role key locally.
- **db.py updated** to prefer `SUPABASE_SERVICE_ROLE_KEY` if set, else fall back to `SUPABASE_KEY`. No app code changes required.
- **GitHub Actions keep-alive cron** added (`.github/workflows/keep-alive.yml`) - hits the Supabase REST API every 6 days to stop the free-tier 7-day auto-pause from breaking the deployed app.
- One-off discovery: the project had auto-paused. Restore took ~2 minutes via `restore_project`. PostgREST schema cache had to be reloaded post-restore (`NOTIFY pgrst, 'reload schema';`) before writes worked again. Worth keeping in mind for future restores.
