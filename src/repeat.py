import sys, json, os, subprocess
import numpy as np

root = sys.argv[1]
steps = [int(s) for s in sys.argv[2:]] or [30, 31, 37]
name = os.path.basename(os.path.normpath(root))
here = os.path.dirname(os.path.abspath(__file__))

runs = {}
for s in steps:
    r = subprocess.run([sys.executable, os.path.join(here, "plan.py"), root, str(s)])
    if r.returncode != 0:
        sys.exit("plan.py failed")
    with open(os.path.join("out", f"{name}_s{s}", "plan.json")) as f:
        runs[s] = json.load(f)["rooms"]

def nearest(rooms, c):
    best, bd = None, 1e9
    for r in rooms:
        d = np.hypot(r["centre_m"][0] - c[0], r["centre_m"][1] - c[1])
        if d < bd:
            best, bd = r, d
    return best, bd

print("\nrooms per run:", {s: len(runs[s]) for s in steps})
print(f"\n{'room':<6}{'dim':<5}" + "".join(f"{'s' + str(s):>9}" for s in steps)
      + "   spread    tol  verdict")
npass = ntot = 0
for ref in runs[steps[0]]:
    if ref["area_m2"]["scanned_floor_lower_bound"] < 3:
        continue
    matches = []
    for s in steps:
        r, d = nearest(runs[s], ref["centre_m"])
        matches.append(r if d < 0.6 else None)
    if any(m is None for m in matches):
        print(f"room {ref['id']}: not found in every run (room split differs)")
        ntot += 2
        continue
    for i, dim in enumerate(("a", "b")):
        vals = [m["size_m"][i] for m in matches]
        spread = max(vals) - min(vals)
        tol = max(0.01, 0.005 * float(np.mean(vals)))
        ok = spread <= tol
        npass += ok
        ntot += 1
        print(f"{ref['id']:<6}{dim:<5}" + "".join(f"{v:9.3f}" for v in vals)
              + f"   {spread:6.3f} {tol:6.3f}  {'PASS' if ok else 'FAIL'}")
print(f"\n{npass} of {ntot} room dimensions within tolerance")
print("tolerance = larger of 1 cm and 0.5% of the length (my reading of the gate)")