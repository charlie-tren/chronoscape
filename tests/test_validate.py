"""Tests for site/validate.py.

The validator is the only thing standing between a malformed country file and
a broken page, since build.py runs it before rendering anything. The
error/warning split matters and is asserted directly: errors fail the build,
warnings are legitimate editorial choices that must NOT.
"""

from validate import validate


def _doc(**over):
    """A minimal country that validates cleanly."""
    doc = {
        "country": {"name": "Testland", "center_lat": 0, "center_lng": 0, "default_zoom": 5},
        "eras": [
            {"name": "Early", "short_name": "E", "sort_order": 0, "year_start": 0,
             "year_end": 100, "date_label": "0-100", "width_pct": 50, "color": "#111111"},
            {"name": "Late", "short_name": "L", "sort_order": 1, "year_start": 100,
             "year_end": 200, "date_label": "100-200", "width_pct": 50, "color": "#222222"},
        ],
        "events": [
            {"era_name": "Early", "sort_year": 50, "display_date": "50", "title": "One",
             "categories": ["Military"], "source": "Testland", "lat": 1.0, "lng": 2.0,
             "is_major": True},
            {"era_name": "Late", "sort_year": 150, "display_date": "150", "title": "Two",
             "categories": [], "lat": None, "lng": None, "is_major": False},
        ],
    }
    doc.update(over)
    return doc


def errs(doc):
    return validate(doc, "t")[0]


def warns(doc):
    return validate(doc, "t")[1]


def test_a_minimal_valid_country_is_clean():
    e, w = validate(_doc(), "t")
    assert e == [] and w == []


# --- structural errors -----------------------------------------------------

def test_missing_country_field_is_an_error():
    d = _doc()
    del d["country"]["center_lat"]
    assert any("center_lat" in x for x in errs(d))


def test_no_eras_or_no_events_is_an_error():
    assert any("no eras" in x for x in errs(_doc(eras=[])))
    assert any("no events" in x for x in errs(_doc(events=[])))


def test_width_pct_must_sum_to_100():
    d = _doc()
    d["eras"][0]["width_pct"] = 49
    assert any("width_pct sums to 99" in x for x in errs(d))


def test_eras_must_be_in_sort_order():
    d = _doc()
    d["eras"][0]["sort_order"], d["eras"][1]["sort_order"] = 1, 0
    assert any("not in sort_order order" in x for x in errs(d))


def test_duplicate_era_sort_order_is_an_error():
    d = _doc()
    d["eras"][1]["sort_order"] = 0
    assert any("duplicate era sort_order" in x for x in errs(d))


def test_era_start_after_end_is_an_error():
    d = _doc()
    d["eras"][0]["year_start"], d["eras"][0]["year_end"] = 100, 0
    assert any("year_start after year_end" in x for x in errs(d))


# --- event errors ----------------------------------------------------------

def test_event_era_must_match_exactly():
    # Fuzzy matching here used to hide renames and silently move events.
    d = _doc()
    d["events"][0]["era_name"] = "early"
    assert any("matches no era" in x for x in errs(d))


def test_unknown_category_is_an_error():
    d = _doc()
    d["events"][0]["categories"] = ["Sporting"]
    assert any("unknown category" in x for x in errs(d))


def test_half_a_coordinate_pair_is_an_error():
    d = _doc()
    d["events"][0]["lng"] = None
    assert any("only one of lat/lng" in x for x in errs(d))


def test_out_of_range_coordinates_are_errors():
    d = _doc()
    d["events"][0]["lat"] = 91
    assert any("lat 91 out of range" in x for x in errs(d))
    d = _doc()
    d["events"][0]["lng"] = 181
    assert any("lng 181 out of range" in x for x in errs(d))


def test_duplicate_titles_are_an_error():
    d = _doc()
    d["events"][1]["title"] = "One"
    assert any("duplicate title" in x for x in errs(d))


def test_empty_title_is_an_error():
    d = _doc()
    d["events"][0]["title"] = "   "
    assert any("empty title" in x for x in errs(d))


# --- warnings must NOT be errors -------------------------------------------

def test_event_outside_its_era_warns_but_does_not_fail():
    """Precursor events are filed narratively on purpose - Iceland's pre-874
    voyages sit in the Settlement Age. This must never fail a build."""
    d = _doc()
    d["events"][0]["sort_year"] = -5
    e, w = validate(d, "t")
    assert e == []
    assert any("outside its era" in x for x in w)


def test_whole_year_comparison_tolerates_a_fractional_sort_year():
    # 100.4 is inside an era ending at 100 - the fraction only orders events
    # within the year and must not trip the range check.
    d = _doc()
    d["events"][0]["sort_year"] = 100.4
    d["events"][0]["era_name"] = "Early"
    e, w = validate(d, "t")
    assert e == []
    assert not any("outside its era" in x for x in w)


def test_unsorted_events_warn():
    d = _doc()
    d["events"][0]["sort_year"] = 199
    assert any("not sorted by sort_year" in x for x in warns(d))


def test_too_many_key_events_warns():
    d = _doc()
    for ev in d["events"]:
        ev["is_major"] = True
        ev["source"] = "Testland"
    assert any("noisy" in x for x in warns(d))
    assert errs(d) == []


# --- source citations -------------------------------------------------------
#
# Every one of these was checked to FAIL before the rule existed - see the
# mutation list in CLAUDE.md. A citation test that cannot go red is worthless,
# because the whole point of the field is that nobody re-reads 290 of them.

def test_major_event_without_a_source_is_an_error():
    d = _doc()
    del d["events"][0]["source"]
    assert any("is_major but has no source" in x for x in errs(d))


def test_minor_event_without_a_source_is_fine():
    d = _doc()
    d["events"][1].pop("source", None)
    assert errs(d) == []


def test_source_given_as_a_url_is_an_error():
    d = _doc()
    d["events"][0]["source"] = "https://en.wikipedia.org/wiki/Knossos"
    assert any("store the article slug only" in x for x in errs(d))


def test_source_with_a_space_is_an_error():
    # Wikipedia accepts spaces in titles but the slug must be canonical, or
    # two spellings of the same article read as two different sources.
    d = _doc()
    d["events"][0]["source"] = "Battle of Marathon"
    assert any("use underscores" in x for x in errs(d))


def test_whitespace_only_source_is_an_error():
    d = _doc()
    d["events"][0]["source"] = "   "
    assert any("empty source" in x for x in errs(d))


def test_percent_escape_in_a_source_is_an_error():
    # The renderer runs encodeURIComponent, so a pre-encoded slug would be
    # double-encoded and 404.
    d = _doc()
    d["events"][0]["source"] = "Battle_of_Marathon%20"
    assert any("not a valid article slug" in x for x in errs(d))


def test_a_slug_with_an_en_dash_or_diacritic_is_accepted():
    # The no-dash house rule does not reach this field: the article really is
    # "Egyptian-en-dash-Hittite peace treaty" and a hyphen version does not exist.
    for slug in ["Egyptian–Hittite_peace_treaty", "Jōmon_period",
                 "2013_Egyptian_coup_d'état", "Poynings'_Law"]:
        d = _doc()
        d["events"][0]["source"] = slug
        assert errs(d) == [], slug
