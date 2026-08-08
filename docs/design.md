# NFL EDGE — Design

> **Operator 2026-08-08: push messaging removed entirely.** Every push alert this document historically described is gone — no OK/NOT-OK, no no-picks, no criticals, no error-workflow pings. Outcomes are silent; state lives in logs, telemetry, the sheet and the delivery surfaces.

**Sibling of:** NBA EDGE / MLB EDGE (architecture), US EDGE (delivery/grader), NIGHT EDGE (quant lineage)  
**Status:** v1 Python service, built dormant 2026-08-01 — GitHub `Stuki71-ai/NFL`

## Thesis

Seventeen-game seasons make possession-level machinery noise: the robust NFL fair-probability
core is **regressed additive power ratings** (points for/against vs league) under a **Normal
score model**. The single dominant non-rating factor — **who plays quarterback** — is
deliberately NOT modeled: it is handled by the news layer (QB status first, from the injury
report and inactives) plus a hard composer veto, because X beat-writers and the official
designations beat any roster model we could maintain.

## Architecture (family-shaped)

```
systemd timer (ET)
    │
    ▼
[1] Slate          Odds API americanfootball_nfl — h2h + spreads + totals
    │              (best price/side, consensus line for spread & total)
    ▼
[2] Ratings        additive deviations per team: off = PF/g − league, def = PA/g − league
    │              (ESPN standings: pointsFor/pointsAgainst totals ÷ (W+L+T))
    │              prev season shrunk ×0.55, current blends in w = gp/(gp+6)
    ▼
[3] Model          expected points per side = league PPG + own off + opp def (±home edge 1.1/0.9)
    │              margin ~ N(m, 13.2) · total ~ N(T, 13.7)   [literature, NOT fitted]
    │              Known v1 limitation: Normal under-weights key numbers 3/7 — accepted
    ▼
[4] Edge calc      edge = model_p · price − 1
    │              floors: ML ≥ 1.75, spread/total ≥ 1.85, min edge 2%, suspect > 30%
    │              coin-flip: |m| < 1.0 → sides blocked (totals stay)
    │              max 1 market/game; rank by win prob, then edge
    ▼
[5] News           grok-4.5 web+X (tool_choice required, zero-search guard):
    │              QB STATUS FIRST, injury designations, inactives, weather → sonar-pro fallback
    ▼
[6] Brain          claude-opus-5 @ max ×3 → gpt-5.6-sol @ high → edge-rank
    │              select ≤3 from shortlist only (exact key bind);
    │              QB VETO: backup starting / starter OUT → skip unless the case survives
    ▼
[7] Delivery       grader claim FIRST (family dedupe) → Whop + email (if enabled)
```


## Markets (v1)

- Moneyline (home/away), floor 1.75
- Point spread at the consensus line, graded as **Asian Handicap** (grader-native), floor 1.85
- Full-game totals at the consensus line, floor 1.85

No props, no halves/quarters, no live, no teasers.

## AI roles

| Role | Model | Job |
|---|---|---|
| Research news | `grok-4.5` web+X → `sonar-pro` fallback | QB status, designations, inactives, weather, one sharp fact per matchup |
| Pick composer | `claude-opus-5` @ max ×3 → `gpt-5.6-sol` @ high → edge-rank | Choose from **shortlist only**; QB veto; never invent prices/teams |
| (Not used for fair odds) | — | Fair probs come from the ratings model, not the LLM |

## Non-goals (v1)

- Key-number (3/7) margin modeling, teaser logic
- QB-value / roster models (news + veto instead)
- Weather as a model term (news + composer judgment instead)
- London 9:30 AM ET games (~5/season — an early slot would trip the one-proposal gate and silence the Sunday slate)
- Bye/rest terms, division/revenge narratives
- Replacing NBA/MLB/US EDGE

## Schedule (America/New_York via systemd timer)

| OnCalendar | ET | Role |
|---|---|---|
| `Sun *-*-* 11:35:00 America/New_York` | Sun 11:35 ET | full Sunday slate — after the ~11:30 inactives leak, before 13:00 kicks |
| `Thu,Mon *-*-* 18:50:00 America/New_York` | Thu + Mon 18:50 ET | primetime — after the 90-min-pre-kick inactives (20:15 kicks) |

One customer proposal per ET day (pipeline gate). Live window: every unstarted game on the
current ET game day. Late-season Saturday slates (December): enable a `Sat 11:35` line at that
point if wanted — noted in OPERATIONS, not preinstalled (it would fire no-picks noise for months).

## Season boundary

September cold start: 0 games → ratings are 55% of last season's deviations (NFL regresses hard
year over year), blending to current form by ~game 6. No manual seasonal maintenance.
