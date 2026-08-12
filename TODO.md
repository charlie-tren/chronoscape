# TODO - Chronoscape (multi-country history timeline)

Last updated: 2026-08-12
Current branch: `master` (GitHub default branch is also `master`; Streamlit Cloud deploys from master)
GitHub: `charlie-tren/chronoscape`
Deployed: **https://chronoscape.charlietrenorden.com** - the static build (`site/`) on
**Cloudflare Pages**, project `chronoscape-timeline`. Migrated off Streamlit Community
Cloud on 06/08/2026 because it slept after 12h of no traffic and supports no custom
domain. Egypt + Iceland + Ireland + Japan + Taiwan, data in `countries/*.json`.
`charlietrenorden.com/chronoscape` redirects here.

`/` is NOT a picker. It renders the `DEFAULT_COUNTRY` timeline (currently Taiwan) from
`site/build.py`, with the canonical pointing at `/taiwan/` so the two copies are not rival
pages. The old `index.html.j2` welcome card is deleted.

Architecture: **no live database.** Country data is checked into `countries/<name>.json`. `db.py` is a JSON loader that keeps the old query surface. Supabase was retired 2026-07-03 - free-tier project quota was needed for `rochford-news-monitor`, and Chronoscape's data is small and read-only.

---

## Outstanding

- [ ] **Two dead Supabase secrets are still on this repo.** `SUPABASE_ANON_KEY` and
      `SUPABASE_URL`, both set 19/05/2026. Supabase was retired 03/07/2026 and there is no
      live database, so these are credentials with no purpose sitting in the repo settings.
      Noticed 11/08/2026 while listing secrets for the deploy workflow; NOT deleted, because
      revoking a credential is Charlie's call and I cannot read them to check whether the
      underlying project still exists. If the Supabase project is gone they are inert; if it
      is not, they are live keys to an unused database and should be rotated or revoked:
        `gh secret delete SUPABASE_ANON_KEY -R charlie-tren/chronoscape`

- [ ] **There are TWO Cloudflare Pages projects for this repo - consolidate to one.**
      Confirmed 07/08/2026 by comparing the version footer across hostnames:
        - `chronoscape-timeline.pages.dev`  -> v3.49   (direct upload via wrangler; the
          custom domain points HERE, so this is what visitors get)
        - `chronoscape-8m5.pages.dev`       -> v3.50   (project `chronoscape`, Git-connected,
          auto-deploys on push, currently has no custom domain)
      Both are in the gmail Cloudflare account. The split is why the live domain lagged the
      repo: the domain is served by the project that does NOT rebuild on push.
      Two ways to fix, pick one:
        (a) Connect Git on `chronoscape-timeline` (see the item below) and delete
            `chronoscape`; or
        (b) Move the custom domain onto `chronoscape` (already Git-connected and current)
            and delete `chronoscape-timeline`. Fewer steps - it is already auto-deploying.
      Diagnostic note for next time: a direct-upload Pages project emits **no GitHub
      check-runs**, so scanning commit check-runs will not reveal it. List the projects via
      `/api/v4/accounts/<id>/pages/projects` instead.
      **11/08/2026 - the case for (b) is now much stronger, and it is measured.** Pushing the
      favicon fix (`aa473ec`) to `master` auto-deployed the Git-connected project and it is
      fully correct there: `/`, `/taiwan/`, `/iceland/`, `/ireland/` and `/sitemap.xml` all
      200, and the new icon serves. The version gap is the whole story:
        - `chronoscape-8m5.pages.dev` (Git-connected)  -> **v3.54**, current
        - `chronoscape-timeline.pages.dev` (direct)     -> v3.51
        - `chronoscape.charlietrenorden.com`            -> v3.51, i.e. the stale one
      **So visitors are three versions behind the repo, and every fix will keep missing the
      live domain until this is done.** (b) is a domain move onto a project already proven
      complete and current - not a migration.
      **This blocks favicon work specifically:** the fix is committed and correct but the
      live site still shows the old emoji `data:` URI, and `/favicon.ico` 404s there.
      Deploying it the other way needs
      `npx wrangler pages deploy site/dist --project-name chronoscape-timeline`, which needs
      `CLOUDFLARE_API_TOKEN` - **not present on the `charl` machine** (no env var, no stored
      wrangler OAuth in `AppData/Roaming/xdg.config/.wrangler`). Per
      `feedback-machine-scoped-findings` that is a statement about THIS machine only.
      **A deploy workflow now exists** (`.github/workflows/deploy.yml`, added 11/08/2026) so
      this needs no dashboard at all. It builds on every push to `master` and publishes to
      `chronoscape-timeline` with `wrangler`. It is inert until TWO repo secrets are set:
        `gh secret set CLOUDFLARE_API_TOKEN -R charlie-tren/chronoscape`
        `gh secret set CLOUDFLARE_ACCOUNT_ID -R charlie-tren/chronoscape`
      The token needs the **Cloudflare Pages: Edit** permission. **Charlie sets these - an
      agent must not create or handle the token value.** Until then the build still runs and
      the run goes GREEN, but it writes a "Not deployed" warning annotation rather than
      skipping silently, so a green tick can never be misread as published (same principle as
      the Consensus Drift publish guard).
      Once the secrets are in, the pending favicon fix (`aa473ec`) publishes on the next push
      with no further work.
      **Wrong-hostname trap, cost me a probe:** the Git-connected project's host is
      `chronoscape-8m5.pages.dev`, NOT `chronoscape.pages.dev`. The latter exists, returns
      200, and serves a COMPLETELY DIFFERENT site (uppercase "CHRONOSCAPE", `/logo.png`), so
      probing it looks like a real answer and is not. Read the hostname off this item rather
      than guessing it from the project name.

- [ ] **Connect Git auto-deploy on Cloudflare Pages.** The project was created by direct
      upload (`wrangler pages deploy`), so it does NOT rebuild when this repo is pushed.
      Adding a country currently needs a manual redeploy:
        `python site/build.py && npx wrangler pages deploy site/dist --project-name chronoscape-timeline`
      To automate: Cloudflare dashboard -> Workers & Pages -> chronoscape-timeline ->
      Settings -> Builds -> Connect to Git, branch `master`, build command
      `pip install -r requirements-build.txt && python site/build.py`, output `site/dist`.
      Dashboard-only - wrangler has no command for it. About five clicks.
      If the Python version trips the build, set `PYTHON_VERSION=3.13.3` in the project's
      build environment variables.
      **NOT DONE BY AN AGENT ON PURPOSE (10/08/2026).** "Connect" opens a **GitHub OAuth
      grant**, handing Cloudflare persistent access to the repositories. That is a
      third-party authorisation rather than a config toggle, so it needs Charlie's own hand
      even when the rest of a dashboard job has been delegated. Everything after the grant -
      branch, build command, output directory - is fine to automate.

- [x] **Confirm the map panel renders in a real browser.** CLOSED 12/08/2026 - it renders.
      Served over http to a real Chrome, the Japan page paints coastline, place names and
      the era-coloured event markers, and `#map canvas` exists. This corroborates the
      10/08 Playwright capture of `/iceland/`; the original report was a false alarm twice
      over. Two separate artefacts produced the blank captures: headless not painting WebGL
      without a settle delay, and `file://` refusing the ES-module import of `app.js` (which
      blanks the timeline as well as the map). **Always verify this site over http, never
      `file://`.** Not a regression - do not rewrite the map.

- [ ] **The hub card still reads "In progress".** It flips to "Live" once Chronoscape
      covers meaningfully more than Iceland + Ireland + Taiwan. That change is in the hub
      repo (`index.html`), not here. **Now due**: Japan and Egypt landed 12/08/2026, so the
      site covers five countries.

- [ ] **Japan and Egypt are not live until a deploy runs.** They are committed here, but
      the custom domain is served by the direct-upload project, so the two new timelines -
      and the new landing page, the Oswald wordmark and the bigger map - will not appear
      until either the two repo secrets above are set (then `deploy.yml` publishes on the
      next push, no further work) or someone runs the manual `wrangler pages deploy`.


### Test coverage - no test suite exists (added 07/08/2026, estate-wide test audit)

- [ ] **Add tests for the two surviving modules.** The migration is done - the
      Streamlit app was removed in `83384d6`, so the surface is now just
      `site/build.py` and `site/validate.py`. That makes this small and worth
      doing now rather than deferring: five pure functions and a validator.

      - `build_segments(eras, events)` - the timeline layout. Assert event-to-era
        assignment and ordering against a fixture, including an event that falls
        on an era boundary and one that matches no era at all.
      - `proportional_position(sort_year, year_start, year_end)` - the positioning
        maths. Assert the endpoints, the midpoint, a BC (negative) year, and a
        zero-width range (which should not divide by zero).
      - `match_era(event_era, era_names)` - assert the miss case returns something
        sane rather than raising.
      - `validate(data, label)` - it is the build gate, so test that it actually
        FAILS a malformed country rather than passing it through. Cover a missing
        required key, a bad year type, and an event outside every era. Assert the
        errors/warnings split, not just that something was returned.
      - `version()` - it reads git and has already shipped one bug on a shallow
        clone (fixed in `b0a1c38`). Test the shallow-repo branch, since Cloudflare
        builds are shallow and this is the code path that broke in production.

      NOTE: the header block at the top of this file is stale post-migration - it
      still describes the Streamlit Cloud deploy and `db.py`. Worth a tidy.

### MIGRATION PLAN: Streamlit -> static site (written 2026-08-05, after the spike)

Stack decided, proven, and now built in `site/`: **Python + Jinja2 -> static HTML,
MapLibre + OpenFreeMap for the map, ported vanilla JS for the timeline, hosted free
on Cloudflare Pages.** No database, no auth, no JS toolchain - accounts were dropped
on 2026-08-05 (see phase 5), so this is the final shape rather than a stepping stone.

**Deploy mechanism resolved:** Cloudflare Pages' build image ships **Python 3.13.3**
and can run `pip install` plus a build script, so the whole thing builds natively on
Cloudflare with **no GitHub Actions workflow file**. That matters practically - the
agent's GitHub token lacks `workflow` scope and local `gh` is not logged in, so any
`.github/workflows/*` change needs the web editor. Cloudflare-native build avoids it.

**Design decision - the COUNTRY page is the indexable unit, not the event.** One page
per event would be ~6,500 pages at 50 countries and ~25,900 at 200, past the ~5,000
where `next build`-class tooling starts to struggle, for pages of one paragraph each.
So: 200 country pages for SEO, and events get `#event-<id>` hash deep links for
sharing. This is a change from the earlier loose talk of "200+ indexable pages" -
the win is 1 -> 200, not 1 -> 26,000.

#### Phase 1 - turn the spike into a real site  ** DONE 2026-08-05 **
- [x] Promoted `spike/` -> `site/`.
- [x] **Hash deep links** - `/taiwan/#event-80` opens with that event selected; `replaceState` so 166 clicks do not bury the back button; clearing selection strips the hash. Verified in-browser.
- [x] **Canonical + Open Graph + Twitter card** on country and landing pages. `SITE_URL` env var overrides the origin for preview builds.
- [x] **`sitemap.xml` + `robots.txt`** generated by the build.
- [x] **404 page** (`/404.html`, which Cloudflare Pages serves automatically), listing the available timelines.
- [x] **`site/validate.py`, wired as a build gate** - bad data fails the build. Verified by injecting a bad era_name and a bad category: build refused. Splits errors (fail) from warnings (report).
- [x] **A11y** - visually-hidden timeline instructions wired via `aria-describedby`, `.visually-hidden` utility, keyboard help text. The server-rendered event list already serves as the text alternative.
- [x] Favicon: keeping the inline emoji data URI. Zero dependencies and it works; a real icon is a nice-to-have, not a blocker.

**Two things worth knowing from doing it:**
- The validator initially flagged 12 "problems". Six were a **bug in the validator**, not the data: `sort_year` carries a fraction to order events within a year (1944.4 = May 1944) and was being compared against an integer era end. The other six are **legitimate editorial placements** - precursor events sitting in the era they belong to narratively (Iceland's pre-874 voyages, Taiwan's Koxinga-father events). Hence errors vs warnings. The data was not touched.
- Accounts were dropped from the roadmap on 2026-08-05, which **settles the framework question permanently** - they were the only argument for Astro or Next over plain Python + Jinja. No future migration pressure.

#### Phase 2 - deploy
- [ ] Create the Cloudflare Pages project against the repo. Build command `pip install -r requirements-build.txt && python site/build.py`, output dir `site/dist`.
- [x] `requirements-build.txt` and `.python-version` added.
- [ ] Point **`chronoscape.charlietrenorden.com`** at it - DNS is already at Cloudflare, so this is a CNAME and automatic TLS. (A path like `/chronoscape` on the hub is harder: GitHub Pages serves the hub at the apex and a real subpath needs a proxy that breaks the cert. Subdomain is the clean answer.)
- [ ] Verify on a real phone - the spike's breakpoints were verified by applying the rules, not by a genuine viewport resize.

#### Phase 3 - cut over
- [ ] Run both in parallel for ~a week.
- [ ] Update the hub card/link to the new domain.
- [ ] Delete the Streamlit app: `app.py`, `db.py`, `styles.py`, `data_parser.py`, `event_data.py`, `event_list_component.py`, `map_component.py`, `timeline_component.py`, `timeline_files/`, `requirements.txt`, `taiwan_timeline.md` - about **2,090 lines**. Keep `countries/*.json` (the data) and `PLAN.md`/`TODO.md` (the history).
- [ ] Delete the Streamlit Cloud app. **This also retires the CARTO basemap problem** below, since the new site is on OpenFreeMap.
- [ ] `.github/workflows/keep-alive.yml` is already dead weight (Supabase retired 2026-07-03) - remove it in the same pass. Needs the web editor, per the scope note above.

#### Phase 4 - the content workflow (this is what makes 50+ countries actually happen)
- [ ] Write down the repeatable process for adding a country: source -> structured JSON -> validate -> commit -> auto-deploy. Ireland was built ad hoc; that does not scale to 50.
- [ ] Nail the conventions in one place: 10 eras, `width_pct` summing to 100, palette colours in order, ~35-40% of events flagged `is_major`, era names matching exactly (see the Taiwan normalisation), coordinates only where genuinely known.
- [ ] Consider a `scripts/new_country.py` scaffold that emits a skeleton + runs the validator.
- Japan and Egypt (12/08/2026) were written as throwaway generator scripts: a flat list of
  `(era, sort_year, display_date, title, description, categories, lat, lng)` tuples, plus an
  explicit `MAJOR = {...}` set of titles, dumped with `json.dumps(indent=2,
  ensure_ascii=False)`. Two things that pattern got right and are worth keeping in the
  scaffold: assertions in the generator (widths sum to 100, sorted by `sort_year`, no
  duplicate titles, every `MAJOR` name matches a real event), and choosing the key events
  as a **named list** rather than flagging them while writing - flagging by feel produced
  63% majors on the first pass, which makes the stars meaningless.

#### Phase 5 - accounts: **DROPPED 2026-08-05**
Charlie decided accounts are not wanted. This removes the only reason to consider
Astro or Next over plain Python + Jinja, and removes the need for Neon and Clerk
entirely. The site stays fully static and fully free. The auth research below is
kept only in case this is ever revisited.

**Rough effort:** phase 1 is a solid session, phase 2 an hour or two mostly waiting on DNS, phase 3 trivial once soaked. Phase 4 is the one that pays off repeatedly.

### Basemap licensing: the app is currently outside CARTO's terms (found 2026-08-05)

`map_component.py` uses `tiles="cartodbdark_matter"`, i.e. CARTO's hosted basemap service. CARTO changed its licence on **2025-10-16** (commit `c2b1c18` on `CartoDB/basemap-styles`, amended 2025-11-11): access to the hosted tile service is now "restricted to CARTO enterprise customers and Non-Profit GRANTS only and is **not available for free public use**". The style code (BSD-3) and design (CC-BY) are still open - only the hosted tiles are restricted.

The tiles **still serve** (verified HTTP 200 on 2026-08-05), so nothing is visibly broken. But this is exactly the kind of thing that gets rate-limited or 403'd without warning, and it is a live term-of-service issue on a public site, not a hypothetical.

- [ ] Move to **OpenFreeMap** (no key, no account, no limits) or another genuinely-free provider. Note every free dark basemap in 2026 is **vector-tile only**, which needs MapLibre - so on Streamlit this is awkward, and it is a further argument for doing the Next.js migration rather than patching folium. Interim option if staying on Streamlit: a raster OSM style, accepting it will not be dark.

### The alternative that was never tested: just rehost Streamlit (researched 2026-08-05)

Before committing to a rewrite, the cheap option was finally evaluated. It is stronger than expected and the framing in this TODO was wrong: **four of the five complaints are Streamlit COMMUNITY CLOUD problems, not Streamlit problems.**

- Community Cloud **sleeps after 12 hours** of no traffic (not days), has **no custom domain support at any tier** (only `*.streamlit.app` subdomains), is **US-only**, and rate-limits GitHub-triggered updates. The stalled deploys are a known, widely-reported issue, not something we were doing wrong.
- **US-only hosting matters a lot here**: from Australia every interaction pays ~200-300ms RTT *before* Python runs. Hosting in Sydney would cut the per-click latency substantially on its own.
- **Rehosting = about half a day and $3-7/mo. Verified: NO host offers a usable FREE always-on tier.** Render's free tier spins down after 15 min (~1 min cold start, cannot be disabled); Railway's free plan gives $1/mo of credit against ~$5/mo for 0.5 GB; **Fly.io removed its free tier entirely in Oct 2024** (2-hour trial only). Cheapest real always-on: **Fly ~$3.32/mo** (512 MB, no plan fee, but must set `auto_stop_machines="off"` and certs cost $0.10/mo), **Railway Hobby $5 + usage** (best-documented websocket support - explicitly exempt from all timeouts), **Render $7/mo** (simplest, never sleeps on paid, but Hobby bandwidth was cut to 5 GB in Apr 2026). Azure Container Apps ~$4-14; Cloud Run ~$46-50 (an open websocket is billed active all month); Hugging Face **deprecated the Streamlit SDK in Apr 2025** and now requires a paid plan for compute Spaces. Streamlit in Snowflake is enterprise-only (~$1,400+/mo always-on) - out of scope.
- **This is the structural point: "free" and "always-on" are incompatible for anything running a server process.** A free tier keeping a Python process warm 24/7 is giving away continuous compute, which is exactly why every free option sleeps. Static hosting is free AND always-on because there is no process.
- Streamlit self-hosting needs websocket support: proxy must forward upgrade headers, `_stcore` paths must be excluded from rewrites, sticky sessions are mandatory behind a load balancer, and `--server.enableCORS=false --server.enableXsrfProtection=false` is usually needed behind a proxy (fine read-only, a real relaxation once auth exists).

**What Streamlit genuinely fixed in 2025-26** (the gap narrowed more than this TODO assumed): **Components v2 (1.51, Oct 2025) made custom components frameless - no iframe**, Shadow DOM style scoping, bidirectional data flow. That directly addresses the timeline's awkward scroll/drag. Plus real theming config (no CSS hacks), horizontal flex containers (1.48), matured `st.fragment` incl. `parallel=True` (1.58), and Tornado replaced by Starlette/Uvicorn (1.57).

**What rehosting can NEVER fix:** (a) the rerun round-trip - every interaction re-executes the script server-side; fragments shrink the Python term, not the network term; (b) **mobile layout - `st.columns` auto-stacks below ~640px and there is still no breakpoint API. The feature request has been open since July 2022.**

**Decision: still go static, but the deciding factor is the budget constraint, not effort.** Rehosting is the better effort-to-benefit trade in isolation, but it costs $2-7/mo forever versus $0 forever for static hosting, and it can never fix mobile. Given "must be fully free" plus a public-facing portfolio site where polish matters, static wins. Rehosting remains the correct fallback if the rewrite stalls - and it is non-destructive, so it can be done first if the migration is going to take a while.

### ⚠️ RE-OPEN before scaffolding: is it actually Next.js? (2026-08-05)

The Astro rejection above was written when **on-demand generation and API routes were assumed**. That premise died on 2026-08-05 when generation was dropped. Two independent analyses have now concluded Next.js is overkill for "static JSON + one timeline + one map".

Options to weigh properly before running `create-next-app`:
- **Astro** - islands model, ships almost no JS, content collections fit `countries/*.json` exactly. Supports SSR + Clerk when accounts land.
- **Eleventy, or plain HTML + vanilla JS** - lowest ceremony.
- **Python-generated HTML (Jinja2) + ~150 lines of vanilla JS** for the two interactive bits. Plays directly to existing skills and avoids the JS toolchain almost entirely. Genuinely worth considering.
- **Next.js** - still the safest choice *if* accounts are definitely coming, since auth + SSR are first-class and Vercel integration is tightest.

Hosting is free on all of these (Cloudflare Pages / GitHub Pages / Netlify / Vercel), so the choice is purely about which is least painful to build and maintain. Note: whichever wins, the map still needs MapLibre (all free dark basemaps are vector-only) and the timeline is still hand-rolled SVG + `d3-scale` - those two decisions are framework-independent.

### Stack investigation: migrate to Next.js + Vercel before scaling up (2026-07-03, decisions resolved 2026-08-05)

Chronoscape is heading toward 50+ countries and user-facing features (search across countries, saved views, share links). Streamlit is fine for the current read-only shape but doesn't scale where the project is going: CSS scoping fights, no server-side API surface, no real auth story, mobile layout limits. Add to that the operational pain seen repeatedly on 2026-08-05 - **no custom domain** (so the personal site can only redirect), **deploys that stall and need a manual Reboot** (twice in one session), and the app **sleeping on inactivity**.

**Recommended target: Next.js on Vercel** (same pattern as `macro-signals-web`, already live). Fit at scale:
- **Content** - `countries/*.json` -> one dynamic route with `generateStaticParams()`, plain SSG on push. No ISR, no DB. See resolved decision 1.
- **User features** - Clerk for accounts + a small Neon Postgres for saved views and share links. See resolved decisions 2 and 3.
- **Perf** - edge caching, static shells. The binding constraint is the RSC payload, not Vercel.
- **Ecosystem** - largest React community, deepest AI-code-gen coverage, MapLibre for the map, hand-rolled SVG + `d3-scale` for the timeline.

*(Note: on-demand Anthropic generation was dropped from the roadmap on 2026-08-05 - too much work, and Wikipedia sources barely change. Countries are generated offline in batches and committed. This removes the write path entirely and is why no database is needed for content.)*

Rejected alternatives (documented so the decision doesn't get relitigated):
- **Astro** - great for read-only static, but loses to Next as dynamic features (generation API, auth, DB queries) enter the picture.
- **Vanilla HTML + D3 + Leaflet** - falls off past a few countries; no component model.
- **Observable Framework** - purpose-built for data storytelling but not for multi-page apps with auth.
- **SvelteKit** - technically a peer of Next but smaller ecosystem and Charlie has no Svelte experience.
- **T3 stack (Next + tRPC + Prisma + NextAuth + Tailwind)** - worth considering if the answer to "will there be user accounts + typed API calls" is a firm yes. Otherwise plain Next is enough.

**Decisions RESOLVED by research 2026-08-05.** Product intent confirmed same day: on-demand generation is OFF (too hard, and Wikipedia sources are near-static - countries get generated offline in batches and committed); user accounts ARE wanted; target 50+ countries; must fix domain / stalled deploys / sleeping / mobile.

**Budget constraint (2026-08-05): must be FULLY FREE at current scale.** Paying is acceptable only if the project actually grows into it. This is a real input to the architecture, not a footnote:
- Every piece of the recommended stack is free at this scale: Vercel Hobby (static hosting + custom domains + auto-deploy), Clerk (50k users), Neon (0.5 GB / 100 CU-hours), OpenFreeMap (no key, no account, no limits).
- **It also argues against the "just rehost Streamlit elsewhere" alternative.** "Free" and "never sleeps" are structurally in tension for anything running a server process - a free tier keeping a Python process warm 24/7 is giving away continuous compute, which is exactly why Streamlit Community Cloud sleeps. A static site is free AND always-on because there is no process. Always-on Python hosting generally costs a few dollars a month and still would not fix the per-interaction rerun latency.
- **One watch item: Vercel Hobby is licensed for personal, NON-COMMERCIAL use.** A portfolio project is fine. Ads, payments or client work would force Pro at $20/user/mo regardless of traffic.
- No cliff edges in this stack at realistic scale. Neon's first paid tier has had no monthly minimum since Dec 2025, so overage degrades to cents rather than a $25 step (which is what Supabase Pro would have been).

1. **Content model - keep JSON in git. No database for content, at any realistic scale.**
   The old "JSON stops scaling past ~50-100 countries" assumption was wrong by 1-2 orders of magnitude. Vercel has **no cap on statically generated pages**; the 2048 limit people hit is on the *routing table*, and one `app/[country]/page.tsx` with `generateStaticParams()` is ONE route entry whether it renders 3 countries or 10,000. Measured from our own data: avg country = 67 KB / 129 events, so 200 countries is ~13 MB and ~26k events. Build stays under a minute. Hard fail is a 45-min build, ~22x away.
   Move to a DB only when one of these fires: (a) cross-cutting queries across all countries (global search / "all events 1900-1950") - though the first fix is a pre-computed index JSON, not a DB; (b) someone other than Charlie edits content, or editing moves into a browser; (c) build exceeds ~10 min or `next build` OOMs (~5,000+ pages); (d) repo over ~500 MB including history; (e) content must change without a deploy.
   Discipline to adopt now: serialise with `sort_keys=True, indent=2, ensure_ascii=False`; validate against a JSON Schema **in the Python generator** so bad content never reaches git; `.gitattributes` with `*.json text eol=lf` on day one or Windows CRLF rewrites turn one-event changes into whole-file diffs. Optional later upgrade if hand-edited JSON starts costing time: **Velite** or **Content Collections** for build-time Zod validation + generated TS types (Contentlayer is abandoned - do not use).

2. **DB for USER data only - Neon, via the Vercel Marketplace.** Content stays static, so the DB holds only `users` / `saved_views` / `share_links`.
   - **Vercel Postgres no longer exists** - discontinued, folded into the Marketplace, existing stores migrated to Neon. Remove it from consideration.
   - **Neon** - 100 free projects (no org-wide cap), 0.5 GB + 100 CU-hours per project. Scales to zero after 5 min idle but **auto-wakes in ~sub-second on the next query**; hostname keeps resolving, no dashboard click. Paid tier has no monthly minimum since Dec 2025, so overage degrades to cents rather than a $25 step.
   - **Turso** is the runner-up and the only option that never idles at all (a DB is a file, not a process); $4.99/mo first paid tier. Cost: SQLite dialect, smaller ecosystem.
   - **Supabase stays rejected.** Both failure modes are still live policy: free projects pause after ~1 week with **manual-only** restore, and the free-project cap is **2 across the whole account**, not per org. This also explains why our keep-alive cron could never have worked: Supabase measures activity as *"user requests to the database"*, i.e. the Postgres query path - not HTTP hits on the project. A REST ping was never going to reset the timer.

3. **Auth - Clerk. Defer it to phase 2; ship the static site first.**
   **"NextAuth or Clerk" is no longer a live choice**: Auth.js/NextAuth was absorbed into Better Auth (Sep 2025) and is security-patch-only, and Auth.js v5 never went stable (npm `latest` is still 4.24.15, v5 at `beta.32` after 3 years). Vercel then acquired Better Auth (Jul 2026). Lucia is deprecated.
   - **Clerk** - 50,000 free MRU (tier changed Feb 2026; note MRU is narrower than MAU). No database or schema needed for auth itself, and no hand-written session / cookie / CSRF code. Best App Router docs. Accept: MFA is Pro-only ($25/mo), 7-day fixed sessions on free.
   - **Better Auth** is the runner-up if data ownership matters - MIT, now a Vercel property, ~6.6M weekly downloads. Cost: you provision Postgres and run migrations, and its CVEs cluster in *plugins*, so enable the minimum set.
   - Clerk user metadata is capped at **8 KB/user** (1.2 KB if in the session token), so saved views still need the Neon tables. Share links are not user-scoped anyway - an anonymous visitor resolves a token - so they need a real lookup table regardless.

**Security rules that must be followed once auth lands** (they do not apply to the static phase):
- **Middleware is NOT an authorisation boundary.** Beyond CVE-2025-29927 there have been six further Next.js middleware bypasses, the latest patched in 16.2.11. Enforce authorisation in the **data access layer** - a `verifySession()` wrapped in React `cache()`, called by every data function, Server Component, Server Action and Route Handler. Middleware does optimistic redirects only.
- **Next.js 16 renamed `middleware.ts` to `proxy.ts`.** Migrating without running `npx @next/codemod@canary middleware-to-proxy` makes route protection **silently stop running**.
- **Clerk CVE-2026-41248**: `createRouteMatcher` could be evaded. Declare which routes are **public** and protect everything else - never allowlist the protected ones.
- Do not put auth checks in a layout (layouts do not re-render on navigation and do not gate sibling segments).

**Migration checklist** (updated 2026-08-05 with research findings):

*Phase 0 - environment (Windows).* Verified: `C:\Users\charl\Documents` is a real local folder, NOT OneDrive-redirected, so Known Folder Move is off. But `C:\Users\charl\OneDrive\Documents` exists, so do not scaffold there - OneDrive + `node_modules` is an open, unfixed conflict (Files On-Demand placeholders break `stat`/`open`; per-folder exclusion is Group-Policy-only and arrives GA ~Aug 2026 for organisations, not personal accounts).
- [ ] Project at **`C:\dev\chronoscape-web`**, outside OneDrive.
- [ ] Add `C:\dev` to **Microsoft Defender exclusions** - this is step 1 of Next.js's own local-development guide.
- [ ] **Node 24 LTS** (Node 20 is EOL and Vercel deprecates it 2026-10-01; Vercel's default is 24.x). `fnm` if you want a version manager - **Volta is unmaintained**, nvm-windows is mid-rewrite. A plain MSI install of Node 24 is also fine for one project. Pin with `.node-version` + `"engines": {"node": "24.x"}` so local matches Vercel.
- [ ] `git config --global core.longpaths true`.
- [ ] **Skip WSL2.** Microsoft's own docs recommend native Windows for JS beginners, and Turbopack uses native NTFS watching so HMR is fine.

*Phase 1 - static site (no DB, no auth).*
- [ ] `npx create-next-app@latest --typescript --app` (Next 16.3: App Router, RSC and Turbopack are all default).
- [ ] Copy `countries/*.json` across as-is - same shape.
- [ ] `app/page.tsx` (chip picker), `app/[country]/page.tsx` + `generateStaticParams()`. **`params` is async in Next 16** (`const { country } = await params`) - most tutorials and AI-generated code predate this.
- [ ] Load the countries directory ONCE into a module-level cache in `lib/content.ts`; do not re-read files per page.
- [ ] **Slim the data before it crosses into any `'use client'` component.** This is the real perf bottleneck, not Vercel: a 150 KB country JSON serialised into the RSC payload is downloaded by every visitor. Bites at 3 countries, not 200.
- [ ] **Map: MapLibre, not Leaflet.** `maplibre-gl@6` + `react-map-gl@8` (`react-map-gl/maplibre`). react-leaflet has not shipped a release in 20 months and Leaflet core in 3 years, its Next.js `window is not defined` issue has been open since Jan 2025, and it is pure ESM so it needs `transpilePackages`. Render the ~50-200 markers as a **GeoJSON source + `circle` layer** with one `map.on('click', ...)` handler, not N React `<Marker>` nodes. Remember `import 'maplibre-gl/dist/maplibre-gl.css'`.
- [ ] **Basemap: move off CARTO** (see the separate item below - this is a live licensing problem, not just a migration task). Use **OpenFreeMap** (`https://tiles.openfreemap.org/styles/dark`) - unlimited, no API key, no account. Two caveats: no SLA, and its style JSON has `attribution: null` so you must add the credit manually via `AttributionControl customAttribution="OpenFreeMap © OpenMapTiles Data from OpenStreetMap"`. Fallback if it ever dies: self-hosted Protomaps PMTiles on Cloudflare R2 (needs HTTP range requests - Vercel is not a supported PMTiles host).
- [ ] **`ssr: false` is NOT allowed in a Server Component in the App Router** - it throws a build error. Needs a three-file sandwich: `page.tsx` (server) renders `MapLoader.tsx` (`'use client'`, does the `dynamic(..., {ssr:false})`) which renders `Map.tsx` (`'use client'`). Any tutorial putting `dynamic(..., {ssr:false})` straight in `page.tsx` is pre-App-Router.
- [ ] **Timeline: hand-rolled SVG + `d3-scale` only** (`scaleTime`, ~16 kB). Rejected: react-chrono (wrong shape, explicitly no zoom/drag), vis-timeline (imperative, 10 peer deps incl. deprecated `moment`), Nivo (15 months stale, no timeline primitive), full D3 (fights React for DOM ownership), visx (viable but an extra abstraction for one component). "D3 for maths, React for DOM" is still the 2026 consensus. Being weak at React argues *for* hand-rolling - one thing to learn, not two. `scaleTime()` is basically `np.interp` with a nicer API.
- [ ] Timeline a11y from the start: **roving tabindex** (container `tabIndex=0`, dots `tabIndex={i===active?0:-1}`, arrows/Home/End) - this also makes keyboard focus auto-scroll the strip for free; `role` + `aria-label` on each dot (SVG shapes have no implicit name); `aria-selected`; tooltip on **focus** as well as hover; keep native `overflow-x:auto` under the drag handler; add a visually-hidden `<ul>` of the same events as a text alternative.
- [ ] Reuse the dark theme + Inter + cyan accent; Tailwind absorbs the tokens from `styles.py DARK_CSS`.
- [ ] Deploy: connect the repo in Vercel. **Plain SSG on git push - no ISR** (ISR solves content changing between deploys, which we do not have, and it is incompatible with static export). Hobby is 1 concurrent deployment / 100 per day.
- [ ] Consider staying **static-export-compatible** as a discipline (no Server Actions, no middleware, no rewrites): it keeps the app portable and permanently outside the entire class of Next.js server CVEs.
- [ ] Confirm parity on Taiwan, then Iceland + Ireland, then point the domain at Vercel. Keep Streamlit live during the swap; soak a week.

*Phase 2 - accounts (only after phase 1 is live).* Clerk + Neon, following the security rules above.

- [ ] Once retired, archive the Streamlit repo (the JSON files stay useful as the data source either way).

**When to trigger:** Before the next substantive feature push. Doing more work in the Streamlit shell now creates rework at migration time. If a new country is the next task, migrate first, then add the country in Next.

### If Anthropic-generated countries come back

The old on-demand Wikipedia -> Claude pipeline (`pipeline.py`, `worker.py`) was deleted along with the Supabase backend. To bring it back:

- [ ] Rewrite `pipeline.py` to output a `countries/<name>.json` file instead of writing to Supabase (same schema).
- [ ] Add either a "generate" button in the app that calls the pipeline synchronously and commits/pushes the JSON, OR a local-only CLI (`python pipeline.py Japan`) that Charlie runs by hand and then commits.
- [ ] Add `anthropic` back to `requirements.txt`.
- [ ] Set `ANTHROPIC_API_KEY` in `.env` locally.

For a side project this "generate locally, commit, push" flow is probably fine - the deployed app never needs write access. The Supabase `generating`/`failed`/`retry` UI states and the failed-state retry button are gone with the DB.

### Cleanup that needs a browser session

- [ ] **Streamlit Cloud**: delete the `SUPABASE_URL` and `SUPABASE_KEY` entries from Streamlit Cloud Secrets - they're no longer read by the app.
- [ ] **Supabase dashboard**: delete the paused project `xbhhdpcbrsgmactfuxlq` ("History Timeline", us-east-1). Frees a project slot in the Rochford org permanently. The Supabase MCP exposes pause/restore/create but NOT delete, so this has to be done via the dashboard UI (Project Settings -> General -> Danger Zone -> Delete Project). Irreversible.

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
