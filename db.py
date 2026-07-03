"""Local JSON-file loader for country timelines.

Data lives in `countries/*.json` in the repo. Each file matches the schema
of `iceland.json` (country + eras + events). This module keeps the same
public surface db.py used to expose over Supabase (list_countries,
load_country_data) so app.py needs no structural changes.

The Supabase backend was retired 2026-07-03 - free-tier project quota was
being reserved for other Rochford projects and Chronoscape is effectively
read-only. To add a new country: drop a JSON file into countries/, commit,
push. Streamlit Cloud picks it up on the next rebuild.
"""

import json
from functools import lru_cache
from pathlib import Path

from event_data import TimelineEvent

COUNTRIES_DIR = Path(__file__).parent / "countries"


@lru_cache(maxsize=32)
def _load_json(path_str: str) -> dict:
    with Path(path_str).open(encoding="utf-8") as f:
        return json.load(f)


def _country_files() -> list[Path]:
    if not COUNTRIES_DIR.exists():
        return []
    return sorted(COUNTRIES_DIR.glob("*.json"))


def list_countries() -> list[dict]:
    """Return all countries available on disk, sorted by name."""
    out = []
    for p in _country_files():
        data = _load_json(str(p))
        c = data["country"]
        out.append({
            "name": c["name"],
            "name_lower": c["name"].lower(),
            "status": "ready",
            "event_count": len(data.get("events", [])),
        })
    out.sort(key=lambda x: x["name"])
    return out


def load_country_data(country_name: str) -> tuple:
    """Load a country's full data from countries/<name>.json.

    Returns (events: list[TimelineEvent], eras_config: list[dict], country_config: dict)
    or (None, None, None) if the country isn't on disk.
    """
    target = country_name.strip().lower()
    for p in _country_files():
        data = _load_json(str(p))
        if data["country"]["name"].lower() != target:
            continue

        events = []
        for i, e in enumerate(data.get("events", [])):
            coords = None
            if e.get("lat") is not None and e.get("lng") is not None:
                coords = (e["lat"], e["lng"])
            events.append(TimelineEvent(
                id=i,
                raw_date=e.get("display_date", ""),
                sort_year=e["sort_year"],
                display_date=e["display_date"],
                title=e["title"],
                description=e.get("description", ""),
                era=e["era_name"],
                categories=e.get("categories", []),
                coordinates=coords,
                is_major=e.get("is_major", False),
            ))

        country_config = {
            "name": data["country"]["name"],
            "center_lat": data["country"].get("center_lat", 0),
            "center_lng": data["country"].get("center_lng", 0),
            "default_zoom": data["country"].get("default_zoom", 5),
        }
        return events, data.get("eras", []), country_config

    return None, None, None
