from __future__ import annotations

import math
from typing import Any

from nfl_edge.config import (
    HCA_AWAY_PTS,
    HCA_HOME_PTS,
    LEAGUE_PPG,
    SIGMA_MARGIN,
    SIGMA_TOTAL,
)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def model_game(talent: dict[str, Any], total_line: float | None, spread_line: float | None) -> dict[str, Any]:
    """Additive power ratings: expected points per side =
    league PPG + own offense deviation + opponent defense deviation (+/- home edge).

    talent: {home_r, away_r} with {off, dfn} point deviations vs league; league_ppg.
    """
    h, a = talent["home_r"], talent["away_r"]
    league = float(talent.get("league_ppg") or LEAGUE_PPG)

    pts_home = league + float(h["off"]) + float(a["dfn"]) + HCA_HOME_PTS
    pts_away = league + float(a["off"]) + float(h["dfn"]) - HCA_AWAY_PTS

    margin = pts_home - pts_away
    total = pts_home + pts_away

    out: dict[str, Any] = {
        "pts_home": round(pts_home, 2),
        "pts_away": round(pts_away, 2),
        "exp_margin": round(margin, 2),
        "exp_total": round(total, 2),
        "p_home": norm_cdf(margin / SIGMA_MARGIN),
        "p_away": norm_cdf(-margin / SIGMA_MARGIN),
        "p_over": None,
        "p_under": None,
        "p_home_cover": None,
        "p_away_cover": None,
        "total_line": total_line,
        "spread_line": spread_line,
    }
    if total_line is not None:
        z = (total - float(total_line)) / SIGMA_TOTAL
        out["p_over"] = norm_cdf(z)
        out["p_under"] = 1.0 - norm_cdf(z)
    if spread_line is not None:
        # spread_line = home handicap (e.g. -3.5). Home covers when margin + line > 0.
        zc = (margin + float(spread_line)) / SIGMA_MARGIN
        out["p_home_cover"] = norm_cdf(zc)
        out["p_away_cover"] = 1.0 - norm_cdf(zc)
    return out
