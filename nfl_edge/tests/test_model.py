from nfl_edge.config import LEAGUE_PPG
from nfl_edge.model import model_game, norm_cdf
from nfl_edge.ratings import build_game_talent, league_averages, match_team


def _flat_ratings() -> dict:
    """Two exactly-average teams."""
    mk = lambda name: {
        "team": name,
        "off": 0.0,
        "dfn": 0.0,
        "gp": 17,
        "league_ppg": LEAGUE_PPG,
        "blend_w_current": 1.0,
    }
    return {"teama": mk("Team A"), "teamb": mk("Team B")}


def test_probs_sum_to_one():
    tal = build_game_talent("Team A", "Team B", _flat_ratings(), {"ppg": LEAGUE_PPG})
    mo = model_game(tal, 44.5, -1.0)
    assert abs(mo["p_home"] + mo["p_away"] - 1.0) < 1e-9
    assert abs(mo["p_over"] + mo["p_under"] - 1.0) < 1e-9
    assert abs(mo["p_home_cover"] + mo["p_away_cover"] - 1.0) < 1e-9


def test_hca_makes_even_matchup_favor_home():
    tal = build_game_talent("Team A", "Team B", _flat_ratings(), {"ppg": LEAGUE_PPG})
    mo = model_game(tal, None, None)
    assert abs(mo["exp_margin"] - 2.0) < 1e-6  # +1.1 home scoring, +0.9 away suppressed
    assert 0.55 < mo["p_home"] < 0.60


def test_better_offense_raises_total_and_margin():
    r = _flat_ratings()
    r["teama"] = dict(r["teama"], off=6.0)
    good = model_game(build_game_talent("Team A", "Team B", r, {"ppg": LEAGUE_PPG}), 44.5, None)
    flat = model_game(
        build_game_talent("Team A", "Team B", _flat_ratings(), {"ppg": LEAGUE_PPG}), 44.5, None
    )
    assert good["exp_margin"] > flat["exp_margin"] + 5
    assert good["exp_total"] > flat["exp_total"] + 5
    assert good["p_over"] > flat["p_over"]


def test_bad_defense_raises_opponent_points():
    r = _flat_ratings()
    r["teamb"] = dict(r["teamb"], dfn=5.0)  # B allows 5 above league
    mo = model_game(build_game_talent("Team A", "Team B", r, {"ppg": LEAGUE_PPG}), None, None)
    assert mo["pts_home"] > LEAGUE_PPG + 5  # A scores into B's leaky defense


def test_spread_cover_prob_coherent():
    tal = build_game_talent("Team A", "Team B", _flat_ratings(), {"ppg": LEAGUE_PPG})
    mo = model_game(tal, None, -2.0)
    # handicap == -expected margin → cover ≈ coin flip
    assert 0.45 < mo["p_home_cover"] < 0.55


def test_norm_cdf_basics():
    assert abs(norm_cdf(0.0) - 0.5) < 1e-9
    assert norm_cdf(3.0) > 0.99
    assert norm_cdf(-3.0) < 0.01


def test_match_team_fallback_is_league_average():
    t = match_team("Nonexistent Team", {})
    assert t["off"] == 0.0 and t["dfn"] == 0.0
    assert t["league_ppg"] == LEAGUE_PPG


def test_league_averages_empty_table():
    la = league_averages({})
    assert la["ppg"] == LEAGUE_PPG


def test_talent_notes_carry_deviations():
    r = _flat_ratings()
    r["teama"] = dict(r["teama"], off=3.5, dfn=-2.0)
    tal = build_game_talent("Team A", "Team B", r, {"ppg": LEAGUE_PPG})
    n = tal["notes"]
    assert n["home_off"] == 3.5
    assert n["home_def"] == -2.0
    assert n["away_off"] == 0.0
