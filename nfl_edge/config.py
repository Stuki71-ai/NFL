from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Prefer: NFL_EDGE_ENV -> shared CODE .env (Windows/Linux) -> local repo .env
_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_ENV = _ROOT / ".env"
_ENV_CANDIDATES = [
    Path(p)
    for p in (
        os.environ.get("NFL_EDGE_ENV") or "",
        r"C:\Users\istva\.claude\CODE\.env",
        str(Path.home() / ".claude" / "CODE" / ".env"),
        "/root/.claude/CODE/.env",
        str(_LOCAL_ENV),
    )
    if p
]
for _p in _ENV_CANDIDATES:
    if _p.is_file():
        load_dotenv(_p, override=False)
# Local .env always wins when present (operator overrides)
if _LOCAL_ENV.is_file():
    load_dotenv(_LOCAL_ENV, override=True)

# --- product gates (EDGE family) ---
MIN_ODDS_ML = 1.75
MIN_ODDS_SPREAD = 1.85
MIN_ODDS_TOTAL = 1.85
MIN_EDGE = 0.02  # 2%
MAX_PICKS = 3
MAX_EDGE_SUSPECT = 0.30  # drop absurd edges

# --- NFL model constants (literature values, deliberately NOT fitted) ---
# Margin ~ Normal(exp_margin, SIGMA_MARGIN); total ~ Normal(exp_total, SIGMA_TOTAL).
# Known v1 limitation: a Normal margin under-weights the 3/7 key numbers — accepted;
# the suspect-edge cap and the composer veto are the guards.
SIGMA_MARGIN = 13.2
SIGMA_TOTAL = 13.7
HCA_HOME_PTS = 1.1   # home team scores ~+1.1 at home ...
HCA_AWAY_PTS = 0.9   # ... and allows ~-0.9 (net home edge ~ +2.0)
# Coin-flip: |expected margin| below this -> no ML/spread side (totals still allowed)
COINFLIP_MARGIN = 1.0
# Season-boundary blending: weight_current = games_played / (games_played + K)
# 17-game seasons: half-weight by ~game 6.
RATINGS_BLEND_K = 6
# NFL regresses hard year over year: previous-season rating deviations carry ~55%.
PREV_SEASON_CARRYOVER = 0.55
LEAGUE_PPG = 22.5    # fallback league points per team-game

SPORT_KEY = "americanfootball_nfl"
REGIONS = "us"
MARKETS = "h2h,spreads,totals"
ODDS_FORMAT = "decimal"

# AI - pick composer ladder (EDGE family)
COMPOSER_PRIMARY_MODEL = "claude-opus-5"
COMPOSER_PRIMARY_EFFORT = "max"
COMPOSER_ATTEMPTS_PRIMARY = 3
COMPOSER_FALLBACK_MODEL = "gpt-5.6-sol"
COMPOSER_FALLBACK_EFFORT = "high"
COMPOSER_ATTEMPTS_FALLBACK = 3
SONAR_MODEL = "sonar-pro"  # fallback news engine - NEVER plain "sonar" (operator 2026-08-01)
# News primary: grok-4.5 live web+X search (family-proven), sonar-pro fallback
GROK_NEWS_MODEL = "grok-4.5"
GROK_NEWS_TIMEOUT = 300


def env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()
