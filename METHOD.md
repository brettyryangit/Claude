# Method

A living file. Rules get added here as I state them, in my own words first, and
only get tightened into something testable once enough trades exist to test them
against. Nothing here is inferred from a single trade.

## Core

**I chase liquidity in gold.** Price goes up one way to take liquidity, then
goes down. Sweep one side, reverse. The trade is taken after the sweep, not into
it.

## Working notes

These are consequences of the above that the journal should track — confirm or
kill them as trades accumulate:

- **The sweep is the signal, not the level.** A level with liquidity resting
  above it is where the trap gets set; the entry is the failure *after* the
  liquidity is taken. Entering before the sweep is a different trade and should
  be logged as one.
- **Stop placement is the open problem.** If the setup is a liquidity grab, the
  stop logically belongs above the wick that took the liquidity — but that wick
  is exactly what makes the stop wide. Trade 0001 put the stop *below* the
  sweep high to keep the risk at $129. That tension will recur on every trade
  this method produces, so it gets tracked explicitly per trade.
- **No follow-through = out.** Stated on 0001 as "not pushing the 5-minute."
  Not yet a rule — needs a number (how many bars, how much movement) before it
  can be followed consistently rather than felt.

## Open questions for me to answer

1. What counts as a liquidity sweep — a wick through a prior high/low, a
   specific level type (session high, prior day, equal highs), or something
   about how it closes?
2. Do I take these only in one direction per session, or both sides?
3. Does session matter? 0001 was ~01:45, thin overnight liquidity.
4. Where does the stop actually belong, given the point above?

## Rules given so far

| Date | Rule, as stated |
|---|---|
| 2026-07-29 | "I chase a little liquidity in gold. I know it goes up one way and goes down. Chase liquidity." |
