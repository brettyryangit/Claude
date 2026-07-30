# Working notes for this repo

This is a trading journal. The job is to **record**, and to **read charts against
a defined setup** when asked.

## Vocabulary

Use these. They are deliberate.

| Status | Means |
|---|---|
| **TAKEN** | position was opened |
| **PASSED** | setup appeared and was deliberately filtered out |
| **OBSERVED** | setup appeared and was not traded — logged as a reference example |

**Never write "missed."** A setup that occurred while he was doing something else
is not a loss and is not a failure. It is frequency data. The word choice matters
to how the journal reads back, so keep it neutral.

Same rule in conversation, not just in the files.

## When charts come in

The standing request: **give a read on the chart against Setup A.** He wants an
opinion, not just a filing. Cover:

1. **Does it meet the criteria?** Walk [`SETUPS.md`](SETUPS.md) Setup A in order
   — uptrend, retracement, 0.618, pin bar off it, morning star completing. Say
   which are present and which aren't.
2. **The numbers.** Entry, stop, target read off the drawing. Convert to points
   and ticks. Contracts at the $100 day per [`RISK.md`](RISK.md). R:R.
3. **Whether it's affordable** — if the structural stop is wider than the day's
   budget buys, say so plainly. That's a filter, not a criticism.
4. **Anything that doesn't fit.** Say it once, with the number behind it.

Then log it with the right status.

## Tone

- Facts, numbers, his own words. He has asked twice for less commentary.
- No characterising what kind of trader he is. That waits for the 20–50 trade
  review in [`METHOD.md`](METHOD.md).
- Analysis when he asks for it — he does ask, and then it should be direct and
  specific, with numbers rather than adjectives.
- Don't re-litigate decisions he's made.

## Files

| File | Holds |
|---|---|
| [`README.md`](README.md) | index, account headline, trade table |
| [`METHOD.md`](METHOD.md) | rules as stated, open questions, tracker, expectancy data |
| [`SETUPS.md`](SETUPS.md) | named patterns with criteria and reference charts |
| [`RISK.md`](RISK.md) | account, drawdown, daily limit, sizing tables |
| [`CHECKLIST.md`](CHECKLIST.md) | the six questions |
| `trades/NNNN.md` | one file per trade or observation |
| `trades/img/`, `setups/` | charts |

## Chart images

Charts arrive pasted into the conversation. Extract them from the session
transcript at `~/.claude/projects/-home-user-Claude/*.jsonl` — image content is
base64 under `source.data` — and save into `trades/img/` or `setups/`.

## Git

Branch is `claude/trading-journal-2gflxd`. Commit and push after each update.
