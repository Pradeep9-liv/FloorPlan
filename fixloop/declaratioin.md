# Fix declaration

## 1. Worst-performing gate in my own benchmark

Repeatability (same room, same plan out). Measured on single_scan_with_ceiling,
three frame subsets (steps 30/31/37), same scan: 2 of 10 room dimensions within
tolerance (larger of 1 cm and 0.5% of the length). Worst spread: 1.15 m
(room 3, side b: 3.20 / 3.75 / 2.60 m).

## 2. Root-cause hypothesis and evidence

Primary: room "size" is the bounding box of a floor region, and the region outline
changes with the frame subset (room count 7/6/6, one room's scanned area 8.05 /
6.69 / 7.83 m2). Evidence: ceilings agree to 2 mm and rotation and floor level are
identical in all runs, so the depth data is steady; wall-to-wall distances for the
same rooms agree to 2-5 mm where the wall is a single layer.
Secondary: wall-surface selection. 10 of 16 wall sides show 2-3 layers 12-37 cm
apart; the first-hit rule on a 5 cm grid flips between layers (room 7 side a-:
20 cm jump) and quantizes (1-3 cm).

## 3. Fix and predicted number

Report room size as wall-to-wall distance: median over 11 parallel rays 10 cm
apart, each refined to a 1 cm point-density peak. Prediction: 5 of 10 dimensions
within tolerance (plausible range 4-7); worst spread below 10 cm. The full gate
(every dimension within tolerance) will probably still fail; I will report why.
