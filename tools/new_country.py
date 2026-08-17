"""Scaffold a new countries/<slug>.json and validate it.

    python tools/new_country.py Portugal --lat 39.5 --lng -8.0 --zoom 6

Writes ten eras on the house palette with `width_pct` already summing to 100,
plus one placeholder event per era so the file validates immediately and the
page renders. Fill in the real content, then:

    python site/validate.py portugal
    python site/build.py

Conventions live in countries/README.md. This only removes the fiddly parts -
getting the palette in order and the widths to total exactly 100.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "countries"

RAMP = ["#5a8a9a", "#6b7f9e", "#7a6fa0", "#8a6b93", "#9c6a7d",
        "#a87356", "#b08a45", "#8f9a4a", "#5f9a6a", "#4fa3a0"]

# Ten widths totalling exactly 100. Weighted towards the later eras, which is
# usually where the events are - reweight freely, just keep the sum at 100.
WIDTHS = [8, 8, 10, 10, 10, 11, 11, 11, 11, 10]


def scaffold(name: str, lat: float, lng: float, zoom: int) -> dict:
    eras, events = [], []
    for i, (colour, width) in enumerate(zip(RAMP, WIDTHS)):
        start, end = 1000 + i * 100, 1000 + (i + 1) * 100
        era_name = f"TODO era {i + 1}"
        eras.append({
            "name": era_name,
            "short_name": f"Era {i + 1}",
            "sort_order": i,
            "year_start": start,
            "year_end": end,
            "date_label": f"{start}-{end}",
            "width_pct": width,
            "color": colour,
        })
        events.append({
            "era_name": era_name,
            "sort_year": start + 50,
            "display_date": str(start + 50),
            "title": f"TODO event {i + 1}",
            "description": "TODO.",
            "categories": ["Political"],
            "lat": None,
            "lng": None,
            "is_major": i % 3 == 0,          # lands near the 35-45% target
        })

    return {
        "country": {"name": name, "center_lat": lat, "center_lng": lng, "default_zoom": zoom},
        "eras": eras,
        "events": events,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new country file.")
    ap.add_argument("name", help="Display name, e.g. Portugal")
    ap.add_argument("--lat", type=float, required=True, help="Map centre latitude")
    ap.add_argument("--lng", type=float, required=True, help="Map centre longitude")
    ap.add_argument("--zoom", type=int, default=6, help="Default zoom (4 huge .. 8 small)")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing file")
    a = ap.parse_args()

    slug = a.name.strip().lower().replace(" ", "-")
    out = COUNTRIES / f"{slug}.json"
    if out.exists() and not a.force:
        print(f"{out.relative_to(ROOT)} already exists. Pass --force to overwrite.")
        return 1

    out.write_text(json.dumps(scaffold(a.name.strip(), a.lat, a.lng, a.zoom),
                              indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} - 10 eras, 10 placeholder events")

    print("\nvalidating...")
    r = subprocess.run([sys.executable, str(ROOT / "site" / "validate.py"), slug], cwd=ROOT)
    if r.returncode == 0:
        print(f"\nNow replace the TODOs. See countries/README.md.")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
