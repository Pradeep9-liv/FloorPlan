import glob, os
import numpy as np
import pandas as pd

FLOOR_Y = {"single_scan_with_ceiling": -1.494,
           "single_room": -1.482,
           "single_scan_floor_only": -1.406}

for name, fy in FLOOR_Y.items():
    hits = glob.glob(os.path.join("data", name, "**", "odometry.csv"), recursive=True)
    if not hits:
        print(name, "not found")
        continue
    odo = pd.read_csv(hits[0], skipinitialspace=True)
    hgt = odo["y"].to_numpy() - fy
    p = np.percentile(hgt, [5, 25, 50, 75, 95])
    print(f"{name:<26} start {hgt[0]:.2f}  5/25/50/75/95%: "
          + "  ".join(f"{v:.2f}" for v in p)
          + f"   min {hgt.min():.2f}  max {hgt.max():.2f}")