from pathlib import Path

from nfl_edge.dedupe import (
    claim_key,
    drop_already_sent,
    filter_to_claim_keys,
    gnorm,
    load_sent_keys,
    pick_key,
    record_sent,
)
from nfl_edge.preflight import missing_live_secrets


def test_pick_key_stable():
    p = {
        "date": "2026-10-27",
        "home": "Boston Celtics",
        "away": "New York Knicks",
        "market": "Total",
        "selection_struct": "OVER 224.5",
    }
    assert pick_key(p) == (
        "2026-10-27",
        "Boston Celtics",
        "New York Knicks",
        "Total",
        "OVER 224.5",
    )


def test_claim_key_matches_family_norm():
    """Must match US EDGE _gkey / grader Build Rows byte-for-byte."""
    p = {
        "date": "2026-11-01",
        "sport": "americanfootball_nfl",
        "home": "Dallas Cowboys",
        "away": "Philadelphia Eagles",
        "market": "Asian Handicap",
        "selection_struct": "HOME -3.5",
    }
    assert gnorm("Dallas Cowboys") == "dallascowboys"
    assert claim_key(p) == (
        "2026-11-01_americanfootballnfl_dallascowboys_philadelphiaeagles_asianhandicap_home35"
    )


def test_drop_shared_sheet_keys():
    p_dup = {
        "date": "2026-10-27",
        "sport": "americanfootball_nfl",
        "home": "Boston Celtics",
        "away": "New York Knicks",
        "market": "Total",
        "selection_struct": "OVER 224.5",
        "pick_name": "Over 224.5",
    }
    p_fresh = {
        "date": "2026-10-27",
        "sport": "americanfootball_nfl",
        "home": "C",
        "away": "D",
        "market": "Moneyline",
        "selection_struct": "HOME",
        "pick_name": "C",
    }
    shared = {claim_key(p_dup)}
    fresh, dups = drop_already_sent([p_dup, p_fresh], set(), shared_claim_keys=shared)
    assert len(dups) == 1 and dups[0]["pick_name"] == "Over 224.5"
    assert len(fresh) == 1 and fresh[0]["pick_name"] == "C"


def test_filter_to_claim_keys():
    p1 = {
        "date": "2026-10-27",
        "sport": "americanfootball_nfl",
        "home": "A",
        "away": "B",
        "market": "Moneyline",
        "selection_struct": "HOME",
    }
    p2 = {
        "date": "2026-10-27",
        "sport": "americanfootball_nfl",
        "home": "C",
        "away": "D",
        "market": "Moneyline",
        "selection_struct": "AWAY",
    }
    kept = filter_to_claim_keys([p1, p2], {claim_key(p1)})
    assert len(kept) == 1
    assert kept[0]["home"] == "A"


def test_drop_already_sent(tmp_path: Path):
    p1 = {
        "date": "2026-10-27",
        "home": "A",
        "away": "B",
        "market": "Total",
        "selection_struct": "OVER 224.5",
        "pick_name": "Over 224.5",
    }
    p2 = {
        "date": "2026-10-27",
        "home": "C",
        "away": "D",
        "market": "Moneyline",
        "selection_struct": "HOME",
        "pick_name": "C",
    }
    record_sent(tmp_path, "2026-10-27", [p1])
    sent = load_sent_keys(tmp_path, "2026-10-27")
    fresh, dups = drop_already_sent([p1, p2], sent)
    assert len(dups) == 1
    assert len(fresh) == 1
    assert fresh[0]["pick_name"] == "C"


def test_preflight_returns_list():
    m = missing_live_secrets()
    assert isinstance(m, list)
