import sys, glob, os
import numpy as np
import cv2
from PIL import Image
from transformers import pipeline
from fuse import load_depth, load_conf

folder = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])

frames = sorted(glob.glob(f"cache/frames_{name}/*.jpg"))
pick = frames[::max(1, len(frames) // n)][:n]
dfiles = sorted(glob.glob(f"{folder}/depth/*"))
cfiles = sorted(glob.glob(f"{folder}/confidence/*"))

MODEL = "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf"
pipe = pipeline(task="depth-estimation", model=MODEL, device=-1)

print(f"{'frame':>7} {'scale':>7} {'rel.err':>8} {'after scaling':>14} {'within10%':>10}")
scales, errs, errs_s = [], [], []
for f in pick:
    i = int(os.path.basename(f)[:-4])
    if i >= len(dfiles):
        continue
    up = cv2.rotate(cv2.imread(f), cv2.ROTATE_90_CLOCKWISE)
    rgb = Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))
    pred = np.array(pipe(rgb)["predicted_depth"]).squeeze().astype(np.float32)
    pred = cv2.resize(pred, (up.shape[1], up.shape[0]), interpolation=cv2.INTER_LINEAR)
    pred = cv2.rotate(pred, cv2.ROTATE_90_COUNTERCLOCKWISE)
    pred = cv2.resize(pred, (256, 192), interpolation=cv2.INTER_AREA)

    dep = load_depth(dfiles[i])
    cf = load_conf(cfiles[i])
    m = (cf == 2) & (dep > 0.3) & (dep < 5.0)
    if m.sum() < 2000:
        continue
    ratio = float(np.median(pred[m] / dep[m]))
    rel = np.abs(pred[m] - dep[m]) / dep[m]
    rel_s = np.abs(pred[m] / ratio - dep[m]) / dep[m]
    scales.append(ratio)
    errs.append(float(np.median(rel)))
    errs_s.append(float(np.median(rel_s)))
    print(f"{i:>7} {ratio:7.2f} {100 * np.median(rel):7.1f}% "
          f"{100 * np.median(rel_s):13.1f}% {100 * (rel < 0.10).mean():9.0f}%")

print(f"\nframes used: {len(scales)}")
print(f"scale (model / LiDAR): median {np.median(scales):.2f}, "
      f"range {min(scales):.2f} to {max(scales):.2f}")
print(f"median relative error: {100 * np.median(errs):.1f}%   "
      f"after fixing the scale per frame: {100 * np.median(errs_s):.1f}%")