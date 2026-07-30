# Risk

## The account

| | |
|---|---|
| Account size | **$50,000** |
| Max drawdown | **$2,000**, **trailing** |
| High-water mark reached | +$700–800 |
| Floor implied by that HWM | ~$48,800 |
| Drawdown remaining | **~$1,200** *(as stated — pending screenshot)* |

### What trailing means here

The floor tracks the high-water mark and **never comes back down**. Every new
equity high ratchets it up permanently.

So giving back profit does not return you to where you started — it costs buffer
for good. Going +$800 and back to flat moved the floor from $48,000 to $48,800:
**$800 of room gone, P&L unchanged.**

That is a real mechanical cost, not a feeling. It is also not an argument for
bailing out of trades early — the lever is size, so a normal loss doesn't eat
the buffer in the first place.

### One figure to check against the screenshot

Journal shows &minus;$132.30 realised. If the HWM was +$800, the floor sits at
$48,800 and the balance should be ~$50,668 — about **$1,868** of room, not
$1,200. Either the HWM was higher than +$800, or there are trades before this
journal started. The screenshot settles which.

## The binding constraint

Not the $50,000. The **$1,200**.

| Risk per trade | % of $50k | % of $1,200 | Consecutive losers to bust |
|---|---|---|---|
| $129 *(trade 0001)* | 0.26% | 10.8% | **9** |
| $141.50 *(trade 0002)* | 0.28% | 11.8% | **8** |
| $100 | 0.20% | 8.3% | 12 |
| **$75** | 0.15% | 6.3% | **16** |
| $60 | 0.12% | 5.0% | 20 |

Risk has been consistent across both trades. It is sized against the balance,
not against the buffer.

## Contract maths

| | $/point | Tick | $/tick |
|---|---|---|---|
| MGC — Micro Gold | $10.00 | 0.10 | **$1.00** |
| MNQ — Micro Nasdaq | $2.00 | 0.25 | **$0.50** |

## Widest stop affordable at 1 contract

Minimum size is 1 contract, so the stop distance is what has to give — not the
size below 1.

| Risk cap | MGC | MNQ |
|---|---|---|
| $60 | 6.0 pts (60 ticks) | 30 pts (120 ticks) |
| **$75** | **7.5 pts (75 ticks)** | **37.5 pts (150 ticks)** |
| $100 | 10.0 pts (100 ticks) | 50 pts (200 ticks) |

If the structural stop — under the swing low, under the entry candle — sits
**wider** than the number above, the trade doesn't qualify at this buffer. That
is a filter, not a compromise between a bad stop and a bad size.

## The two trades re-sized to 1 contract

| # | Stop distance | Risk at 1 contract | Actual size | Actual risk |
|---|---|---|---|---|
| 0001 MGC | 4.20 pts | **$42** | 3 | $129 |
| 0002 MNQ | 35.38 pts | **$71** | 2 | $141.50 |

Both inside a $75 cap at 1 contract.

**0002 exception:** the drawdown before the reversal came was ~150 points —
$300 at 1 contract. That trade was not affordable at any size on this buffer.
