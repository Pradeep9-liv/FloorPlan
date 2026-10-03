import sys, os
import numpy as np
import open3d as o3d
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fuse import fuse

THETA = np.arctan2(0.479, 0.878)   # room rotation measured earlier (this folder only)

def get_cloud(folder, step):
    os.makedirs("cache", exist_ok=True)
    name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])
    path = f"cache/{name}_s{step}.npy"
    if os.path.exists(path):
        return np.load(path)
    cloud = fuse(folder, step=step, flip=False, rot_k=0)
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(cloud))
    pts = np.asarray(pcd.voxel_down_sample(0.01).points).astype(np.float32)
    np.save(path, pts)
    return pts

def room_report(p, a0, a1, b0, b1, label):
    c, s = np.cos(THETA), np.sin(THETA)
    a = c * p[:, 0] + s * p[:, 2]
    b = -s * p[:, 0] + c * p[:, 2]
    m = (a > a0) & (a < a1) & (b > b0) & (b < b1)
    y = p[m, 1]
    print(f"\n=== {label}: box a[{a0},{a1}] b[{b0},{b1}], {m.sum():,} points ===")
    if m.sum() < 20000:
        print("Too few points in this box. Adjust the box.")
        return
    bins = np.arange(-2.5, 2.5, 0.01)
    h, e = np.histogram(y, bins=bins)
    hs = np.convolve(h, np.ones(3) / 3, mode="same")
    ctr = e[:-1] + 0.005
    peaks = [(hs[i], ctr[i]) for i in range(2, len(hs) - 2)
             if hs[i] > hs[i - 1] and hs[i] >= hs[i + 1] and hs[i] > 0.04 * hs.max()]
    low = [pk for pk in peaks if pk[1] < -1.2]
    if not low:
        print("No floor peak found in this box.")
        return
    fl_strength, fl_y = max(low)
    fl = np.median(y[np.abs(y - fl_y) < 0.02])
    print(f"floor at y = {fl:.3f}")
    print("Surfaces above the floor (height above floor, strength vs floor):")
    for strength, py in sorted([pk for pk in peaks if pk[1] > fl + 1.8],
                               key=lambda t: -t[1]):
        sel = y[np.abs(y - py) < 0.02]
        print(f"  {np.median(sel) - fl:.3f} m   strength {100 * strength / fl_strength:.0f}%")
    plt.figure(figsize=(7, 3))
    plt.plot(ctr, h)
    plt.xlabel("height y (m)")
    plt.title(label)
    plt.savefig(f"room_{label}.png", dpi=110)
    plt.close()

if __name__ == "__main__":
    folder = sys.argv[1]
    step = int(sys.argv[2])
    boxes = {
        "left_room":  (-0.6, 1.1, -1.1, 2.0),
        "right_room": (5.5, 8.8, 0.0, 2.8),
        "top_right":  (6.6, 8.8, 3.0, 6.0),
    }
    p = get_cloud(folder, step)
    for label, box in boxes.items():
        room_report(p, *box, label)