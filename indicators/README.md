# Leading Pin Bar + OBV Divergence Confluence

Pine Script v5 indicator (`leading_pinbar_volume_divergence.pine`) for TradingView. Standalone — no dependency on any other indicator.

## What it does
Flags a pin bar (hammer / shooting star) only when it lines up with OBV (On-Balance Volume) divergence, optionally confirmed on a second, lower timeframe. The idea: a pin bar alone is noisy; a pin bar backed by volume already diverging from price is a stronger case for an imminent move. It detects both divergence families:

- **Regular divergence (reversal)** — green solid triangle (bull) / red solid triangle (bear), labeled "REG". Price makes a lower low while OBV makes a higher low (bull), or price makes a higher high while OBV makes a lower high (bear). This is the classic "trend is running out of gas" signal.
- **Hidden divergence (continuation)** — teal diamond (bull) / orange diamond (bear), labeled "HID". Price makes a *higher* low while OBV makes a *lower* low (bull), or price makes a *lower* high while OBV makes a *higher* high (bear). This is the "pullback within a trend, trend likely resumes" signal — the opposite use case from regular divergence, so it's kept visually distinct rather than merged into the same marker.
- Each type has its own toggle (Detect regular / Detect hidden) so you can run either in isolation.
- Plain pin bars without any volume confluence still print as small dim circles, so you can see what got filtered out.
- `alertcondition()` is wired separately for all four signals (bull/bear x regular/hidden).

## On-chart display
A status table (toggle: Show status table, default on, corner configurable) shows the most recent signal type + its bar time, plus running counts for bull-regular, bull-hidden, bear-regular, bear-hidden since the indicator was added to the chart. That's the "where do I see this" answer — you don't have to hunt for the shape on the chart, the table always shows the latest state.

## Inputs
- **Pin Bar:** wick-to-body ratio, max opposite wick, how close the body must sit to the long-wick end.
- **OBV Divergence:** pivot lookback (left/right bars used to confirm a swing high/low), max bars allowed between the two pivots being compared, and toggles for regular vs. hidden detection.
- **Lower-Timeframe Confirmation:** toggle + which lower timeframe to also require the *same* divergence type on (e.g. 15m confirmation on a 1H chart).
- **Display:** show/hide the status table and pick its corner.

## Honesty about "leading"
`ta.pivotlow`/`ta.pivothigh` can only confirm a swing after `pivotRight` bars have printed past it — that's unavoidable lag in any pivot-based divergence method, not a bug. The signal still fires *before* the larger move plays out (that's the point), but it is not known in real time until `pivotRight` bars after the actual low/high. Lower `pivotRight` for less lag / more false positives, raise it for the opposite trade-off. `request.security` calls for the lower-timeframe check use `lookahead_off`, so they don't repaint into the past, but like any multi-timeframe study the current (unclosed) lower-timeframe bar can still update until it closes.

## On the screenshot you shared
The 1H US Nas 100 chart you posted has no visible time axis and no OBV/volume pane, so I can't read exact timestamps or actual OBV values off it — I can only eyeball candle shapes. All three boxes you drew do sit at local swing lows immediately before an upward leg, which is consistent with your pin-bar-at-the-bottom idea, but I can't confirm real OBV divergence or verify the timing is consistent (e.g. same session time each day) without the underlying data. Load this indicator on that exact chart with OBV visible (Toggle "Volume" pane or add the built-in OBV study alongside it) and it will mark, timestamp, and alert on exactly this pattern going forward instead of relying on eyeballing screenshots.
