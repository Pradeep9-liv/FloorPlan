import sys
import numpy as np
import open3d as o3d
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fuse import fuse

folder = sys.argv[1]
step = int(sys.argv[2]) if len(sys.argv) > 2 else 30

cloud = fuse(folder, step=step, flip=False, rot_k=0)
pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(cloud))
p = np.asarray(pcd.voxel_down_sample(0.01).points)

# 1. How many points sit at each height?
bins = np.arange(-2.5, 2.5, 0.02)
h, edges = np.histogram(p[:, 1], bins=bins)
hs = np.convolve(h, np.ones(5) / 5, mode="same")
centres = edges[:-1] + 0.01
peaks = [(hs[i], centres[i]) for i in range(2, len(hs) - 2)
         if hs[i] > hs[i - 1] and hs[i] >= hs[i + 1] and hs[i] > 0.03 * hs.max()]
peaks.sort(reverse=True)
print("HEIGHT PEAKS (y in metres, strongest first):")
for count, y in peaks[:8]:
    print(f"  y = {y:+.2f}   strength {count:,.0f}")

plt.figure(figsize=(8, 4))
plt.plot(centres, h)
plt.xlabel("height y (m)")
plt.ylabel("points")
plt.title("Where the points are, by height")
plt.savefig("heights.png", dpi=120)
plt.close()

# 2. Top-down view of the wall band, turned so walls are straight
theta = np.arctan2(0.479, 0.878)
c, s = np.cos(theta), np.sin(theta)
band = p[(p[:, 1] > -1.2) & (p[:, 1] < 0.5)]
a = c * band[:, 0] + s * band[:, 2]
b = -s * band[:, 0] + c * band[:, 2]
print("\nWALL BAND extents (1st to 99th percentile):")
print(f"  along direction A: {np.percentile(a, 1):.2f} to {np.percentile(a, 99):.2f} m")
print(f"  along direction B: {np.percentile(b, 1):.2f} to {np.percentile(b, 99):.2f} m")

H, xe, ye = np.histogram2d(a, b, bins=[np.arange(a.min(), a.max(), 0.02),
                                      np.arange(b.min(), b.max(), 0.02)])
plt.figure(figsize=(8, 8))
plt.imshow(np.log1p(H.T), origin="lower", cmap="gray",
           extent=[xe[0], xe[-1], ye[0], ye[-1]])
plt.gca().set_aspect("equal")
plt.title("Top-down view (wall band)")
plt.savefig("topdown.png", dpi=120)
plt.close()
print("\nSaved heights.png and topdown.png in the current folder")