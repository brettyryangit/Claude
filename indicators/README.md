# Leading Pin Bar + OBV Divergence + Market Structure

Pine Script v5 indicator (`leading_pinbar_volume_divergence.pine`) for TradingView. Standalone — no dependency on any other indicator.

Two independent signal engines in one script, each with its own settings group:
1. **Pin bar + OBV divergence** (sections 1–3) — reversal/continuation confluence.
2. **Market structure BOS / CHoCH** (sections 4–5) — the BUY/SELL structure-break signal with R:R boxes.

Either can be switched off with its `Enable ...` toggle at the top of its group.

## What it does
Flags a pin bar (hammer / shooting star) only when it lines up with OBV (On-Balance Volume) divergence, optionally confirmed on a second, lower timeframe. The idea: a pin bar alone is noisy; a pin bar backed by volume already diverging from price is a stronger case for an imminent move. It detects both divergence families:

- **Regular divergence (reversal)** — green solid triangle (bull) / red solid triangle (bear), labeled "REG". Price makes a lower low while OBV makes a higher low (bull), or price makes a higher high while OBV makes a lower high (bear). This is the classic "trend is running out of gas" signal.
- **Hidden divergence (continuation)** — teal diamond (bull) / orange diamond (bear), labeled "HID". Price makes a *higher* low while OBV makes a *lower* low (bull), or price makes a *lower* high while OBV makes a *higher* high (bear). This is the "pullback within a trend, trend likely resumes" signal — the opposite use case from regular divergence, so it's kept visually distinct rather than merged into the same marker.
- Each type has its own toggle (Detect regular / Detect hidden) so you can run either in isolation.
- Plain pin bars without any volume confluence still print as small dim circles, so you can see what got filtered out.
- `alertcondition()` is wired separately for all four divergence signals (bull/bear × regular/hidden) plus the two structure signals (Structure BUY / Structure SELL).

## Market structure (BOS / CHoCH) — the BUY/SELL section
This is the part that reproduces the setups you boxed on the 15m chart.

Swing highs and lows are confirmed with a configurable pivot length. The script keeps a running **bias** (bullish / bearish / undetermined) and marks each active level as taken once price breaks it:

- **CHoCH (Change of Character)** — the first break *against* the prevailing structure. Bearish CHoCH = structure was bullish, price breaks the prior swing low → **SELL**. Bullish CHoCH = structure was bearish, price breaks the prior swing high → **BUY**. This is the reversal signal and matches what you marked.
- **BOS (Break of Structure)** — a break in the *same* direction as the existing bias, i.e. trend continuation.
- `Signal on` lets you fire on CHoCH only (default), BOS only, or both.

Every knob is exposed in settings with a tooltip:
- `Swing pivot length` — bars either side required to confirm a swing.
- `Break confirmation` — **Close** (bar must close beyond the level; stricter) vs **Wick** (any touch counts).
- `Min break distance (x ATR)` — price must exceed the level by this much before it counts, to filter marginal breaks.
- `ATR length` — used for both the break buffer and the stop buffer.
- `Require OBV to confirm the structure break` — OBV must break the OBV value recorded *at that same swing point*, not just price. This is the volume confluence applied to structure, and it filters breaks that happen on thin volume.
- `Also require a pin bar within N bars` — optional extra filter tying section 1 into section 4.

An outside bar that takes out both the swing high and the swing low on the same bar is ambiguous, so it consumes both levels, signals nothing, and leaves the bias unchanged.

## Risk / reward boxes
On each structure signal the script draws the two boxes from your screenshot: a red risk box from entry to stop, and a teal reward box from entry to target. Stop is placed beyond the relevant swing plus an ATR buffer; target is `Reward : Risk ratio` × risk. Box width, R:R ratio, and stop buffer are all inputs, and the whole thing can be turned off.

## Verifying signals
Every structure signal drops a label whose tooltip shows the numbers behind it — the exact broken level, the close, bias before and after, current OBV, the OBV value recorded at that swing, and ATR. Hover any signal to audit it rather than taking it on faith. Active (unbroken) swing levels are plotted as lines so you can see what the script is currently watching.

## On-chart display
A status table (toggle: Show status table, default on, corner configurable) has two blocks:

- **Pin bar + OBV:** most recent divergence signal type + its bar time, plus running counts for bull-regular, bull-hidden, bear-regular, bear-hidden.
- **Market structure:** current bias, the active swing high and swing low (with "(taken)" once broken), the last structure event including the exact level broken, its timestamp, and CHoCH/BOS counts.

You don't have to hunt for shapes on the chart — the table always shows live state.

## Inputs
- **Pin Bar:** wick-to-body ratio, max opposite wick, how close the body must sit to the long-wick end.
- **OBV Divergence:** pivot lookback (left/right bars used to confirm a swing high/low), max bars allowed between the two pivots being compared, and toggles for regular vs. hidden detection.
- **Lower-Timeframe Confirmation:** toggle + which lower timeframe to also require the *same* divergence type on (e.g. 15m confirmation on a 1H chart).
- **Display:** show/hide the status table and pick its corner.

## Honesty about "leading"
`ta.pivotlow`/`ta.pivothigh` can only confirm a swing after `pivotRight` bars (or `swingLen` bars, for the structure section) have printed past it — that's unavoidable lag in any pivot-based method, not a bug. The structure section inherits this: a swing high isn't a usable level until `swingLen` bars after it formed, so with the default of 10 the level goes live 10 bars late. Lower it for faster levels and more noise. The signal still fires *before* the larger move plays out (that's the point), but it is not known in real time until `pivotRight` bars after the actual low/high. Lower `pivotRight` for less lag / more false positives, raise it for the opposite trade-off. `request.security` calls for the lower-timeframe check use `lookahead_off`, so they don't repaint into the past, but like any multi-timeframe study the current (unclosed) lower-timeframe bar can still update until it closes.

## On the screenshot you shared
The 1H US Nas 100 chart you posted has no visible time axis and no OBV/volume pane, so I can't read exact timestamps or actual OBV values off it — I can only eyeball candle shapes. All three boxes you drew do sit at local swing lows immediately before an upward leg, which is consistent with your pin-bar-at-the-bottom idea, but I can't confirm real OBV divergence or verify the timing is consistent (e.g. same session time each day) without the underlying data. Load this indicator on that exact chart with OBV visible (Toggle "Volume" pane or add the built-in OBV study alongside it) and it will mark, timestamp, and alert on exactly this pattern going forward instead of relying on eyeballing screenshots.
