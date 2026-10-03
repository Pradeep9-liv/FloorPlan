import sys, glob, os, json, warnings
import numpy as np
import cv2
from PIL import Image
from transformers import pipeline
from fuse import load_depth, load_conf
warnings.filterwarnings("ignore")

folder = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 80
name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])
cache = f"cache/mono_ratios_{name}_{n}.json"

if os.path.exists(cache):
    rec = json.load(open(cache))
else:
    frames = sorted(glob.glob(f"cache/frames_{name}/*.jpg"))
    pick = frames[::max(1, len(frames) // n)][:n]
    dfiles = sorted(glob.glob(f"{folder}/depth/*"))
    cfiles = sorted(glob.glob(f"{folder}/confidence/*"))
    pipe = pipeline(task="depth-estimation",
                    model="depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf",
                    device=-1)
    rec = []
    for k, f in enumerate(pick):
        i = int(os.path.basename(f)[:-4])
        if i >= len(dfiles):
            continue
        up = cv2.rotate(cv2.imread(f), cv2.ROTATE_90_CLOCKWISE)
        rgb = Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))
        pred = pipe(rgb)["predicted_depth"].squeeze().cpu().numpy().astype(np.float32)
        pred = cv2.resize(pred, (up.shape[1], up.shape[0]))
        pred = cv2.rotate(pred, cv2.ROTATE_90_COUNTERCLOCKWISE)
        pred = cv2.resize(pred, (256, 192), interpolation=cv2.INTER_AREA)
        dep, cf = load_depth(dfiles[i]), load_conf(cfiles[i])
        m = (cf == 2) & (dep > 0.3) & (dep < 5.0)
        if m.sum() < 2000:
            continue
        ratio = float(np.median(pred[m] / dep[m]))
        shape = float(np.median(np.abs(pred[m] / ratio - dep[m]) / dep[m]))
        rec.append({"frame": i, "ratio": ratio, "shape_err": shape})
        print(f"\r{k + 1}/{len(pick)}", end="")
    print()
    json.dump(rec, open(cache, "w"))

rec.sort(key=lambda x: x["frame"])
r = np.array([x["ratio"] for x in rec])
lr = np.log(r)
q = np.percentile(r, [5, 25, 50, 75, 95])
print(f"\nframes: {len(r)}")
print("scale ratio (model / LiDAR) at 5/25/50/75/95 %: " + "  ".join(f"{v:.2f}" for v in q))
print(f"shape error after fixing scale: median {100 * np.median([x['shape_err'] for x in rec]):.1f}%")

third = len(r) // 3
for k, nm in enumerate(["first third", "middle third", "last third"]):
    seg = r[k * third:(k + 1) * third] if k < 2 else r[2 * third:]
    print(f"  {nm}: median ratio {np.median(seg):.2f}  range {seg.min():.2f} to {seg.max():.2f}")

rng = np.random.default_rng(0)
cov = []
for _ in range(500):
    idx = rng.permutation(len(lr))
    a, b = idx[:len(lr) // 2], idx[len(lr) // 2:]
    lo, hi = np.percentile(lr[a], [5, 95])
    cov.append(((lr[b] >= lo) & (lr[b] <= hi)).mean())
print(f"\nrandom split: 90% interval covers {100 * np.mean(cov):.0f}% of held-out frames (target 90%)")

h = len(lr) // 2
lo, hi = np.percentile(lr[:h], [5, 95])
c2 = ((lr[h:] >= lo) & (lr[h:] <= hi)).mean()
print(f"blocked split (first half of walk -> second half): covers {100 * c2:.0f}%")

lo, hi = q[0], q[4]
print(f"\nunanchored rule: true length = model length / s, s in [{lo:.2f}, {hi:.2f}] "
      f"(point estimate s = {q[2]:.2f})")
print(f"  i.e. relative to the point estimate: {100 * (q[2] / hi - 1):+.0f}% to {100 * (q[2] / lo - 1):+.0f}%")