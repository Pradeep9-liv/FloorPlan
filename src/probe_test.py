import sys, json, os
import numpy as np
from room_height import get_cloud
import dims

folder = sys.argv[1]
name = os.path.basename(os.path.dirname(os.path.normpath(folder)))
steps = [30, 31, 37]
DEG, FLOOR_Y, CELL = 28.5, -1.494, 0.05

def prepare(p):
    t = np.radians(DEG)
    c, s = np.cos(t), np.sin(t)
    h = p[:, 1] - FLOOR_Y
    keep = (h > 0.3) & (h < 2.0)
    q, hq = p[keep], h[keep]
    a = c * q[:, 0] + s * q[:, 2]
    b = -s * q[:, 0] + c * q[:, 2]
    ia = np.floor(a / CELL).astype(int)
    ib = np.floor(b / CELL).astype(int)
    ih = np.clip(np.floor((hq - 0.3) / 0.1).astype(int), 0, 16)
    amin, bmin = ia.min(), ib.min()
    occ = np.zeros((ia.max() - amin + 1, ib.max() - bmin + 1, 17), bool)
    occ[ia - amin, ib - bmin, ih] = True
    return occ.sum(axis=2) >= 9, amin * CELL, bmin * CELL, a, b

def load(s):
    with open(os.path.join("out", f"{name}_s{s}", "plan.json")) as f:
        return json.load(f)["rooms"]

rooms = {s: load(s) for s in steps}
maps = {s: prepare(get_cloud(folder, s)) for s in steps}

print("A) starting point held FIXED at the s30 room centre")
print(f"{'room':<5}{'dim':<4}" + "".join(f"{'s' + str(s):>8}" for s in steps)
      + "   spread    tol  verdict")
npass = ntot = 0
for r in rooms[30]:
    if r["area_m2"]["scanned_floor_lower_bound"] < 3:
        continue
    p0 = r["centre_m"]
    for axis, dn in ((0, "a"), (1, "b")):
        vals = []
        for s in steps:
            walls, a0, b0, wa, wb = maps[s]
            vals.append(dims.wall_to_wall(walls, a0, b0, CELL, wa, wb, p0, axis))
        ntot += 1
        if any(v is None for v in vals):
            print(f"{r['id']:<5}{dn:<4}  no wall found in at least one run")
            continue
        spread = max(vals) - min(vals)
        tol = max(0.01, 0.005 * float(np.mean(vals)))
        ok = spread <= tol
        npass += ok
        print(f"{r['id']:<5}{dn:<4}" + "".join(f"{v:8.3f}" for v in vals)
              + f"   {spread:6.3f} {tol:6.3f}  {'PASS' if ok else 'FAIL'}")
print(f"\n{npass} of {ntot} dimensions within tolerance (fixed starting point)")

print("\nB) how far each room's centre moves between runs")
for r in rooms[30]:
    if r["area_m2"]["scanned_floor_lower_bound"] < 3:
        continue
    line = f"room {r['id']} (s30 area {r['area_m2']['scanned_floor_lower_bound']:.2f}):"
    for s in (31, 37):
        best = min(rooms[s], key=lambda q: np.hypot(q["centre_m"][0] - r["centre_m"][0],
                                                    q["centre_m"][1] - r["centre_m"][1]))
        d = np.hypot(best["centre_m"][0] - r["centre_m"][0],
                     best["centre_m"][1] - r["centre_m"][1])
        line += f"   s{s}: moved {100 * d:.0f} cm, area {best['area_m2']['scanned_floor_lower_bound']:.2f}"
    print(line)