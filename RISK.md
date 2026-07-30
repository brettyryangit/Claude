# Risk

## The account

| | |
|---|---|
| Account size | **$50,000** |
| Max drawdown | **$2,000**, **trailing** |
| High-water mark reached | +$700–800 |
| Floor implied by that HWM | ~$48,800 |
| Drawdown remaining | **~$1,200** *(as stated — pending screenshot)* |

The floor tracks the high-water mark and never comes back down. Going +$800 and
back to flat moved the floor from $48,000 to $48,800: $800 of room gone, P&L
unchanged.

## The model

**Max loss for the day: $100.** *(reduced from $200 on 2026-07-30)*

Structure picks the stop. I pick the risk. Contracts are whatever makes the two
meet:

```
contracts = risk budget ÷ (stop in ticks × $ per tick)
```

The stop is never chosen to fit the size. The size is chosen to fit the stop.

**Target shape:** 2:1 minimum. Break-even hit rate at 2:1 is **33%**.

### The day's $100 can be spent as

- one trade at $100
- two trades at $50
- four at $25 — however it gets divided, the day stops at $100

## Sizing table

MGC = **$1.00**/tick · MNQ = **$0.50**/tick

Contracts for the whole day's $100 in one trade, and for splitting it in two:

| Stop | MGC @ $50 | **MGC @ $100** | MNQ @ $50 | **MNQ @ $100** |
|---|---|---|---|---|
| 25 ticks | 2 | **4** | 4 | **8** |
| 50 ticks | 1 | **2** | 2 | **4** |
| 75 ticks | — | **1** | 1 | **2** |
| 100 ticks | — | **1** | 1 | **2** |
| 150 ticks | — | — | — | **1** |
| 200 ticks | — | — | — | **1** |
| 400 ticks | — | — | — | — |

Same dollar risk buys twice as many ticks on MNQ as on MGC. Tick counts don't
transfer between instruments.

## The one number to know

$100 a day against ~$1,200 of remaining drawdown:

| Daily loss limit | Losing days to bust |
|---|---|
| $200 | 6 |
| $150 | 8 |
| **$100** | **12** |

Twelve red days at the full limit. That is the constraint the daily figure runs
against — not the $50,000.

## What has actually been risked

| # | Instrument | Stop | Lots | Risk | vs the new $100 day |
|---|---|---|---|---|---|
| 0001 | MGC | 42 ticks | 3 | $126 | over — would have been 2 lots ($84) |
| 0002 | MNQ | 141.5 ticks | 2 | $141.50 | over — would have been 1 lot ($70.75) |
| 0003 | MGC | 33 ticks | — | not taken | — |
| 0005 | MGC | 69 ticks | 1 | $69 | inside — 69% of the day, $31 left |

0001 and 0002 were both bigger than the new limit allows. 0005 was the first
trade sized to fit inside it — $69 of $100, $31 left over. Running net:
**−$134.90** across three closed trades.

### Win rate needed

At 2:1, break-even is **33%**. The journal computes the actual figure as trades
accumulate — see the expectancy table in [`METHOD.md`](METHOD.md).
