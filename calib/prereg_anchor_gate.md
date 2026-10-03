# Pre-registered gate for the camera-height anchor (written before the held-out runs)

Rule: accept a frame's floor estimate only if implied scale s_est = model_h / 1.42
lies in [0.7, 2.0]. Rationale: the model's scale error was 0.88-3.37 on the tuning
folder (mostly 1.0-1.5), and a "floor" less than ~1 m below a handheld phone is
implausible. The thresholds were chosen after seeing single_scan_with_ceiling,
so that folder is in-sample.
Held-out data: single_room and single_scan_floor_only (not looked at for this).
Success: >= 30% of frames accepted AND >= 60% of accepted frames within 20% error.
If met: the photo/video tiers use the anchor, with interval = the held-out 5-95%
error range. If not: the tiers stay unanchored with the wide interval.
Limits: "down" comes from recorded poses (optimistic); one operator, one phone;
LiDAR is the reference, not a tape.
