import sys, os, glob
import cv2

folder = sys.argv[1]
per_sec = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0

path = glob.glob(os.path.join(folder, "*.mp4"))[0]
cap = cv2.VideoCapture(path)
fps = cap.get(cv2.CAP_PROP_FPS)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"video: {os.path.basename(path)}  fps={fps:.2f}  frames={n}  size={w}x{h}")

name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])
out = os.path.join("cache", f"frames_{name}")
os.makedirs(out, exist_ok=True)

every = max(1, int(round(fps / per_sec)))
i = saved = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if i % every == 0:
        cv2.imwrite(os.path.join(out, f"{i:06d}.jpg"), frame)
        saved += 1
    i += 1
print(f"read {i} frames, saved {saved} to {out}")