import sys, json, os
import numpy as np
from room_height import get_cloud

folder = sys.argv[1]
steps = [30, 31, 37]
DEG, FLOOR_Y, CELL = 28.5, -1.494, 0.05   # identical in all three runs

def prepare(p):
    t = np.radians(DEG)
    c, s = np.cos(t), np.sin(t)
    h = p[:, 1] - FLOOR_Y
    q = p[(h > 0.3) & (h < 2.0)]
    hq = q[:, 1] - FLOOR_Y
    a = c * q[:, 0] + s * q[:, 2]
    b = -s * q[:, 0] + c * q[:, 2]
    ia = np.floor(a / CELL).astype(int)
    ib = np.floor(b / CELL).astype(int)
    ih = np.clip(np.floor((hq - 0.3) / 0.1).astype(int), 0, 16)
    amin, bmin = ia.min(), ib.min()
    occ = np.zeros((ia.max() - amin + 1, ib.max() - bmin + 1, 17), bool)
    occ[ia - amin, ib - bmin, ih] = True
    return occ.sum(axis=2) >= 9, amin, bmin, a, b

def ray(wall, amin, bmin, a, b, p0, axis, sign, max_m=12.0):
    start = np.array(p0, float)
    for k in range(1, int(max_m / CELL)):
        pos = start.copy()
        pos[axis] += sign * k * CELL
        i = int(np.floor(pos[0] / CELL)) - amin
        j = int(np.floor(pos[1] / CELL)) - bmin
        if 0 <= i < wall.shape[0] and 0 <= j < wall.shape[1] and wall[i, j]:
            along = (a, b)[axis]
            lateral = (b, a)[axis]
            sel = (np.abs(along - pos[axis]) < 0.08) & \
                  (np.abs(lateral - start[1 - axis]) < 0.15)
            if sel.sum() < 20:
                return None
            return abs(float(np.median(along[sel])) - start[axis])
    return None

with open(os.path.join("out", "single_scan_with_ceiling_s30", "plan.json")) as f:
    rooms = json.load(f)["rooms"]

data = {}
for s in steps:
    p = get_cloud(folder, s)
    data[s] = prepare(p)

print(f"{'room':<5}{'dir':<5}" + "".join(f"{'s' + str(s):>8}" for s in steps)
      + "   spread    tol  verdict")
npass = ntot = 0
for r in rooms:
    if r["area_m2"]["scanned_floor_lower_bound"] < 3:
        continue
    p0 = r["centre_m"]
    for axis, name in ((0, "a"), (1, "b")):
        widths = []
        for s in steps:
            wall, amin, bmin, a, b = data[s]
            d1 = ray(wall, amin, bmin, a, b, p0, axis, -1)
            d2 = ray(wall, amin, bmin, a, b, p0, axis, +1)
            widths.append(None if d1 is None or d2 is None else d1 + d2)
        if any(w is None for w in widths):
            print(f"{r['id']:<5}{name:<5}  no wall found in one direction")
            ntot += 1
            continue
        spread = max(widths) - min(widths)
        tol = max(0.01, 0.005 * float(np.mean(widths)))
        ok = spread <= tol
        npass += ok
        ntot += 1
        print(f"{r['id']:<5}{name:<5}" + "".join(f"{w:8.3f}" for w in widths)
              + f"   {spread:6.3f} {tol:6.3f}  {'PASS' if ok else 'FAIL'}")
print(f"\n{npass} of {ntot} wall-to-wall distances within tolerance")
print("a ray that escapes through a doorway gives a long distance: read those rows with care")

print("\n--- which side moves, and why ---")

def hist_peaks(vals, center, half=0.4, bw=0.02):
    if len(vals) < 50:
        return []
    edges = np.arange(center - half, center + half + bw, bw)
    h, e = np.histogram(vals, bins=edges)
    hs = np.convolve(h, np.ones(3) / 3, mode="same")
    out = []
    for i in range(1, len(hs) - 1):
        if hs[i] >= hs[i - 1] and hs[i] > hs[i + 1] and hs[i] > 0.2 * hs.max():
            out.append((round(100 * (e[i] + bw / 2 - center)), int(h[i])))
    return out

for r in rooms:
    if r["area_m2"]["scanned_floor_lower_bound"] < 3:
        continue
    p0 = r["centre_m"]
    for axis, name in ((0, "a"), (1, "b")):
        for sign, side in ((-1, "-"), (+1, "+")):
            line = f"room {r['id']} {name}{side}:"
            for s in steps:
                wall, amin, bmin, a, b = data[s]
                d = ray(wall, amin, bmin, a, b, p0, axis, sign)
                if d is None:
                    line += f"  s{s}: none |"
                    continue
                center = p0[axis] + sign * d
                al = (a, b)[axis]
                la = (b, a)[axis]
                sel = (np.abs(al - center) < 0.4) & (np.abs(la - p0[1 - axis]) < 0.15)
                line += f"  s{s}: d={d:.3f} peaks(cm:count)={hist_peaks(al[sel], center)} |"
            print(line)