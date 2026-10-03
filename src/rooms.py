import sys
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from room_height import get_cloud

folder = sys.argv[1]
step = int(sys.argv[2])
marker_m = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5

Wz = np.load("cache/walls.npz")
counts = Wz["counts"]
floor_y = float(Wz["floor_y"])
deg = float(Wz["deg"])
a0, b0, cell = float(Wz["a0"]), float(Wz["b0"]), float(Wz["cell"])
p = get_cloud(folder, step)

t = np.radians(deg)
c, s = np.cos(t), np.sin(t)
a = c * p[:, 0] + s * p[:, 2]
b = -s * p[:, 0] + c * p[:, 2]
ia = np.floor((a - a0) / cell).astype(int)
ib = np.floor((b - b0) / cell).astype(int)
H, Wd = counts.shape
inside = (ia >= 0) & (ia < H) & (ib >= 0) & (ib < Wd)
h = p[:, 1] - floor_y

# 1. Where is open floor?
fl = inside & (np.abs(h) < 0.03)
floor_cnt = np.zeros((H, Wd), int)
np.add.at(floor_cnt, (ia[fl], ib[fl]), 1)
floor_mask = floor_cnt >= 3
floor_mask = cv2.morphologyEx(floor_mask.astype(np.uint8),
                              cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0

# 2. Remove walls, clean up
walls = counts >= 9
walls_d = cv2.dilate(walls.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
free = floor_mask & ~walls_d
free = ndi.binary_opening(free, iterations=1)

# 3. Split into rooms: wide areas are rooms, narrow gaps are doorways
dist = ndi.distance_transform_edt(free) * cell
markers, n_markers = ndi.label(dist > marker_m)
labels = watershed(-dist, markers, mask=free)

# 4. Measure each room
import json

lab_pt = np.zeros(len(p), dtype=int)
lab_pt[inside] = labels[ia[inside], ib[inside]]
MIN_CEIL_POINTS = 5000      # fewer points than this: do not trust the ceiling
PRIOR_LOW, PRIOR_HIGH = 2.3, 3.3   # provisional prior, not calibrated

rooms = []
for k in range(1, labels.max() + 1):
    m = labels == k
    vis = m.sum() * cell * cell
    if vis < 1.5:
        continue
    mf = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE,
                          np.ones((11, 11), np.uint8)) > 0
    mf = ndi.binary_fill_holes(mf) & ~walls_d
    filled = mf.sum() * cell * cell

    hh = h[(lab_pt == k) & (h > 1.8) & (h < 4.0)]
    ceil_h, npts, flag = None, 0, "no_ceiling_seen"
    if len(hh) > 0:
        hist, e = np.histogram(hh, bins=np.arange(1.8, 4.0, 0.01))
        hs = np.convolve(hist, np.ones(3) / 3, mode="same")
        pk = e[np.argmax(hs)] + 0.005
        near = hh[np.abs(hh - pk) < 0.02]
        ceil_h, npts = float(np.median(near)), int(len(near))
        flag = "ok" if npts >= MIN_CEIL_POINTS else "low_confidence"
    ok = flag == "ok"
    top = float(np.percentile(h[lab_pt == k], 99.9))
    cy, cx = ndi.center_of_mass(m)
    rooms.append({
        "id": k,
        "centre_cells": [round(float(cy)), round(float(cx))],
        "area_m2": {"scanned_floor_lower_bound": round(vis, 2),
                    "filled_estimate": round(filled, 2)},
        "area_note": "lower bound only: floor the phone never saw is not counted",
        "ceiling_height_m": round(ceil_h, 3) if ok else None,
        "ceiling_interval_m": ([round(ceil_h - 0.02, 3), round(ceil_h + 0.02, 3)]
                               if ok else [round(max(top, PRIOR_LOW), 2), PRIOR_HIGH]),
        "ceiling_basis": "measured" if ok else "prior_only_ceiling_not_captured",
        "highest_point_seen_m": round(top, 2),
        "ceiling_points": npts,
        "ceiling_flag": flag,
        "interval_status": "provisional_uncalibrated",
    })

out = {"source": folder, "marker_threshold_m": marker_m,
       "wall_rotation_deg": deg, "rooms": rooms}
with open("plan.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"marker threshold = {marker_m} m, rooms kept = {len(rooms)}")
print("\nid  scanned_m2  filled_m2  ceiling_m  interval_m      flag")
for r in rooms:
    c = r["ceiling_height_m"]
    iv = r["ceiling_interval_m"]
    print(f"{r['id']:<3} {r['area_m2']['scanned_floor_lower_bound']:9.2f} "
          f"{r['area_m2']['filled_estimate']:10.2f} "
          f"{('-' if c is None else f'{c:.3f}'):>9}  "
          f"[{iv[0]:.2f}, {iv[1]:.2f}]   {r['ceiling_flag']}")

# 5. Picture
rng = np.random.default_rng(3)
colors = rng.uniform(0.25, 0.95, (labels.max() + 1, 3))
colors[0] = 0
img = colors[labels]
img[walls] = 1.0
plt.figure(figsize=(9, 9))
plt.imshow(img.transpose(1, 0, 2), origin="lower")
for r in rooms:
    plt.text(r["centre_cells"][0], r["centre_cells"][1], str(r["id"]),
             color="black", fontsize=13, ha="center", va="center",
             fontweight="bold")
plt.title("Rooms (white = walls)")
plt.savefig("rooms.png", dpi=120)
plt.close()
print("\nsaved rooms.png and plan.json")