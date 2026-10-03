import sys, glob, os, warnings
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from scipy.spatial.transform import Rotation as R
from transformers import pipeline
from fuse import load_depth, load_conf
warnings.filterwarnings("ignore")

folder = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 80
floor_y = float(sys.argv[3]) if len(sys.argv) > 3 else -1.494
ASSUMED_H = 1.42
name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])

odo = pd.read_csv(f"{folder}/odometry.csv", skipinitialspace=True)
frames = sorted(glob.glob(f"cache/frames_{name}/*.jpg"))
pick = frames[::max(1, len(frames) // n)][:n]
dfiles = sorted(glob.glob(f"{folder}/depth/*"))
cfiles = sorted(glob.glob(f"{folder}/confidence/*"))
os.makedirs(f"cache/pred_{name}", exist_ok=True)
pipe = None

def predict(f, i):
    global pipe
    path = f"cache/pred_{name}/{i:06d}.npy"
    if os.path.exists(path):
        return np.load(path)
    if pipe is None:
        pipe = pipeline(task="depth-estimation",
                        model="depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf",
                        device=-1)
    up = cv2.rotate(cv2.imread(f), cv2.ROTATE_90_CLOCKWISE)
    rgb = Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))
    pred = pipe(rgb)["predicted_depth"].squeeze().cpu().numpy().astype(np.float32)
    pred = cv2.resize(pred, (up.shape[1], up.shape[0]))
    pred = cv2.rotate(pred, cv2.ROTATE_90_COUNTERCLOCKWISE)
    pred = cv2.resize(pred, (256, 192), interpolation=cv2.INTER_AREA)
    np.save(path, pred)
    return pred

rows = []
print(f"{'frame':>6} {'true_h':>7} {'model_h':>8} {'s_true':>7} {'s_est':>6} {'error':>7}")
for k, f in enumerate(pick):
    i = int(os.path.basename(f)[:-4])
    if i >= len(dfiles):
        continue
    pred = predict(f, i)
    dep, cf = load_depth(dfiles[i]), load_conf(cfiles[i])
    m = (cf == 2) & (dep > 0.3) & (dep < 5.0)
    if m.sum() < 2000:
        continue
    s_true = float(np.median(pred[m] / dep[m]))
    r = odo.iloc[i]
    true_h = float(r.y - floor_y)
    up_cam = R.from_quat([r.qx, r.qy, r.qz, r.qw]).inv().apply([0.0, 1.0, 0.0])
    fx, fy, cx, cy = r.fx / 7.5, r.fy / 7.5, r.cx / 7.5, r.cy / 7.5
    u, v = np.meshgrid(np.arange(256), np.arange(192))
    Z = pred
    P = np.stack([(u - cx) * Z / fx, (v - cy) * Z / fy, Z], -1).reshape(-1, 3)
    d = -(P @ up_cam)                       # distance below the camera, model units
    d = d[(d > 0.3) & (d < 4.0)]
    if len(d) < 1000:
        continue
    cnt, e = np.histogram(d, bins=np.arange(0.3, 4.0, 0.02))
    sm = np.convolve(cnt, np.ones(3), mode="same")
    kpk = int(np.argmax(sm))
    if sm[kpk] < 0.06 * len(d):
        continue                             # no clear floor in view
    c0 = e[kpk] + 0.01
    model_h = float(np.median(d[np.abs(d - c0) < 0.04]))
    s_est = model_h / ASSUMED_H
    err = s_est / s_true - 1
    rows.append((i, true_h, model_h, s_true, s_est, err))
    print(f"{i:>6} {true_h:7.2f} {model_h:8.2f} {s_true:7.2f} {s_est:6.2f} {100 * err:6.0f}%")

a = np.array(rows)
if len(a) == 0:
    sys.exit("no frame had a clear floor")
err = a[:, 5]
s_true = a[:, 3]
base = np.median(s_true) / s_true - 1
print(f"\nframes with a clear floor: {len(a)} of {len(pick)}")
for nm, x in (("anchored (floor height / 1.42 m)", err), ("unanchored (one global ratio)", base)):
    p = np.percentile(x, [5, 25, 50, 75, 95])
    print(f"{nm:<34} error 5/25/50/75/95%: " + "  ".join(f"{100 * v:+.0f}%" for v in p)
          + f"   within 10%: {100 * (np.abs(x) < .10).mean():.0f}%"
          + f"   within 20%: {100 * (np.abs(x) < .20).mean():.0f}%")
print("note: orientation of 'down' comes from recorded poses (optimistic);"
      " 1.42 m and the global ratio were both chosen on these same frames")


print("\n--- plausibility gate (fixed in calib/prereg_anchor_gate.md) ---")
acc = (a[:, 4] >= 0.7) & (a[:, 4] <= 2.0)
print(f"frames accepted by the gate: {acc.sum()} of {len(pick)} ({100 * acc.sum() / len(pick):.0f}%)")
if acc.sum() >= 5:
    e = err[acc]
    p = np.percentile(e, [5, 25, 50, 75, 95])
    print("error among accepted 5/25/50/75/95%: " + "  ".join(f"{100 * v:+.0f}%" for v in p)
          + f"   within 10%: {100 * (np.abs(e) < .10).mean():.0f}%"
          + f"   within 20%: {100 * (np.abs(e) < .20).mean():.0f}%")



print("\n--- room-level scale: median of k accepted frames (gate from the pre-registration) ---")
idx = np.where(acc)[0]
rng = np.random.default_rng(0)
for k in (2, 4, 8):
    if len(idx) < k:
        continue
    res = []
    for _ in range(2000):
        sub = rng.choice(idx, size=k, replace=False)
        res.append(np.median(a[sub, 4]) / np.median(a[sub, 3]) - 1)
    res = np.array(res)
    p = np.percentile(res, [5, 25, 50, 75, 95])
    print(f"k={k} frames: scale error 5/25/50/75/95%: " + "  ".join(f"{100 * v:+.0f}%" for v in p)
          + f"   within 10%: {100 * (np.abs(res) < .10).mean():.0f}%"
          + f"   within 20%: {100 * (np.abs(res) < .20).mean():.0f}%")
print("lengths: true = estimated x (1 + scale error). Frames drawn at random from the whole walk.")