# Leading Pin Bar + OBV Divergence Confluence

Pine Script v5 indicator (`leading_pinbar_volume_divergence.pine`) for TradingView. Standalone — no dependency on any other indicator.

## What it does
Flags a pin bar (hammer / shooting star) only when it lines up with OBV (On-Balance Volume) divergence, optionally confirmed on a second, lower timeframe. The idea: a pin bar alone is noisy; a pin bar backed by volume already diverging from price is a stronger case for an imminent reversal.

- **Bullish confluence (green triangle below bar):** bullish pin bar + bullish OBV divergence (price makes a lower low, OBV makes a higher low) on the chart timeframe, plus (optional) the same divergence on a lower timeframe.
- **Bearish confluence (red triangle above bar):** mirror image — bearish pin bar + bearish OBV divergence.
- Plain pin bars without the volume confluence still print as small dim circles, so you can see what got filtered out.
- `alertcondition()` is wired for both signals — set a TradingView alert on "Bullish Pin Bar + OBV Divergence" / "Bearish Pin Bar + OBV Divergence".

## Inputs
- **Pin Bar:** wick-to-body ratio, max opposite wick, how close the body must sit to the long-wick end.
- **OBV Divergence:** pivot lookback (left/right bars used to confirm a swing high/low) and max bars allowed between the two pivots being compared.
- **Lower-Timeframe Confirmation:** toggle + which lower timeframe to also require divergence on (e.g. 15m confirmation on a 1H chart).

## Honesty about "leading"
`ta.pivotlow`/`ta.pivothigh` can only confirm a swing after `pivotRight` bars have printed past it — that's unavoidable lag in any pivot-based divergence method, not a bug. The signal still fires *before* the larger move plays out (that's the point), but it is not known in real time until `pivotRight` bars after the actual low/high. Lower `pivotRight` for less lag / more false positives, raise it for the opposite trade-off. `request.security` calls for the lower-timeframe check use `lookahead_off`, so they don't repaint into the past, but like any multi-timeframe study the current (unclosed) lower-timeframe bar can still update until it closes.

## On the screenshot you shared
The 1H US Nas 100 chart you posted has no visible time axis and no OBV/volume pane, so I can't read exact timestamps or actual OBV values off it — I can only eyeball candle shapes. All three boxes you drew do sit at local swing lows immediately before an upward leg, which is consistent with your pin-bar-at-the-bottom idea, but I can't confirm real OBV divergence or verify the timing is consistent (e.g. same session time each day) without the underlying data. Load this indicator on that exact chart with OBV visible (Toggle "Volume" pane or add the built-in OBV study alongside it) and it will mark, timestamp, and alert on exactly this pattern going forward instead of relying on eyeballing screenshots.
