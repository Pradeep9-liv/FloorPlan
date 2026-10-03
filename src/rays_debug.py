import sys, json, os
import numpy as np
from room_height import get_cloud
import dims

folder = sys.argv[1]
name = os.path.basename(os.path.dirname(os.path.normpath(folder)))
steps = [30, 31, 37]
DEG, FLOOR_Y, CELL = 28.5, -1.494, 0.05
CASES = [(7, 0), (7, 1), (6, 1), (3, 0)]    # (room id in the s30 plan, axis)

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
    return occ.sum(axis=2) >= 9, amin * CELL, bmin * CELL

with open(os.path.join("out", f"{name}_s30", "plan.json")) as f:
    rooms30 = {r["id"]: r for r in json.load(f)["rooms"]}
maps = {s: prepare(get_cloud(folder, s)) for s in steps}
offs = np.arange(-0.5, 0.51, 0.1)

for rid, axis in CASES:
    p0 = rooms30[rid]["centre_m"]
    print(f"\nroom {rid}, axis {'ab'[axis]}: first-hit distance (m) for 11 parallel rays, '--' = none within 12 m")
    for sign in (-1, +1):
        for s in steps:
            walls, a0, b0 = maps[s]
            row = []
            for off in offs:
                st = list(p0)
                st[1 - axis] += off
                d = dims._first_hit(walls, a0, b0, CELL, st, axis, sign)
                row.append(" -- " if d is None else f"{d:4.2f}")
            print(f"  side {'-' if sign < 0 else '+'} s{s}: " + " ".join(row))