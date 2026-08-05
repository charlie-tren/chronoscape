"""Static-site spike: build one HTML page per country from countries/*.json.

Proves the proposed stack: Python + Jinja2 -> static HTML, no JS toolchain.
The event list is rendered SERVER-SIDE (real HTML in the source, so it is
indexable - the thing Streamlit cannot do), while the timeline and map get the
data as embedded JSON for client-side interactivity.

Usage:
    python spike/build.py            # build every country in countries/
    python spike/build.py taiwan     # build just one

Output goes to spike/dist/, which is deployable to Cloudflare Pages as-is.
"""

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
SPIKE = ROOT / "spike"
COUNTRIES = ROOT / "countries"
DIST = SPIKE / "dist"

# Mirrors timeline_component.py so the ported JS keeps identical geometry.
TOTAL_WIDTH = 6000


def proportional_position(sort_year: float, year_start: float, year_end: float) -> float:
    """Where a dot sits inside its era segment, as a percentage."""
    if year_end == year_start:
        return 50.0
    y = max(year_start, min(year_end, sort_year))
    pct = (y - year_start) / (year_end - year_start)
    return 6 + pct * 88


def match_era(event_era: str, era_names: list[str]) -> str:
    """Resolve an event's era_name to a canonical era (exact, then fuzzy)."""
    lower = event_era.lower()
    for name in era_names:
        if name.lower() == lower:
            return name
    for name in era_names:
        if name.lower() in lower or lower in name.lower():
            return name
    return era_names[-1] if era_names else event_era


def build_segments(eras: list[dict], events: list[dict]) -> list[dict]:
    """Group events into era swimlanes with pre-computed dot positions."""
    era_names = [e["name"] for e in eras]
    by_era: dict[str, list[dict]] = {}
    for i, ev in enumerate(events):
        by_era.setdefault(match_era(ev["era_name"], era_names), []).append({**ev, "id": i})

    segments = []
    for era in eras:
        evts = sorted(by_era.get(era["name"], []), key=lambda e: e["sort_year"])
        segments.append({
            "width_pct": era.get("width_pct", 8),
            "color": era.get("color", "#666666"),
            "era_label": era.get("short_name", era["name"]),
            "date_label": era.get("date_label", ""),
            "dots": [
                {
                    "id": ev["id"],
                    "left": round(
                        proportional_position(
                            ev["sort_year"], era.get("year_start", 0), era.get("year_end", 1)
                        ),
                        2,
                    ),
                    "major": bool(ev.get("is_major")),
                    "tooltip": f"{ev['display_date']}: {ev['title']}",
                }
                for ev in evts
            ],
        })
    return segments


def build_country(path: Path, env: Environment, all_countries: list[dict]) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    country, eras, events = data["country"], data["eras"], data["events"]

    # Stable ids by index, matching the order the list and map both use.
    for i, ev in enumerate(events):
        ev["id"] = i

    era_colors = {e["name"]: e.get("color", "#666666") for e in eras}
    era_shorts = {e["name"]: e.get("short_name", e["name"]) for e in eras}
    era_names = [e["name"] for e in eras]
    for ev in events:
        canonical = match_era(ev["era_name"], era_names)
        ev["era_color"] = era_colors.get(canonical, "#666666")
        ev["era_short"] = era_shorts.get(canonical, canonical)

    # GeoJSON for MapLibre - only events that actually have coordinates.
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [ev["lng"], ev["lat"]]},
            "properties": {
                "id": ev["id"],
                "color": ev["era_color"],
                "major": bool(ev.get("is_major")),
                "title": ev["title"],
                "date": ev["display_date"],
            },
        }
        for ev in events
        if ev.get("lat") is not None and ev.get("lng") is not None
    ]

    categories = sorted({c for ev in events for c in (ev.get("categories") or [])})

    slug = path.stem
    html = env.get_template("country.html.j2").render(
        country=country,
        slug=slug,
        eras=eras,
        events=events,
        categories=categories,
        all_countries=all_countries,
        date_range=f"{eras[0].get('date_label', '')} - present" if eras else "",
        payload=json.dumps(
            {
                "segments": build_segments(eras, events),
                "totalWidth": TOTAL_WIDTH,
                "geojson": {"type": "FeatureCollection", "features": features},
                "center": [country.get("center_lng", 0), country.get("center_lat", 0)],
                "zoom": country.get("default_zoom", 5),
                "events": [
                    {
                        "id": ev["id"],
                        "title": ev["title"],
                        "date": ev["display_date"],
                        "description": ev.get("description", ""),
                        "era": ev["era_name"],
                        "eraShort": ev["era_short"],
                        "eraColor": ev["era_color"],
                        "categories": ev.get("categories") or [],
                        "major": bool(ev.get("is_major")),
                        "lat": ev.get("lat"),
                        "lng": ev.get("lng"),
                        "sortYear": ev["sort_year"],
                    }
                    for ev in events
                ],
            },
            separators=(",", ":"),
        ),
    )

    out = DIST / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    return {"slug": slug, "name": country["name"], "count": len(events)}


def main() -> None:
    only = sys.argv[1].lower() if len(sys.argv) > 1 else None
    files = sorted(COUNTRIES.glob("*.json"))
    if only:
        files = [f for f in files if f.stem == only]
        if not files:
            sys.exit(f"No such country: {only}")

    manifest = [
        {"slug": f.stem, "name": json.loads(f.read_text(encoding="utf-8"))["country"]["name"]}
        for f in sorted(COUNTRIES.glob("*.json"))
    ]

    env = Environment(
        loader=FileSystemLoader(SPIKE / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    DIST.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SPIKE / "static", DIST / "static", dirs_exist_ok=True)

    built = [build_country(f, env, manifest) for f in files]

    # Landing page - the chip picker.
    (DIST / "index.html").write_text(
        env.get_template("index.html.j2").render(all_countries=manifest),
        encoding="utf-8",
    )

    for b in built:
        print(f"  built /{b['slug']}/  ({b['name']}, {b['count']} events)")
    print(f"\n{len(built)} page(s) -> {DIST}")


if __name__ == "__main__":
    main()
