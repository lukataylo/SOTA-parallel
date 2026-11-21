# Experiments for the MacBook Pro, Saturday evening

**Updated 18:12.** Steps 1, 3 and 4 are done (the Air ran 3 and 4 when its GPU freed up). **Run next:** `uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py full` (the Air is running the same list in reverse; about 3 hours shared), then step 2 (friction).

Run these in order. Each is one command from the repository root, is resumable, and writes into `results/`. Commit and push results after each step, and put the numbers in `status/pro.md`. Background and pass lines: `docs/P1_CRITERIA.md`, `docs/BETS.md`, `docs/ABSORPTION.md`, `docs/mythos/6_decisions_after_research.md`.

The Air is saturated (GPU and CPU), so the Pro is now the faster route for everything on the GPU.

## 1. Control experiment, far half (most important; about 1.5 h)

```
uv run --with mlx --with numpy python fill/p1_run.py reverse
```

- **What it is:** 120 ground patches (60 the fill model says do nothing, 30 random, 30 it says matter), each at three storms. The Air runs the same list from the front; you run it from the back, and the two meet. Chunk files go to `results/air/p1_chunks/` (same names from both machines, so pull before you start and commit as you go).
- **Why it comes first:** Mythos's decision after the literature review is to lead the entry with this experiment. It does not depend on the terrain-error model, has controls, and its pass lines were committed before any run.
- **Do not score it yourself;** the Air will, against `docs/P1_CRITERIA.md`.

## 2. Friction sensitivity (about 15 min)

```
uv run --with mlx --with numpy python fill/p1_friction_run.py
```

- **What it is:** 30 of the control patches (10 per class) at the middle storm, with Manning's n raised from 0.015 to 0.02, the Environment Agency's 2013 value for tarmac. 31 runs, into `results/pro/p1_friction/`.
- **What it answers:** whether the controlling ground stays the same when friction changes. A judge can otherwise ask whether friction matters more than centimetres.

## 3. Do-no-harm design check (about 4 min)

```
uv run --with mlx --with numpy python fill/bet3_verify_run.py
```

- **What it is:** the fill model's best harm-free set of five 5 cm patches, and the naive set chosen by benefit alone, each at three storms. 9 runs, into `results/pro/bet3_verify.npz`. The script prints how many buildings fall or rise by 1 cm in each.
- **Pass line (from `docs/BETS.md`):** at least 60% of predicted beneficiaries drop by 1 cm or more, and no receptor rises by 1 cm, for the harm-free design.

## 4. Measure-where-it-matters pilot (about 35 min) — go

```
uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py pilot
```

- **What it is:** 8 terrains with survey error, each run up a ladder of 6 rain depths, with and without the chosen 1% of ground "measured". 96 runs, into `results/pro/bet1_pilot/`.
- **Cleared to run as written.** The correlation-length tests are done: 5 cm error over 3 m is kept, labelled as the kerb-and-threshold-scale scenario.
- **Pass line:** the spread of critical rainfall with the chosen ground known is at most 75% of the spread with nothing known.

## 5. Later tonight, once the Air publishes the cases

- **Absorption go/no-go (E1):** 144 runs with the new absorbing-ground solver (`solver/flood_sink.py`). Case file and runner will appear in `shared/` and `fill/`; `status/air.md` will say when.
- **Measure-where-it-matters, full run:** `fill/bet1_solver_run.py full` (1,080 runs, about 6 h), only if the pilot passes.

## Not to run

- The 1,000-storm brute-force ensemble.
- More work on the moving-water correction, non-triangular storms, or anything at 2 m resolution.
- No new solver runs after Sunday 11:00.

## Notes on the solver

- `solver/flood_sink.py` is a new file written on the Air. It leaves `solver/flood.py` untouched and is bit-identical to it with sinks off (checked on a 128 x 128 crop only). If you change `solver/flood.py`, say so in `status/pro.md`, because the sink file copies its step.
- The `emulator/` directory was added by another session; it is not part of this plan.
