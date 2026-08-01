from nfl_edge.edge import _is_coinflip, build_candidates


def test_coinflip_near_zero_margin():
    assert _is_coinflip(0.0) is True
    assert _is_coinflip(0.9) is True
    assert _is_coinflip(-0.9) is True


def test_coinflip_clear_side():
    assert _is_coinflip(3.2) is False
    assert _is_coinflip(-2.1) is False


def test_coinflip_blocks_sides_keeps_total():
    games = [
        {
            "home": "Dallas Cowboys",
            "away": "Philadelphia Eagles",
            "kickoff_et": "1:00 PM ET",
            "prices": {
                "home": "Dallas Cowboys",
                "away": "Philadelphia Eagles",
                "ml_home": 1.91,
                "ml_away": 1.91,
                "total_line": 44.5,
                "total_over": 1.91,
                "total_under": 1.91,
                "spread_line": -1.0,
                "spread_home": 1.91,
                "spread_away": 1.91,
                "commence_time": "2026-11-01T18:00:00Z",
            },
            "model": {
                "exp_margin": 0.4,
                "exp_total": 49.5,
                "p_home": 0.51,
                "p_away": 0.49,
                "p_over": 0.62,
                "p_under": 0.38,
                "p_home_cover": 0.51,
                "p_away_cover": 0.49,
            },
            "talent": {"notes": {}},
        }
    ]
    cands = build_candidates(games)
    assert cands, "the mispriced total must survive"
    assert all(c["market"] == "Total" for c in cands)
