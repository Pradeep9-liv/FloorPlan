# Post-mortem of fix v2

Prediction: 6 of 12 dimensions within tolerance (range 5-8), worst spread < 10 cm.
Result: 5 of 12 (5 of 10 measurable; room 3 not found in every run), worst spread 4.7 cm.
Attribution (all on single_scan_with_ceiling, steps 10/11/13 vs 30/31/37):

- Density (~320 to ~900 frames): worst spread 1.68 m to 9.6 cm. Main effect.
- Cluster aggregation: pass count unchanged (5), worst spread 9.6 to 4.7 cm; improved 2b and 7b,
  worsened 7a and 6b. It shifted 7a by ~9.5 cm in every run, so accuracy of that wall is
  unverified (no tape ground truth).
  Why the gate is still failed:

1. Room 3 is split differently across subsets (room segmentation instability).
2. Four dimensions spread 3.7-4.7 cm; cause not established. Suspect: walls with 2-3
   layers 12-37 cm apart seen in the diagnostics. Not tested.
   Limits: all subsets come from one scan; tolerance is my reading of the gate
   (larger of 1 cm and 0.5% of the length).
