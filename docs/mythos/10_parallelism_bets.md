===== model=claude-mythos-5-2 stop=end_turn in=2836 out=20992 =====

**Decision:** tonight's bet is one you did not list: pack many non-interacting what-ifs into each full-domain run. It needs no new numerics, and it makes A honest. B runs as a gated side bet. C, D, E and the GPU half of F are cut.

Guesses, flagged once: the packing factors, the window speed-up, the flagged what-if count (I assume 4,653 cells x 2 signs = 9,306) and how the 60 "nulls" were sampled.

## 1. Ranking

1. **G (mine): packed what-ifs.** One storm saturates the GPU, so the only way to get more what-ifs per second is more what-ifs per cell-step. Put K patches that cannot interact into one terrain, as in sparse-Jacobian colouring. About 65% to land.
2. **A: screen-then-simulate.** It is the right end-to-end claim, but today it does not hold (below). G makes the audit affordable.
3. **B: nested windows.** "Solve only where the answer changes" is the best criterion-2 line, and it covers dense clusters that G cannot pack. New boundary code, about 40%.
4. **C: kill.** Rain-on-grid wets every cell with thin film, so the active set requires a model change, and MLX gather/scatter will eat the gain. B is C done the easy way.
5. **F: kill the GPU/SIMD repair.** Nobody needs 10 minutes to become 1. Keep only the idle core-scaling run, which is now mandatory (section 3).
6. **D: kill.** A forward-mode pass costs about twice the nonlinear run it approximates, and 5 cm against centimetre-deep flow is not a small perturbation. Free check: is the response to +5 cm and −5 cm antisymmetric in the held runs?
7. **E: kill for terrain.** Raising a patch on a flow path dams water upstream, and your own benefit-only set raised 7 receptors. Keep rain monotonicity as a correctness invariant.

## 2. Top three

**Why A fails today.** The 3.4% bound applies to 166,505 dismissed cells, so it allows about 5,700 missed movers. You have found about 3,100 (67% of 4,653), so the screen could be missing more than it finds. If the 60 nulls were chosen by rule, only the 30 random patches count and the bound is 9.5%. For recall of at least 95% you need at most about 165 missed cells, a miss rate of at most 0.1%. That means zero misses in about 3,000 uniform random dismissed what-ifs: 17 GPU-hours one at a time, about 1 hour packed.

### G: packed what-ifs

- **Claim:** K separated patches in one run give the same per-receptor verdicts as K single runs.
- **Baseline:** one what-if per run, same solver, GPU and grid (20.6 s). A judge accepts it because only the packing changes and you hold the single runs.
- **Build (CPU, now):** a conflict graph from the atlas. Two patches conflict if they share a controlled receptor or catchment, or sit closer than twice the measured footprint. Get the footprint from the held runs: the farthest receptor moved 1 mm per patch. Colour greedily; the number of colours is the number of runs.
- **Check (M4, about 0.7 h):** repack the 120 held patches into about 12 terrains x 3 storms (36 runs, 25 min) and compare with the 360 single runs. Add 20 runs that each plant one confirmed mover among 31 dismissed patches (14 min).
- **Pass line:** at least 30 of 33 flagged patches keep their verdict in every storm, there are no new 1 cm movers among the 87, the median difference in peak change is at most 1 mm, and at least 19 of 20 planted movers are recovered.
- **Fallback:** "5 cm patches interact at X m separation in the solver", a negative result that supports the do-no-harm finding.

### A: audited screen

- **Claim:** the atlas plus solver runs on the flagged set answers "which ground changes move any building in the full solver", with a stated recall.
- **Baseline:** 342,316 single runs, 81 days, labelled "projected, never run". Also show packing-only brute force (about 10,700 runs, 2.5 days, projected), so the screen's contribution is not inflated.
- **Audit (M4, about 1.1 h):** 3,072 uniform random dismissed what-ifs at K = 32, which is 96 runs at 41 s. Split any group where a receptor moves. Use one storm and name it.
- **Flagged set (M3, 21:50 to 06:00):** all packed flagged groups. The budget is about 1,400 runs. If the colouring needs more, run a random 1,000-what-if sample.
- **Pass line:** at most 2 misses in 3,072 lets you state recall of at least 90%; zero misses gives 95%.
- **Fallback:** report the measured miss rate and where the misses sit. I expect them on transient flow paths, which matches the fill model's 66% peak recall.

### B: nested windows

- **Claim:** a 96 to 128 m window driven by the live baseline reproduces full-run receptor changes at several times lower cost per what-if.
- **Baseline:** the same 360 held full runs.
- **Build:** a sub-agent adds a 2-cell halo whose depth and flux are overwritten from the baseline each step. The baseline runs in the same batch, so no boundary data is stored.
- **Cost:** saturation helps here, because cost follows cell count. 64 windows of 128 x 128 plus the baseline is 1.3M cells per step, about 2.4 s per what-if.
- **Gates (M4, about 1 h, hard stop 23:30):**
  1. Throughput is at least 5x per what-if including the baseline.
  2. A window with no patch reproduces the baseline to 1e-6 m.
  3. The 360 held what-ifs agree on at least 95% of verdicts, with error at most 1 mm.
  4. A perturbation monitor 8 cells inside the edge flags every case where an outside receptor moved.
- **Fallback:** "the influence of a 5 cm patch is not contained within W m", with the measured footprint.

## 3. Slide sentences

**A discrepancy to resolve first.** At 2.6 ms, 342,316 what-ifs is 15 core-minutes of repair work, but the tile took 80 process-minutes. End to end you are about 5x slower than the microbenchmark, so a tile-level ratio against "3 hours" is not supported. Run the idle timing with a core-scaling curve at 21:30 on the M3, before the overnight queue (20 min).

**Today:** "An exact local repair answers each terrain what-if in 2.6 ms against 32 ms for a full rebuild in the same compiled code (13x per core, identical answers 20 of 20); all 342,316 what-ifs on the tile ran in 10 minutes on a laptop."

**If G and A land:** "Which 5 cm ground changes anywhere on this tile move a building in the full solver: answered in X GPU-hours against a projected 81 days of single runs, by an exact screen (342,316 to 9,306 what-ifs, 0 of 3,072 dismissed moved, recall at least 95%) and by packing K non-interacting what-ifs per simulation (verdicts match 360 held single runs)."

## 4. Positioning against the imaging team

- **Concede:** they have the larger same-computation speed-up, at larger scale. Do not contest "days to hours", and never show 81 days without the word "projected".
- **Make the judges notice:**
  - Your gain comes from reshaping the question (criterion 2), and the error of each step is measured against runs you hold.
  - You withdrew your own 200x claim.
  - Your lines were committed before the runs.
  - Your negatives are measured: batching gives no gain, pit lumping gives at most 2x, and the fill model's size and sign predictions failed.
  - This is the brief's own flood example.

## 5. Stop tonight

- C, D, E and the GPU repair.
- All JAX work.
- Extensions to floodable buildings, friction and more do-no-harm designs.
- 2 m resolution work and M3/M4 cross-checks.
- Any extension of the ensemble: let it finish at 21:30 and leave it.

Until the G check passes, GPU time goes only to that check.