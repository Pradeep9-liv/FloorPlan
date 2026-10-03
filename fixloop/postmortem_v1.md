# Post-mortem of fix v1 (wall-to-wall rays)

Prediction: 5 of 10 dimensions within tolerance (range 4-7), worst spread < 10 cm.
Result: 4 of 10 (before: 2 of 10). Worst spread 1.68 m (before: 1.15 m).
Pass count was inside the predicted range; the worst-spread prediction was badly wrong.
Wrong assumption: that the moving room centre (start point of the rays) was the
main weakness. Probe test with a fixed start point gave 3 of 10, so it was not.
Achieved: walls that are a single layer now repeat to 2-10 mm.
What I missed: the wall map comes from ~3% of frames and has holes that change
with the subset; and the median over the ray bundle is fragile when the rays
split between two surfaces.
