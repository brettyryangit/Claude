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
| 2026-07-30 | **Setup A — the one being looked for:** uptrend, retracement to the 0.618 fib, bullish hammer / pin bar off it, then a morning star reversal. Defined with reference charts in [`SETUPS.md`](SETUPS.md). |
| 2026-07-30 | **Gold respects the 0.618 fib.** That is where the retracement is expected to turn. |
| 2026-07-30 | Stops go **under the swing low or under the entry candle**. |
| 2026-07-30 | Smallest size is 1 contract, so stop distance is the only lever — MGC $1/tick, MNQ $0.50/tick. Not willing to run a 200-tick stop to risk $200 on gold. |
| 2026-07-30 | Exit is normally off liquidity — a swing on liquidity. |
| 2026-07-30 | **Exit rule: "if I get pushed and volume, it stays. If not, it gets cut very quickly."** Needs a definition of *push and volume* and of *quickly*. |
| 2026-07-30 | Stop sizing is worked **off the tick amount** on scalps — a fixed cost, not an invalidation level. Structural stops (swing low / entry candle) are the other mode. |
| 2026-07-30 | **Directional lean, not a hard rule.** Trading is off the 5m and 30m, so HTF bias does not have to be obeyed every trade. But with yesterday bullish, the weekly flipping and the monthly bullish, the lean is long and shorts get a harder look. |
| 2026-07-30 | **Target shape: 2:1 minimum.** Doing it properly rather than clipping small wins. |
| 2026-07-30 | **No typical stop.** Market structure picks the stop; I pick the risk; contracts are sized to make the two meet. |
| 2026-07-30 | **Max loss for the day: $100** (reduced from $200 the same day). Divisible across trades however the day goes. See [`RISK.md`](RISK.md). |

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
6. Does session change the *typical* stop the market hands out — London gold vs
   US gold vs overnight? Not a rule to set, just something the data may show.
7. **Which leg does the fib get anchored to?** On 30 Jul the smaller leg put the
   0.618 at 4,064 and the larger at 4,042 — 22 points apart, the difference
   between an 80-tick stop and a 300-tick one.

## Tracker

One row per trade. No conclusions until there are enough rows.

| # | Instr | Entry TF | Exit reason | State | Moved to BE? | Out early? | Net | If held |
|---|---|---|---|---|---|---|---|---|
| 0001 | MGC | 30m | 5m not driving into 1h close | panicky | no | **yes** | &minus;$19.80 | +$268.20 |
| 0002 | MNQ | 30m | closed by hand 7.75 pts above stop | thought stop was safe | no | **yes** | &minus;$112.50 | &minus;$143.50 |
| 0003 | MGC | 30m | **passed** — wrong side of weekly/monthly | — | — | — | $0 | &minus;$33 |
| 0004 | Gold | 30m | **observed** — textbook Setup A, reference example | — | — | — | $0 | — |
| 0005 | MGC | 15m | tagged at break-even, per the rule | noted risk was high | **yes — ruled beforehand** | no | &minus;$2.60 | *TBC* |

### Expectancy data

The numbers that will eventually test the stated edge. Ticks, not dollars, so
size and outcome stay separable.

**R is the comparable, not ticks.** MGC is $1.00/tick, MNQ is $0.50 — so 110
gold ticks is $110 and 110 Nasdaq ticks is $55. Ticks only compare within one
instrument.

| # | Instr | Session | Lots | Risk | Result | **R** | Ticks risked | Ticks out |
|---|---|---|---|---|---|---|---|---|
| 0001 | MGC | *TBC* | 3 | $126 | &minus;$15 gross | **&minus;0.12R** | 42 | &minus;5 |
| 0002 | MNQ | US | 2 | $141.50 | &minus;$110.50 gross | **&minus;0.78R** | 141.5 | &minus;110.5 |
| 0003 | MGC | *TBC* | — | $33 | not taken | — | 33 | — |
| 0005 | MGC | overnight/Asian | 1 | $69 | $0.00 gross | **0R** | 69 | 0 |

In R: cut at 0.12R on one, 0.78R on the other. Still inconsistent, but the gap
is much smaller than the tick counts made it look.

No characterisation of what kind of trader this is until the data says so. See
the review section below.

### Behaviour counts

**Out early (closed by hand): 2 of 2.** Once it cost $288.00, once it saved $31.00.
**Net so far: &minus;$134.90** over 3 trades, 0 wins, $9.40 in charges.
**Stop moved to break-even: 1 of 3** — 0005, on a condition written before entry, not a fear reaction. Watch for this happening *without* a rule on paper first.
**Plan taken to its own conclusion: 0 of 3.**
**Risk per trade: $129, $141.50, $69** — the first two ~11% of the remaining drawdown, 0005 at 5.75%.
**Passed setups: 1** (deliberate). Saved $33.
**Observed Setup A occurrences: 1.** Counted for frequency, not as a loss.

## Review at 20–50 trades

No conclusions before then. Log the trades, keep the columns filled, and answer
these with data rather than with two samples:

- Hit rate, and average R per trade.
- Is 2:1 actually being achieved, or are targets getting cut short?
- Which setups win — Setup A, liquidity grab, fade, continuation?
- Long vs short: is one side carrying the results?
- Session: does London / US / overnight change the outcome?
- Instrument: gold vs Nasdaq.
- Does the exit rule make or lose money once it has a definition?
- Do the passed trades save more than they cost?
- How often does Setup A actually occur? Frequency tells you how much the edge can be used, separately from how it performs.

Then tailor to whatever the numbers actually show.
