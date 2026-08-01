from __future__ import annotations

"""Team ratings: additive point deviations (offense / defense vs league PPG).

Source: ESPN standings — avgPointsFor / avgPointsAgainst per team (the same
endpoint family proven reachable from both the PC and the datacenter VPS in
NBA EDGE). 17-game seasons make anything fancier than regressed point
differentials noise.

Season boundary: previous-season deviations are SHRUNK by PREV_SEASON_CARRYOVER
(NFL regresses hard year to year), then the current season blends in with
weight gp/(gp+K), K=6. At 0 games (September) ratings are 55% of last season's
deviations — the cold-start answer.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from nfl_edge.config import (
    LEAGUE_PPG,
    PREV_SEASON_CARRYOVER,
    RATINGS_BLEND_K,
)
from nfl_edge.utils import norm_team, safe_float

ET = ZoneInfo("America/New_York")


def current_season_year(now: datetime | None = None) -> int:
    """NFL season is labeled by its starting year; new season begins in September."""
    now = now or datetime.now(ET)
    return now.year if now.month >= 8 else now.year - 1


def _from_espn_standings(season_year: int) -> dict[str, dict[str, float]]:
    """ESPN standings: avgPointsFor / avgPointsAgainst / gamesPlayed per team."""
    r = requests.get(
        f"https://site.api.espn.com/apis/v2/sports/football/nfl/standings?season={season_year}",
        timeout=30,
    )
    r.raise_for_status()
    out: dict[str, dict[str, float]] = {}
    for grp in r.json().get("children") or []:
        for e in (grp.get("standings") or {}).get("entries") or []:
            name = ((e.get("team") or {}).get("displayName")) or ""
            stats = {s.get("name"): s.get("value") for s in e.get("stats") or []}
            # NFL standings carry season TOTALS; games played = W+L+T
            pf_total = safe_float(stats.get("pointsFor"), 0.0)
            pa_total = safe_float(stats.get("pointsAgainst"), 0.0)
            gp = (
                safe_float(stats.get("wins"), 0.0)
                + safe_float(stats.get("losses"), 0.0)
                + safe_float(stats.get("ties"), 0.0)
            )
            if not name or gp <= 0 or pf_total <= 0:
                continue
            out[norm_team(name)] = {
                "team": name,
                "pf": pf_total / gp,
                "pa": pa_total / gp,
                "gp": gp,
            }
    return out


def _deviations(table: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """pf/pa per game → off/def deviations vs that season's league PPG."""
    if not table:
        return {}
    league = sum(v["pf"] for v in table.values()) / len(table)
    out: dict[str, dict[str, float]] = {}
    for key, v in table.items():
        out[key] = {
            "team": v["team"],
            "off": round(v["pf"] - league, 2),           # + = scores above league
            "dfn": round(v["pa"] - league, 2),           # + = allows above league (bad defense)
            "gp": v["gp"],
            "league_ppg": round(league, 2),
        }
    return out


def load_season_ratings(season_year: int) -> dict[str, dict[str, float]]:
    try:
        table = _from_espn_standings(season_year)
        if len(table) >= 30:
            print(f"[ratings] ESPN standings {season_year}: {len(table)} teams")
            return _deviations(table)
        print(f"[ratings] ESPN standings thin ({len(table)} teams) for {season_year}")
    except Exception as e:
        print(f"[ratings] ESPN standings {season_year} failed ({str(e)[:120]})")
    return {}


def load_blended_ratings(now: datetime | None = None) -> dict[str, dict[str, float]]:
    """Current-season deviations blended over shrunk previous-season deviations."""
    y = current_season_year(now)
    cur = load_season_ratings(y)
    prev = load_season_ratings(y - 1)
    for v in prev.values():
        v["off"] = round(v["off"] * PREV_SEASON_CARRYOVER, 2)
        v["dfn"] = round(v["dfn"] * PREV_SEASON_CARRYOVER, 2)
    if not cur and not prev:
        print("[ratings] EMPTY — league averages only")
        return {}
    if not cur:
        print(f"[ratings] season {y} not started — shrunk previous season only")
        for v in prev.values():
            v["blend_w_current"] = 0.0
        return prev
    out: dict[str, dict[str, float]] = {}
    for key, c in cur.items():
        p = prev.get(key)
        gp = float(c.get("gp") or 0)
        w = gp / (gp + RATINGS_BLEND_K)
        if p is None:
            w = 1.0
            p = c
        out[key] = {
            "team": c["team"],
            "off": round(w * c["off"] + (1 - w) * p["off"], 2),
            "dfn": round(w * c["dfn"] + (1 - w) * p["dfn"], 2),
            "gp": gp,
            "league_ppg": c.get("league_ppg") or LEAGUE_PPG,
            "blend_w_current": round(w, 3),
        }
    for key, p in prev.items():
        if key not in out:
            p2 = dict(p)
            p2["blend_w_current"] = 0.0
            out[key] = p2
    return out


def league_averages(table: dict[str, dict[str, float]]) -> dict[str, float]:
    if not table:
        return {"ppg": LEAGUE_PPG}
    vals = [v.get("league_ppg") for v in table.values() if v.get("league_ppg")]
    return {"ppg": round(sum(vals) / len(vals), 2) if vals else LEAGUE_PPG}


def match_team(team_name: str, table: dict[str, dict[str, float]]) -> dict[str, float]:
    nt = norm_team(team_name)
    if nt in table:
        return table[nt]
    for key, val in table.items():
        if key in nt or nt in key:
            return val
    nick = team_name.split()[-1] if team_name else ""
    nk = norm_team(nick)
    for key, val in table.items():
        if nk and key.endswith(nk):
            return val
    return {
        "team": team_name,
        "off": 0.0,
        "dfn": 0.0,
        "gp": 0.0,
        "league_ppg": LEAGUE_PPG,
        "blend_w_current": 0.0,
    }


def build_game_talent(
    home: str,
    away: str,
    ratings: dict[str, dict[str, float]],
    league: dict[str, float],
) -> dict[str, Any]:
    h = match_team(home, ratings)
    a = match_team(away, ratings)
    return {
        "home": home,
        "away": away,
        "home_r": h,
        "away_r": a,
        "league_ppg": league.get("ppg", LEAGUE_PPG),
        "notes": {
            "home_off": h.get("off"), "home_def": h.get("dfn"),
            "away_off": a.get("off"), "away_def": a.get("dfn"),
            "home_gp": h.get("gp"), "away_gp": a.get("gp"),
            "home_blend_w": h.get("blend_w_current"), "away_blend_w": a.get("blend_w_current"),
        },
    }
