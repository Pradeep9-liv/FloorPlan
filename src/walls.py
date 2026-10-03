import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from room_height import get_cloud

folder = sys.argv[1]
step = int(sys.argv[2])
p = get_cloud(folder, step)

# 1. Floor level: strongest height peak in the lowest 20% of points
bins = np.arange(p[:, 1].min(), p[:, 1].max() + 0.01, 0.01)
h, e = np.histogram(p[:, 1], bins=bins)
low = e[:-1] < np.percentile(p[:, 1], 20)
floor_y = e[:-1][low][np.argmax(h[low])] + 0.005
floor_y = np.median(p[np.abs(p[:, 1] - floor_y) < 0.02, 1])
print(f"floor level y = {floor_y:.3f}")

# 2. Rotation: find the angle where walls line up with the axes
band = p[(p[:, 1] > floor_y + 0.3) & (p[:, 1] < floor_y + 2.0)]
rng = np.random.default_rng(0)
sub = band[rng.permutation(len(band))[:400000]]
hist_bins = np.arange(-40, 40, 0.03)
best_deg, best_score = 0, -1
for deg in np.arange(0, 90, 0.5):
    t = np.radians(deg)
    c, s = np.cos(t), np.sin(t)
    a = c * sub[:, 0] + s * sub[:, 2]
    b = -s * sub[:, 0] + c * sub[:, 2]
    ha, _ = np.histogram(a, bins=hist_bins)
    hb, _ = np.histogram(b, bins=hist_bins)
    score = (ha.astype(float) ** 2).sum() + (hb.astype(float) ** 2).sum()
    if score > best_score:
        best_deg, best_score = deg, score
print(f"room rotation = {best_deg:.1f} degrees")

# 3. Wall map: cells that have points at many different heights
t = np.radians(best_deg)
c, s = np.cos(t), np.sin(t)
a = c * band[:, 0] + s * band[:, 2]
b = -s * band[:, 0] + c * band[:, 2]
cell = 0.05
a0, b0 = a.min(), b.min()
ia = np.floor((a - a0) / cell).astype(int)
ib = np.floor((b - b0) / cell).astype(int)
ih = np.clip(np.floor((band[:, 1] - floor_y - 0.3) / 0.1).astype(int), 0, 16)
occ = np.zeros((ia.max() + 1, ib.max() + 1, 17), dtype=bool)
occ[ia, ib, ih] = True
counts = occ.sum(axis=2)
walls = counts >= 9
print("grid size:", counts.shape, " wall cells:", int(walls.sum()))

np.savez("cache/walls.npz", counts=counts, floor_y=floor_y,
         deg=best_deg, a0=a0, b0=b0, cell=cell)

plt.figure(figsize=(8, 8))
plt.imshow(walls.T, origin="lower", cmap="gray")
plt.title("Wall map (white = tall vertical structure)")
plt.savefig("walls.png", dpi=120)
plt.close()
print("saved walls.png")