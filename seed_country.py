"""Generic country seeder - loads a JSON file and inserts into Supabase.

Usage:
    python seed_country.py iceland_data.json

The JSON file must have this shape:
    {
        "country": {"name": str, "center_lat": float, "center_lng": float, "default_zoom": int},
        "eras": [{name, short_name, sort_order, year_start, year_end, date_label, width_pct, color}, ...],
        "events": [{era_name, sort_year, display_date, title, description, categories, lat, lng, is_major}, ...]
    }

This is the manual-seed path. The eventual pipeline.py will produce JSON in the
same shape from Wikipedia + Claude extraction, then call the same helpers below.
"""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from db import (
    _get_client,
    create_country,
    update_country,
    save_eras,
    save_events,
)


def seed(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    country_meta = data["country"]
    eras = data["eras"]
    events = data["events"]
    name = country_meta["name"]
    name_lower = name.strip().lower()

    print(f"Seeding {name}: {len(eras)} eras, {len(events)} events")

    client = _get_client()
    existing = (
        client.table("countries")
        .select("id")
        .eq("name_lower", name_lower)
        .limit(1)
        .execute()
    )
    if existing.data:
        country_id = existing.data[0]["id"]
        print(f"  {name} already exists (id={country_id}), updating")
    else:
        record = create_country(name)
        country_id = record["id"]
        print(f"  Created {name} (id={country_id})")

    save_eras(country_id, eras)
    print(f"  Saved {len(eras)} eras")

    save_events(country_id, events)
    print(f"  Saved {len(events)} events")

    update_country(
        country_id,
        status="ready",
        center_lat=country_meta["center_lat"],
        center_lng=country_meta["center_lng"],
        default_zoom=country_meta["default_zoom"],
        event_count=len(events),
        refreshed_at="now()",
    )
    print(f"  Updated {name} status to 'ready'")
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python seed_country.py <path-to-json>")
        sys.exit(1)
    seed(Path(sys.argv[1]))
