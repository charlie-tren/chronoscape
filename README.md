# Chronoscape

Pick a country, get its history as a timeline you can walk through on a map.

**https://charlietrenorden.com/chronoscape/**

In progress. Ten countries so far: Egypt, Greece, Iceland, Ireland, Italy, Japan,
Mexico, Norway, Peru and Taiwan.

## What it does

One static page per country: a timeline strip divided into eras, the event list, and a
map. Selecting an event on the strip fills the detail panel and moves the map. Events
carry a category, an optional location, and a flag marking the pivotal ones.

Years before the common era are negative, so a range that straddles zero, or an era
that opens and closes in the same year, both behave.

## Data

`countries/<slug>.json`, one file per country, checked into the repo. Events were
drafted from Wikipedia with the Claude API and corrected by hand.

Every pivotal event has to name the Wikipedia article it came from, and the validator
rejects the file if one does not. A well-formed slug is not the same as an article that
exists: of the first 290 written, eight were wrong, six pointing at nothing and two at
disambiguation pages. They are worth checking against the API before committing.

## Build

Python and Jinja2 into static HTML. No database, no server, no JS toolchain. Supabase
was retired in July 2026 and the Streamlit app with it. Published to GitHub Pages by
CI on every push to master; the old `chronoscape.charlietrenorden.com` subdomain 301s
to the address above. The map is MapLibre over OpenFreeMap tiles.

```
pip install -r requirements-build.txt
python site/build.py            # build every country
python site/build.py taiwan     # build one, still validates all
python site/validate.py         # check the data without building
python -m pytest tests -q       # 39 tests, run in CI before the build
```

## Notes

- The default branch is `master`, not `main`.
- `site/README.md` has the build detail. `countries/README.md` has the data schema and
  the conventions for adding a country.
- `PLAN.md` describes the original Supabase and Streamlit design. It is kept as
  history and no longer matches what is built.

## Sources

Event text is drawn from Wikipedia, and every pivotal event links the article it came
from.
