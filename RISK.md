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

**Max loss for the day: $200.**

Structure picks the stop. I pick the risk. Contracts are whatever makes the two
meet:

```
contracts = risk budget ÷ (stop in ticks × $ per tick)
```

The stop is never chosen to fit the size. The size is chosen to fit the stop.

**Target shape:** 2:1 minimum. Break-even hit rate at 2:1 is **33%**.

### The day's $200 can be spent as

- one trade at $200
- two trades at $100
- four at $50 — however it gets divided, the day stops at $200

## Sizing table

MGC = **$1.00**/tick · MNQ = **$0.50**/tick

| Stop | MGC @ $100 | MGC @ $200 | MNQ @ $100 | MNQ @ $200 |
|---|---|---|---|---|
| 25 ticks | 4 | 8 | 8 | 16 |
| **50 ticks** | 2 | **4** | 4 | 8 |
| 75 ticks | 1 | 2 | 2 | 5 |
| **100 ticks** | **1** | **2** | 2 | 4 |
| 150 ticks | — | 1 | 1 | 2 |
| 200 ticks | — | 1 | 1 | 2 |
| 400 ticks | — | — | — | 1 |

Same dollar risk buys twice as many ticks on MNQ as on MGC. Tick counts don't
transfer between instruments.

## The one number to know

$200 a day against ~$1,200 of remaining drawdown:

| Daily loss limit | Losing days to bust |
|---|---|
| **$200** | **6** |
| $150 | 8 |
| $100 | 12 |

Six red days at the full limit ends it. That is the constraint the daily figure
is really running against — not the $50,000.

## What has actually been risked

| # | Instrument | Stop | Lots | Risk | % of day's $200 |
|---|---|---|---|---|---|
| 0001 | MGC | 42 ticks | 3 | $126 | 63% |
| 0002 | MNQ | 141.5 ticks | 2 | $141.50 | 71% |
| 0003 | MGC | 33 ticks | — | not taken | — |

Both inside the daily limit. Day one closed at **−$132.30**, 66% of the $200.
