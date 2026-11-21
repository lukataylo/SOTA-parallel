# Brief for the MacBook Pro M3 agent: simulator and brute-force baseline

Read `docs/BRIEF.md` first. You own the time-stepping solver, its correctness evidence, and the brute-force run that is both our baseline and our ground truth. Everything the other agent builds is scored against your output, so a wrong solver sinks the entry.

## Why this is on your machine

The M3 Pro has the stronger GPU and will run overnight. The solver is the only part of the entry that benefits from a GPU.

## What to build

A batched local-inertial shallow-water solver in MLX on the Apple GPU, running many storms at once on the 512 x 512 real terrain.

- **Start from `prior/floodlab.py`**, the JAX reference. `scripts/bench_step.py` already holds its core update ported to MLX and checked for mass conservation; use it as the starting point.
- **Per-storm rain.** Each storm in the batch has its own rain-rate time series and drainage loss.
- **Walls and open ground.** Building cells hold no water and pass no flow.
- **Outputs per storm.** Peak depth and final depth at every receptor, plus a mass balance.
- **Time step.** Choose it from a stability condition on the deepest water in the batch, and record how you chose it. An unstable run that looks plausible is the worst outcome here.

MLX on the Apple GPU is 32-bit only. Say so in your status file and show the mass balance is still acceptable.

## Correctness checks, in this order

1. **Agreement with the JAX reference** on a synthetic street from `prior/floodlab.py`: door depths within a stated tolerance.
2. **Mass balance** on the real terrain: rain in equals water stored plus drained plus left through the boundary.
3. **Lake at rest:** still water over uneven ground stays still.
4. **One analytic or published test case** for the local-inertial scheme, if you can set one up within an hour. If not, say so.
5. **Resolution:** run a handful of storms at 1 m and at 2 m and report how often the flooded-or-not decision agrees at the receptors. Below 95%, report resolution dependence as a limitation; do not hide it.

## Gates

| When | What | If it fails |
|---|---|---|
| Sat 16:00 | Throughput on the M3 Pro in cell-steps/s, single storm and batched, written to `status/pro.md` | Under about 300M cell-steps/s after an hour of tuning: plan the main run at 2 m or with fewer storms, and say which |
| Sat 20:00 | Checks 1 to 3 pass on real terrain; check 5 reported | Fix before anything else; the pilot waits for this |
| Sat 22:00 | 64-storm pilot (`shared/storms_pilot.npz`) run, results in `results/pro/bruteforce_pilot.npz` | |
| Sat 23:30 | Main run launched on `shared/storms_main.npz` | |

## The overnight run

- **Size it from your measured throughput** so it finishes by Sunday 07:00 with an hour to spare. Reduce the storm count before reducing resolution, and write down what you chose and why.
- **Make it chunked and resumable.** Write one results file per chunk, with wall-clock per chunk. A crash at 03:00 must not lose the night.
- **Keep the machine awake** (for example with `caffeinate`) and on mains power.
- **Record wall-clock honestly.** This is the baseline time the speedup is measured against, so include everything a user would wait for and exclude nothing.

## What you are not doing

- The fill model, the volume bound, receptors and storm sampling belong to the Air agent.
- No neural surrogates, no gradient search, no scan map. Those are settled as out of scope.

## When you finish early

In order: push solver speed (larger batches, fewer evaluations, compiled steps) and report each gain against the previous figure; then provide a function the Air agent can call to simulate an arbitrary subset of storms, since the cascade needs that on Sunday.
