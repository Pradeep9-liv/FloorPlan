import sys, glob, os, subprocess
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

def find_capture(root):
    hits = glob.glob(os.path.join(root, "**", "odometry.csv"), recursive=True)
    if not hits:
        sys.exit(f"No odometry.csv found under {root}")
    return os.path.dirname(hits[0])

def main():
    root = sys.argv[1]
    cap = find_capture(root)
    n = len(pd.read_csv(os.path.join(cap, "odometry.csv")))
    step = max(1, n // 320)
    out = os.path.join("out", os.path.basename(os.path.normpath(root)))
    os.makedirs(out, exist_ok=True)
    print(f"capture: {cap}  frames: {n}  step: {step}")

    for script, extra in [("walls.py", [str(step)]),
                          ("rooms.py", [str(step), "0.5"])]:
        r = subprocess.run([sys.executable, os.path.join(HERE, script), cap] + extra)
        if r.returncode != 0:
            sys.exit(f"{script} failed (see the error above)")

    for f in ["plan.json", "rooms.png", "walls.png"]:
        if os.path.exists(f):
            os.replace(f, os.path.join(out, f))
    print("done ->", out)

if __name__ == "__main__":
    main()