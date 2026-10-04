# Phone capture to dimensioned floor plan (Applied AI Engineer case study)

Turns a handheld LiDAR capture from an iPhone into a per-room plan: room regions,
ceiling height per room, wall-to-wall dimensions, JSON output and a rendered plan.
Every number carries an interval and a status flag. This README states what works,
what was measured, and what is not done. Nothing below is claimed without a number
from this repo.

## Status at a glance

| Item | Status |
|---|---|
| LiDAR tier (Stray Scanner capture), one command | Works on the 3 sample captures |
| Video tier | NOT BUILT YET (planned fallback: see "Tiers") |
| Photo tier | NOT BUILT YET (planned fallback: see "Tiers") |
| Drift correction + on/off ablation | NOT BUILT YET (poses are used as-is today) |
| Head-to-head vs Polycam/magicplan | NOT DONE (needs an iPhone with LiDAR) |
| Tape/laser ground truth | NONE (sample data came without any) |
| Capture protocol | Written, untested on a real iPhone (`docs/capture_protocol.md`) |

Update this table before submitting. It must match the compliance matrix.

## Requirements

- Python 3.10 or newer, Windows or Linux, 16 GB RAM recommended
- The sample captures (not in the repo): put them under `data/`, for example
  `data/single_room/<random-hash>/` containing `rgb.mp4`, `depth/`, `confidence/`,
  `camera_matrix.csv`, `odometry.csv`, `imu.csv`

## Setup

```
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## One command per capture

```
python src/plan.py data\single_room
```

The command finds the capture folder inside the path you give (the random-hash
folder), picks a frame step from the capture length, and writes to `out/<name>/`:

- `plan.json`: rooms with area, wall-to-wall size, ceiling height, interval, flags
- `rooms.png`: rendered room regions (white = walls)
- `walls.png`: wall map

Optional second argument forces a frame step: `python src/plan.py data\single_room 5`.
Measured cold run time on `single_room` (1,715 frames, 16 GB laptop, CPU only):
about 35 seconds. One capture, one machine.

## Capture route

Stray Scanner (free iOS app, needs a LiDAR iPhone). Step-by-step page for a
non-engineer: `docs/capture_protocol.md`. It has not been tested on a real device yet.

Device matrix (design, not yet measured on iPhones):

| Hardware | Tier |
|---|---|
| iPhone Pro-class (LiDAR) | LiDAR, video, photo |
| iPhone 15 or newer, non-Pro | video, photo |

## How the LiDAR tier works

1. `src/fuse.py`: back-projects depth with per-frame intrinsics (the RGB intrinsics
   divided by 7.5 for the 256x192 depth map), keeps confidence 2 only, places points
   with the recorded poses (OpenCV camera axes, no image rotation: chosen by a voxel-overlap test).
2. `src/walls.py`: finds the floor level and the dominant wall direction (modulo 90 degrees),
   builds a wall map from cells with points at many heights.
3. `src/rooms.py`: splits free floor into rooms (distance transform + watershed,
   marker threshold 0.5 m), measures a ceiling per room, writes `plan.json`.
4. `src/dims.py`: room size as wall-to-wall distance, median of the largest cluster of
   11 parallel rays, each refined to a 1 cm point-density peak.

Ceiling rules: a ceiling is reported only if at least 5,000 points support it.
Otherwise the value is `null` and the interval is a wide prior (2.3 to 3.3 m,
provisional), with the highest point seen as a lower bound for larger regions.
Areas are labelled lower bounds: floor the phone never saw is not counted.
All intervals are marked `provisional_uncalibrated` in the JSON.

## Measured results (all on the sample captures; no tape ground truth)

| What | Result |
|---|---|
| Ceiling height repeatability across frame subsets | spread about 1-2 mm |
| Room dimension repeatability gate, fix v2 (steps 10/11/13) | 5 of 12 within tolerance (FAIL) |
| Same, before the fix loop (bounding box, steps 30/31/37) | 2 of 10 |
| Worst spread, before / after | 1.15 m / 4.7 cm |
| single_room ceiling | none seen (highest point 2.13 m); reported as `null` |

Tolerance used: the larger of 1 cm and 0.5% of the length (my reading of the gate).
All repeatability numbers come from different frame subsets of one scan, not from two
separate captures. Accuracy against a tape is unknown.

## Fix loop (reproduce)

Files are in `fixloop/`: `declaration.md`, `postmortem_v1.md`, `declaration_v2.md`,
`postmortem_v2.md`, `fix.diff`, and the before/after runs.

```
powershell -File fixloop\regenerate.ps1
```

Prints one line per configuration (expected: 2 of 10, 4 of 10, 5 of 12, 5 of 12).
Single run: `python src/repeat.py data\single_scan_with_ceiling 10 11 13`.

## Tiers (calibration done, code pending)

Experiments with a pretrained monocular metric depth model
(Depth Anything V2 Metric Indoor Small, Hugging Face, used for calibration only)
compared against LiDAR on the sample frames:

| Finding | Number |
|---|---|
| Shape error after fixing scale per frame | about 4.4% |
| Raw scale ratio (model / LiDAR), 5-95% | 1.03 to 2.24 |
| Camera height above floor, 3 captures (one operator) | about 1.41-1.46 m median |
| Room-level scale from k photos, gated camera-height anchor, k=8 | 5-95% error about -19% to +3%; 66-86% of draws within 10% |

The planned video and photo tiers use that anchor and report these intervals.
They are expected to miss the photo (+-8%) and video (+-3%) gates; the report says so.
Limits: one operator, one phone, LiDAR used as reference, and the direction of "down"
came from recorded poses, which a photo does not have. Scripts: `src/mono_test.py`,
`src/calibrate_mono.py`, `src/anchor_test.py`, `src/camheight.py`.
Pre-registered gate: `calib/prereg_anchor_gate.md`.

COLMAP (pycolmap) on the sample video registered only 22 of 60 images in the best
model (two fragments), so it is not used.

## Known failure modes

- Rooms the phone never fully scanned: area is a lower bound.
- Room split changes with frame subset for some rooms (room count 7 / 6 / 6).
- Several walls appear as 2-3 layers 12-37 cm apart; cause not established.
- Four room dimensions still spread 3.7-4.7 cm between subsets; cause not established.
- No ceiling in 2 of the 3 sample captures: tell users to point at the ceiling.
- Wall direction is estimated modulo 90 degrees; non-rectangular layouts are measured crudely.
- Mirrors, glass, wet-look surfaces and low light: not tested.

## Repository layout

```
src/            pipeline and experiment scripts
docs/           capture protocol
fixloop/        fix declarations, post-mortems, before/after, regenerate script
calib/          calibration outputs, pre-registration
requirements.txt
```

## Disclosure

- Pretrained model: Depth Anything V2 Metric Indoor Small (Hugging Face), calibration experiments only.
- Libraries: NumPy, SciPy, pandas, OpenCV, Open3D, scikit-image, pycolmap, PyTorch, Transformers.
- AI coding assistance (Claude) was used throughout; design decisions are defended by the author.
- The pipeline runs locally and calls no external service (model weights are downloaded once).
