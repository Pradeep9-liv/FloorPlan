# Fix declaration v2

## 1. Worst gate

Repeatability on single_scan_with_ceiling, default density (~320 frames/subset,
steps 30/31/37), fix v1: 4 of 10 dimensions within tolerance, worst spread 1.68 m.

## 2. Root cause and evidence

(a) Sparse sampling leaves holes in the wall map that differ per subset: the same
ray hits a wall at 1.05-1.10 m in two runs and passes through to 4.85 m in the
third (room 7, side b-). With ~900 frames/subset the worst spread falls from
1.68 m to 9.6 cm.
(b) Median over the 11 parallel rays flips when the bundle straddles two surfaces
of similar size (room 6, side b+: 5 vs 6 rays at 0.80 m, the rest at 2.45 m;
median 1.80 m vs 0.80 m).
Not claimed: the cause of the remaining 2-10 cm spreads (suspected wall layering).

## 3. Fix and predicted number

Default budget ~900 frames per capture; take the largest cluster of ray hits
(0.30 m window) and its median. Prediction on steps 10/11/13: 6 of 12 within
tolerance (range 5-8), worst spread < 10 cm. The full gate will still fail.
The cluster rule probably adds little beyond density (density-only baseline,
already measured: 5 of 12, worst spread 9.6 cm).
