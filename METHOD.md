# Method

Rules as I state them. Added over time.

## Core

**I chase liquidity in gold.** Price goes up one way to take liquidity, then
goes down. Sweep one side, reverse. The trade is taken after the sweep.

## Rules given

| Date | Rule, as stated |
|---|---|
| 2026-07-29 | "I chase a little liquidity in gold. I know it goes up one way and goes down. Chase liquidity." |
| 2026-07-29 | Entries are taken off the high timeframe. |
| 2026-07-29 | Setups so far: liquidity grab (0001), morning star reversal (0002). |
| 2026-07-30 | Stops go **under the swing low or under the entry candle**. |
| 2026-07-30 | Smallest size is 1 contract, so stop distance is the only lever — MGC $1/tick, MNQ $0.50/tick. Not willing to run a 200-tick stop to risk $200 on gold. |
| 2026-07-30 | Exit is normally off liquidity — a swing on liquidity. |
| 2026-07-30 | **Exit rule: "if I get pushed and volume, it stays. If not, it gets cut very quickly."** Needs a definition of *push and volume* and of *quickly*. |
| 2026-07-30 | Stop sizing is worked **off the tick amount** on scalps — a fixed cost, not an invalidation level. Structural stops (swing low / entry candle) are the other mode. |
| 2026-07-30 | **Directional lean, not a hard rule.** Trading is off the 5m and 30m, so HTF bias does not have to be obeyed every trade. But with yesterday bullish, the weekly flipping and the monthly bullish, the lean is long and shorts get a harder look. |
| 2026-07-30 | **Stated edge: fading the market — higher contract counts, small wins.** That is where the most profitable trades have historically come from. Not yet evidenced in this journal. |

## Risk

Account and sizing live in [`RISK.md`](RISK.md). $50k account, **$2,000
trailing** drawdown, ~$1,200 remaining.

## Open questions

1. What qualifies as a sweep — a wick through a prior high/low, a particular
   level type (session high, prior day, equal highs), or something about the
   close?
2. One side per session, or both?
3. Does session time matter?
4. Where does the stop belong — above the sweep wick, or sized to the risk?
   Partly answered: under the swing low / entry candle, with size cut to 1
   contract so the structural stop fits the buffer. See [`RISK.md`](RISK.md).
5. If entries are HTF, what timeframe governs the exit? 0001 was entered on the
   HTF and exited on the 5-minute into a 1-hour close.

## Tracker

One row per trade. No conclusions until there are enough rows.

| # | Instr | Entry TF | Exit reason | State | Moved to BE? | Out early? | Net | If held |
|---|---|---|---|---|---|---|---|---|
| 0001 | MGC | 30m | 5m not driving into 1h close | panicky | no | **yes** | &minus;$19.80 | +$268.20 |
| 0002 | MNQ | 30m | closed by hand 7.75 pts above stop | thought stop was safe | no | **yes** | &minus;$112.50 | &minus;$143.50 |
| 0003 | MGC | 30m | **not taken** — wrong side of weekly/monthly | — | — | — | $0 | &minus;$33 |

### Expectancy data

The numbers that will eventually test the stated edge. Ticks, not dollars, so
size and outcome stay separable.

| # | Instr | Lots | Ticks risked | Ticks made/lost | Net | Win? |
|---|---|---|---|---|---|---|
| 0001 | MGC | 3 | 42 | **&minus;5** | &minus;$19.80 | no |
| 0002 | MNQ | 2 | 141.5 | **&minus;110.5** | &minus;$112.50 | no |
| 0003 | MGC | — | 33 | not taken | $0 | — |

Cut at 5 ticks on one and 110.5 on the other. Same behaviour, no consistent
threshold yet.

**What would evidence the fade-with-size edge:** hit rate, average win in ticks,
average loss in ticks, over 20–30 trades. Then expectancy per lot is computable
and the size question answers itself instead of being argued.

### Behaviour counts

**Out early: 2 of 2.** Once it cost $288.00, once it saved $31.00.
**Net so far: &minus;$132.30** over 2 trades, 0 wins, $6.80 in charges.
**Stop moved to break-even: 0 of 2.** **Plan taken to its own conclusion: 0 of 2.**
**Risk per trade: $129, $141.50** — both ~11% of the remaining drawdown.
**Passed setups: 1.** Saved $33.
