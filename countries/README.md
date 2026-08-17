# Adding a country

One JSON file per country. Drop it in, run the build, commit. There is no
database and no admin UI - the file **is** the content.

Written up 14/08/2026 after adding Greece and Peru, which is when the
conventions below were actually pinned down. Ireland and Japan were built
ad hoc and predate this.

## The shape

```jsonc
{
  "country": { "name": "Greece", "center_lat": 38.4, "center_lng": 23.6, "default_zoom": 6 },
  "eras":   [ /* 10 of these, in chronological order */ ],
  "events": [ /* 100-130 of these, sorted by sort_year */ ]
}
```

### Era

| Field | Notes |
|---|---|
| `name` | Full name. Events reference it **exactly** - see the era-matching note below |
| `short_name` | Timeline band label. Keep under ~15 characters or it crowds |
| `sort_order` | `0..n`, ascending, no gaps or duplicates |
| `year_start` / `year_end` | Numbers. **Negative for BCE.** Start must not exceed end |
| `date_label` | Human text under the band, e.g. `"146 BCE-330 CE"` |
| `width_pct` | Share of timeline width. **Must sum to exactly 100** across all eras |
| `color` | From the ramp below, in order |

### Event

| Field | Notes |
|---|---|
| `era_name` | Must match an era `name` exactly |
| `sort_year` | Number, negative for BCE. A fraction orders events inside a year (`1944.4` = May 1944) |
| `display_date` | What the reader sees: `"c. 800"`, `"28 July 1821"`, `"1912"` |
| `title` | Short. **Must be unique within the country** |
| `description` | One to three sentences |
| `categories` | Subset of the valid list; most events want one or two |
| `lat` / `lng` | Both or neither. `null`/`null` for diffuse national events |
| `is_major` | The key events. Aim for **35-45%** |

Valid categories: `Military`, `Political`, `Economic`, `Indigenous`,
`Aboriginal`, `Foreign Relations`, `Cultural`, `Social`, `Scientific`,
`Religious`.

## The palette

Ten eras, these colours, in this order. Every existing country uses it, so a
new one that deviates looks broken next to the others.

```
#5a8a9a  #6b7f9e  #7a6fa0  #8a6b93  #9c6a7d
#a87356  #b08a45  #8f9a4a  #5f9a6a  #4fa3a0
```

## Conventions that are not obvious

- **Ten eras.** Not a hard rule in code, but the palette has ten entries and
  the legend is laid out for it.
- **`width_pct` is editorial, not proportional to time.** Greece's Bronze Age
  covers two thousand years and gets 8; the Classical era covers 157 years and
  gets 12. Weight by how much there is to show, or antiquity swallows the strip.
- **Aim for 35-45% `is_major`.** Both Greece and Peru came in near 60% on the
  first pass, which the validator flags as noisy - if most dots are key events,
  none of them are. Cutting to the beats you would use to tell the story in
  forty moments is the right filter.
- **Australian English, hyphens only.** No en or em dashes anywhere in
  `display_date` or `description` - they are rendered text.
- **Precursor events may sit in the era they belong to narratively.** Iceland's
  pre-874 voyages live in the Settlement Age. The validator *warns* and the
  build continues; the dot clamps to the segment edge. This is allowed on
  purpose - do not "fix" it by moving the event.
- **Era matching is exact.** `build.py` will fuzzy-match as a fallback and an
  unmatched event silently lands in the **last** era, so a typo hides rather
  than erroring. `validate.py` catches it - do not skip validation.

## Workflow

```bash
python site/validate.py greece     # one country
python site/validate.py            # all of them
python site/build.py               # validates, then renders to site/dist/
python -m pytest tests -q          # the code, not the data
```

Then commit the JSON and push. **Publishing is not automatic yet** - see the
Cloudflare item in `TODO.md`. Until the `CLOUDFLARE_API_TOKEN` secret exists,
the live domain needs:

```bash
python site/build.py && npx wrangler pages deploy site/dist --project-name chronoscape-timeline
```

The deploy workflow reports how many versions behind the live domain is on
every push, so you will see it in the Actions annotation if you forget.

## Sourcing the content

Both Greece and Peru were written by hand from general knowledge and checked
against Wikipedia, then emitted from a throwaway script holding the events as
compact tuples - far easier to review and reorder than raw JSON, and it makes
the `width_pct` sum and the sort trivial to get right. The scripts were not
kept; the JSON is the artefact.

An automated Wikipedia-to-JSON pipeline existed (`pipeline.py`) and was deleted
with the Supabase backend. `TODO.md` records what bringing it back would take.
