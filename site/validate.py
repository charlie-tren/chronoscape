"""Validation for countries/*.json.

Run by build.py before anything is rendered, so a malformed country fails the
build instead of quietly shipping. Also runnable on its own:

    python site/validate.py            # check every country
    python site/validate.py ireland    # check one
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "countries"

# Must stay in step with CATEGORY_COLORS in the renderer.
VALID_CATEGORIES = {
    "Military", "Political", "Economic", "Indigenous", "Aboriginal",
    "Foreign Relations", "Cultural", "Social", "Scientific", "Religious",
}

REQUIRED_COUNTRY = {"name", "center_lat", "center_lng", "default_zoom"}
REQUIRED_ERA = {
    "name", "short_name", "sort_order", "year_start",
    "year_end", "date_label", "width_pct", "color",
}
REQUIRED_EVENT = {"era_name", "sort_year", "display_date", "title"}


def validate(data: dict, label: str) -> tuple[list[str], list[str]]:
    """Check one country.

    Returns (errors, warnings). Errors fail the build - they mean the page
    would render wrongly or not at all. Warnings are reported and ignored,
    because some of them are legitimate editorial choices: precursor events are
    often placed in the era they belong to narratively rather than the one
    their date falls in (Iceland's pre-874 voyages sit in the Settlement Age;
    Taiwan's events about Koxinga's father sit in the Koxinga era).
    """
    errors: list[str] = []
    warnings: list[str] = []

    def err(msg: str) -> None:
        errors.append(f"{label}: {msg}")

    def warn(msg: str) -> None:
        warnings.append(f"{label}: {msg}")

    country = data.get("country") or {}
    eras = data.get("eras") or []
    events = data.get("events") or []

    for k in REQUIRED_COUNTRY - set(country):
        err(f"country is missing {k!r}")
    if not eras:
        err("no eras")
    if not events:
        err("no events")

    # --- eras ---
    for i, e in enumerate(eras):
        for k in REQUIRED_ERA - set(e):
            err(f"era[{i}] missing {k!r}")
        if e.get("year_start") is not None and e.get("year_end") is not None:
            if e["year_start"] > e["year_end"]:
                err(f"era {e.get('name')!r} has year_start after year_end")

    total_width = sum(e.get("width_pct", 0) for e in eras)
    if round(total_width, 6) != 100:
        err(f"era width_pct sums to {total_width}, not 100")

    orders = [e.get("sort_order") for e in eras]
    if orders != sorted(orders):
        err("eras are not in sort_order order")
    if len(set(orders)) != len(orders):
        err("duplicate era sort_order values")

    era_names = {e.get("name") for e in eras}
    if len(era_names) != len(eras):
        err("duplicate era names")

    # --- events ---
    seen_titles = set()
    for i, ev in enumerate(events):
        where = f"event[{i}] {ev.get('title', '?')!r}"

        for k in REQUIRED_EVENT - set(ev):
            err(f"{where} missing {k!r}")
        if not str(ev.get("title", "")).strip():
            err(f"{where} has an empty title")

        # Era must match EXACTLY. Fuzzy matching used to paper over this and it
        # meant an era rename could silently move events - see the Taiwan
        # normalisation in TODO.md.
        if ev.get("era_name") not in era_names:
            err(f"{where} era_name {ev.get('era_name')!r} matches no era")
        else:
            era = next(e for e in eras if e["name"] == ev["era_name"])
            y = ev.get("sort_year")
            # sort_year carries a fractional part to order events within a year
            # (1944.4 is May 1944), so compare on the whole year - an era ending
            # in 1944 contains every month of 1944.
            if y is not None and not (era["year_start"] <= int(y // 1) <= era["year_end"]):
                warn(
                    f"{where} sort_year {y} outside its era "
                    f"[{era['year_start']}, {era['year_end']}]"
                )

        for c in ev.get("categories") or []:
            if c not in VALID_CATEGORIES:
                err(f"{where} unknown category {c!r}")

        lat, lng = ev.get("lat"), ev.get("lng")
        if (lat is None) != (lng is None):
            err(f"{where} has only one of lat/lng")
        if lat is not None and not (-90 <= lat <= 90):
            err(f"{where} lat {lat} out of range")
        if lng is not None and not (-180 <= lng <= 180):
            err(f"{where} lng {lng} out of range")

        t = ev.get("title")
        if t in seen_titles:
            err(f"{where} duplicate title")
        seen_titles.add(t)

    if events and [e.get("sort_year") for e in events] != sorted(
        e.get("sort_year") for e in events
    ):
        warn("events are not sorted by sort_year")

    # Advisory, not fatal: too many key events makes the timeline noisy.
    majors = sum(1 for e in events if e.get("is_major"))
    if events and majors / len(events) > 0.55:
        warn(f"{majors}/{len(events)} flagged is_major ({majors/len(events):.0%}) - noisy, aim for 35-45%")

    return errors, warnings


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ([f"{path.name}: invalid JSON - {exc}"], [])
    return validate(data, path.stem)


def validate_all(only: str | None = None) -> tuple[list[str], list[str]]:
    files = sorted(COUNTRIES.glob("*.json"))
    if only:
        files = [f for f in files if f.stem == only]
    errors, warnings = [], []
    for f in files:
        e, w = validate_file(f)
        errors.extend(e)
        warnings.extend(w)
    return errors, warnings


if __name__ == "__main__":
    only = sys.argv[1].lower() if len(sys.argv) > 1 else None
    errors, warnings = validate_all(only)
    for w in warnings:
        print("  warn:", w)
    if errors:
        print(f"\n{len(errors)} error(s):\n")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    n = 1 if only else len(list(COUNTRIES.glob("*.json")))
    print(f"\n{n} country file(s) valid ({len(warnings)} warning(s)).")
