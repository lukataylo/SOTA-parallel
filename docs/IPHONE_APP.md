# iPhone app: build breakdown for the app agent

**Updated Saturday 19:00. Read in this order:** `docs/app_design/README.md` (screens, look, data sources and build order; it wins wherever it differs from this file), then `docs/IPHONE_APP_REVIEW.md` (why), then this file for the kernel, bundle, golden test and scan-import tasks, which stand. Three things below are superseded:

- **Task 3's screen list** is replaced by the four tabs in the design README (Rain, Ground, Scan, Fix).
- **"No Metal"** applies to this Mac while the solver runs, not to the phone. The splat is drawn with Metal on the device; keep it behind a flag in the simulator.
- **The word list** no longer bans paving and tree recommendations. Use the limits text in the design README. "Safe", "will not flood", a probability for a home, insurance and any number without a source chip stay banned.

You are Agent B. You build the app and nothing else. The science agents (Air, and the Pro session that wrote this) do not touch `app/`; you do not touch `fill/`, `solver/`, `shared/`, `results/` or `status/air.md`, `status/pro.md`. Design source: `docs/mythos/7_premortem_iphone_more_bets.md`, section 2. Read it first. This file turns it into tasks with done-checks.

## What the app is

A phone app that shows, for each of 207 buildings on one 512 m tile around Blackfriars Road, the rainfall at which settled water reaches its door, which few patches of ground decide that number, and what happens when you change or re-measure them. It is the closing demo, not the headline. A recorded video is the deliverable; a live demo is not planned.

## Constraints on this machine

- **The GPU is busy** with solver runs until Sunday 11:00. Use no MLX, no Metal, no GPU jobs. CPU builds and the simulator are fine.
- Xcode 26.6 is installed, with iPhone 17 Pro simulators.
- Everything goes under `app/`. Write progress to `status/app.md`. Commit only those paths.
- Both other agents push to `main` every few minutes. Always `git pull --rebase` before `git push`. Never commit `emulator/`.
- Device signing needs the human. Get everything running in the simulator first; ask for the device only at task 4.

## The kernel you are porting

`fill/sweep.py` (626 lines, numba). `Sweep.from_files()` loads `shared/terrain_512.npz` (`z`, `open`, 512 x 512, 1 m cells) and `shared/receptors.npz` (`rc`, 207 rows of row, col). `Sweep.patch(r, c, dz, rad=2)` returns the critical net rain (mm, `inf` if never) for all 207 receptors after moving a 5 x 5 m patch by `dz` metres. `Sweep.crit(z, changed)` does the same for any set of changed cells, which is what a scan import needs.

The numba functions to port are `_recv`, `_labels_edges`, `_flooded`, `_walks`, `_crit` and the helpers `_crit` calls (lines 52 to 544). The `Sweep` class (lines 545 to 626) builds the base state once; that part stays in Python and is shipped as data.

Reference answers: `results/air/decisive.npz` holds `jobs` (2,132 rows of r, c, dz, rad), `crit_patch` (2,132 x 207 critical depths), `c0` (base) and `PG` (the 261-level rain grid). `fill/sweep_check.py` shows how the Python kernel is scored against it.

## Tasks, in order

Each task has a check. Do not start the next until the check passes. Tasks 1 to 4 are the minimum; stop and record the video once 1 to 5 work.

### 1. C kernel and golden test on the laptop

- `app/kernel/sweep.c`, `sweep.h`: plain C99, no dependencies, no allocation inside the per-patch call. One init function taking the base-state arrays, one `sweep_patch(r, c, dz, rad, out[207])`, one `sweep_cells(idx[], newz[], n, out[207])`.
- `app/kernel/golden_test.c`: loads the bundle from task 2 and runs all 2,132 jobs.
- **Check:** all 441,324 values equal `crit_patch` exactly (both `inf` or equal to the float). Print the mean time per patch. Mythos's kill line: over 200 ms per patch on the device means the port is wrong; on this laptop expect tens of milliseconds.
- Not Swift (bounds checks, reference counting) and not Metal (the sweep is serial).

### 2. Bundle writer

- `app/tools/make_bundle.py`: writes one flat little-endian binary plus a small JSON index into `app/bundle/`. Run with `uv run --with numpy --with numba python app/tools/make_bundle.py`.
- Contents: terrain `z`, `open`, receptors, `PG`, every array in `Sweep._base` with its dtype and length, base critical depths `c0`, and the golden jobs and answers for the on-device self-test.
- Per building: the three patches that move it most, with distance and response per cm. Derive these from `results/air/decisive.npz` (`crit_patch` minus `c0`).
- Solver maps for three storms: `results/air/p1_chunks/base.npz` holds peak depth at the 207 receptors for net rain 15, 35 and 70 mm. Label them "2D solver, precomputed".
- **Check:** the C golden test in task 1 reads only this bundle, not the `.npz` files.

### 3. Swift shell in the simulator

- `app/FloodPatch/` Xcode project, SwiftUI, C kernel through a bridging header, bundle as a resource.
- Screen 1, **Map:** the tile, buildings coloured by base critical rainfall, labelled "settled-water model".
- Screen 2, **Building card:** critical rainfall, the three deciding patches with distances, and the precomputed solver depths.
- Screen 3, **What-if:** tap a patch, slide plus or minus 10 cm, the number updates live with the milliseconds shown. Any other building whose critical rainfall falls turns red.
- **Check:** builds and runs with `xcodebuild` for the iPhone 17 Pro simulator; a self-test button runs 100 golden jobs and reports 100 of 100 identical.

### 4. On-device timing

- Ask the human to sign and install. Run the self-test and record mean and worst time per what-if in `status/app.md`.
- **Check:** under 200 ms. If not, stop and fix the port before anything else.

### 5. Scan import from a file

- Input: a point cloud or mesh file exported from a scanning app, plus a position the user sets by dragging the scan on the map.
- Vertical tie: one offset per scan, the median of map minus scan over flat open cells. No absolute heights are used.
- Each covered cell takes the height of the surface covering most of it; the changed cells go to `sweep_cells`.
- Write and test this pipeline on the laptop first (`app/tools/scan_to_cells.py`), then call the same logic from the app.
- **Check:** a synthetic scan that lowers a known patch by 5 cm reproduces `Sweep.patch` for that patch.
- Say on screen that the scan was imported from another app.

### 6 to 8. Stretch, only if 1 to 5 ran on a device

In-app ARKit capture, guided targets ("walk 14 m left to the dropped kerb"), AR water-level plane. Mythos cut the AR overlay; do not start it without the human asking.

## A first real scan, and what it tells you

The human made a Gaussian splat at Southwark station on Saturday evening: `https://scaniverse.com/scan/yqkxnkirl2vkxxfn`. The splat file is in the repository at `data/scans/southwark_station/gaussians.spz` (4.5 MB, SPZ version 3, 184,894 Gaussians), with its format notes in the README beside it.

- Its tagged position (51.50386, -0.10439; OSGB 531663.6, 180028.1) is row 270, column 298 of the tile, on open ground at 3.61 m, 8 m from receptor 204.
- It is a night capture and the preview is heavily blurred. Half the Gaussians lie more than about 30 m from the centre, and no single 0.4 to 0.5 m slab holds more than 12% of the nearby points, so there is no clean ground plane to fit.
- **Consequence for task 5:** do not build the import around splat centres. Ask the human for a LiDAR mesh or point-cloud export (Scaniverse mesh mode, exported as PLY or OBJ) of a kerb and a doorstep in daylight, with a tape-measure reading, as Mythos's dry run specifies.

## Words the app must not use

"Safe", "will not flood", a probability or return period for a home, "raise this kerb", anything about insurance, sewers, rivers or groundwater, any single number without a range, any claim that trees or grass help. Label every fill-model number "settled water". The full list is in section 2d of the Mythos note.

## If time runs out

Compile the same C kernel to WebAssembly for a web page with screens 1 to 3, and pair it with a video of the scan. The golden test and bundle carry over unchanged.
