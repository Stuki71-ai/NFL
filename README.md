# NFL EDGE

Quantitative **NFL-only** betting edge service. Sibling of **NBA EDGE / MLB EDGE** (architecture) and **US EDGE** (delivery format + GQ Sports grader).

> **STATUS: BUILT DORMANT (2026-08-01).** Season starts ~Sept 10 — the timer is deployed
> **disabled** with the `STOPPED` flag present. Activation is an operator decision at season
> start (see OPERATIONS → Activation).

**GitHub:** https://github.com/Stuki71-ai/NFL  
**Local:** `C:\Users\istva\.claude\CODE\NFL-EDGE`  
**VPS:** `root@vmi…:/root/nfl-edge` — schedule **Sun 11:35 ET** + **Thu/Mon 18:50 ET** (America/New_York timer; NFL-native slots)

## Always-in-sync rule

After **any** code change:

```bash
cd C:\Users\istva\.claude\CODE\NFL-EDGE
python scripts/sync_all.py --push
```

This keeps **Git main ↔ this PC ↔ VPS** aligned (pull → pytest → commit/push → scp deploy → hash verify → units).  
Never leave the VPS on older code than `origin/main`.

| Flag | Meaning |
|---|---|
| (default) | pull, test, deploy, verify, ensure units |
| `--push` | also commit+push local dirty tree first |
| `--no-deploy` | PC/Git only |
| `--no-cron` | deploy code without touching schedule units |
| `--no-pull` | skip `git pull` |

## Core idea

- **Ratings:** additive point deviations — team points for/against per game vs league PPG (ESPN standings; 17-game seasons make anything fancier noise)
- **Year-over-year regression built in:** previous-season deviations **shrunk to 55%**, current season blends in via `gp/(gp+6)` — at 0 games (September) ratings are 55% of last season
- **Fair probs:** Gaussian — margin `Φ(m/13.2)`, totals `Φ((T−line)/13.7)` (literature constants, deliberately **not fitted**); home edge +2.0 net
- **Markets:** Moneyline ≥ 1.75 · **Spread** ≥ 1.85 (graded as Asian Handicap — grader-native) · Totals ≥ 1.85; edge ≥ 2%, ≤ 3 picks, 1/game
- **Coin-flip:** |expected margin| < 1.0 → no ML/spread side (totals stay)
- **News:** **grok-4.5 live web+X** — **QB status first**, injury designations, inactives, weather (`tool_choice: required`, zero-search guard) → **sonar-pro** fallback — never plain sonar
- **Brain:** **claude-opus-5** (effort **max**, 3 tries) → **gpt-5.6-sol** (effort **high**) → **edge-rank**; the composer is the **QB availability veto** (backup QB starting → skip unless the case survives)
- **Delivery:** Whop (sports exp, title stays `US EDGE`) + GQ Sports grader webhook (claim-first) + Gmail if enabled — email subject is `NFL EDGE`

Silence is valid. Honest no-picks → private ntfy `Stuki71-EDGE` title `NFL EDGE @ No picks for today` (operator-only).

## Why these slots

NFL is a weekly sport with three game days. **Sun 11:35 ET** runs after the ~11:30 inactives
leak and before the 13:00 window — one run covers the entire Sunday slate (early, late, SNF).
**Thu/Mon 18:50 ET** run after the 90-minutes-pre-kick inactives for 20:15 primetime.
No daily slot → no weekly no-picks noise on off-days. Known v1 scope cut: the ~5 London
9:30 AM ET games per season are not covered (an early slot would trip the one-proposal-per-day
gate and silence the whole Sunday slate).

## Quick start

```bash
cd C:\Users\istva\.claude\CODE\NFL-EDGE
pip install -r requirements.txt
# credentials: C:\Users\istva\.claude\CODE\.env  (auto-loaded; or local .env / NFL_EDGE_ENV)

python scripts/run_nfl_edge.py --dry-run
python scripts/run_nfl_edge.py --date 2026-01-04 --dry-run   # historical replay (last season)
python scripts/grade_run.py --date YYYY-MM-DD
python -m pytest nfl_edge/tests -q
```

## Layout

```
nfl_edge/          quant pipeline package
scripts/           run_nfl_edge, grade_run, sync_all
docs/              design.md, OPERATIONS.md
deploy/            nfl-edge-live.service / .timer (systemd, America/New_York)
```

See [docs/design.md](docs/design.md) and [docs/OPERATIONS.md](docs/OPERATIONS.md).
