# Dashboard walkthrough

<!-- generated:walkthrough:start -->
Illustrations selected after inspecting saved results; not validation or evidence of representative performance.

## Improvement: 84077 — WORLD WAR 2 GLIDERS ASSTD DESIGNS

Selection: Greatest six-period absolute-error reduction; product-ID ascending tie-break. Display period uses the same extremum, then earliest start.

In Forecast Evaluation choose **Walkthrough example → Improvement**. This applies experiment Training-window experiment, start 2011-11-01, product 84077, no smoothing curves, and four-week/last-week baselines. Manual controls remain available.

Six-period absolute errors: 24,526.50 units for the four-week mean versus 41,239.00 for last-week repetition; reduction +16,712.50 units. The displayed period reduction is +15,090.00 units.

A product-specific example; the selected chart period is distinct from the six-period product score.

Source: [saved predictions](../outputs/training_windows_v1/predictions.csv), matching product/start/model/date keys; fields actual, prediction, spike_threshold and is_spike. Screenshot: [selected view](screenshots/walkthrough-improvement.png).

## Deterioration: 15036 — ASSORTED COLOURS SILK FAN

Selection: Most negative six-period absolute-error reduction; product-ID ascending tie-break. Display period uses the same extremum, then earliest start.

In Forecast Evaluation choose **Walkthrough example → Deterioration**. This applies experiment Training-window experiment, start 2011-07-01, product 15036, no smoothing curves, and four-week/last-week baselines. Manual controls remain available.

Six-period absolute errors: 14,028.50 units for the four-week mean versus 10,752.00 for last-week repetition; reduction -3,276.50 units. The displayed period reduction is -2,069.00 units.

A product-specific example; the selected chart period is distinct from the six-period product score.

Source: [saved predictions](../outputs/training_windows_v1/predictions.csv), matching product/start/model/date keys; fields actual, prediction, spike_threshold and is_spike. Screenshot: [selected view](screenshots/walkthrough-deterioration.png).

## Spike: 22197 — SMALL POPCORN HOLDER

Selection: Largest actual-minus-existing shared threshold; product-ID then date ascending ties.

In Forecast Evaluation choose **Walkthrough example → Spike**. This applies experiment Training-window experiment, start 2011-05-01, product 22197, no smoothing curves, and four-week/last-week baselines. Manual controls remain available.

On 2011-05-27, actual sales were 4,314 units against a 1,200.80-unit historical threshold (excess 3,113.20).

Large observed sales against a strictly preorigin 99th-percentile threshold; cause is unknown and the observation remains in primary scores.

Source: [saved predictions](../outputs/training_windows_v1/predictions.csv), matching product/start/model/date keys; fields actual, prediction, spike_threshold and is_spike. Screenshot: [selected view](screenshots/walkthrough-spike.png).

[Machine-readable selection evidence](../outputs/portfolio/walkthrough_examples.json).
<!-- generated:walkthrough:end -->
