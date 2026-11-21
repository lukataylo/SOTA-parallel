# Mythos: overnight plan (Saturday 21:00)

## 1. Yes, A. The one experiment that matters is the complete solver map at the 35 mm storm

Its headline does not depend on the fill screen being right. It settles D over all ground instead of a sample. Its baseline is the published one: one run per cell (arXiv 2311.00420).

**Specification**

| Item | Choice |
|---|---|
| Blocks | The pool test's 5 x 5 m grid. Every block with open ground; change open cells only. This makes the 276 singles a free check. |
| Change | +5 cm and -5 cm |
| Storm | 35 mm, where all existing validation sits |
| Colours | (row mod 24, column mod 24): 576 colours per sign, 1,152 runs. Use the same definition of 120 m as `pack_check`. |
| Order | Fixed-seed random permutation of colours, so any prefix is a uniform random sample of the tile |
| Split | Pro lowers, Air raises. Either alone is a whole-tile, one-sign map. Each machine writes only to its own results directory. |
| Saved | Per run: 207 receptor peaks and mass balance, to git every 25 runs. Full peak field to local disk. |

**Attribution.** A receptor moves if its peak changes by 1 cm against the unchanged run. Assign it to the nearest block in that run. Two blocks 120 m apart cannot both be within 60 m of one receptor, so the assignment is unique. If the nearest block is more than 60 m away, mark the move "unattributed". A block is a remote mover if it moves a receptor more than 7.5 m away.

**Cheap verification (the confirm stage).** Each machine re-runs its own movers, largest effect first, capped at 100 runs. The first 40 runs are true singles of randomly drawn movers. The rest are repacked 240 m apart, so every mover gets different and sparser neighbours.

**The honest factor is about 12x, not 18x.** Blocks under buildings are not what-ifs. Open ground is about 171,000 cells, so about 13,700 what-ifs in 1,152 runs. Report what-ifs divided by runs, as measured.

**Gate before launch, from the 276 singles.** If no receptor moved 1 cm more than 60 m from its block, launch as specified. Otherwise use period 30 (150 m): 900 colours per sign, 35 mm only, and drop step 3.

**Pass lines.** Commit these to `docs/G_CRITERIA.md` before the first run.

| Line | Slide if it passes | Slide if it fails |
|---|---|---|
| **Integrity:** mass imbalance at most 5e-5 in every run; unchanged run identical at start and end. | (none; required for all the rest) | Drop the bad runs and report coverage. |
| **Packing holds at scale:** at least 95% of the 276 singles keep their verdict; at least 36 of 40 true singles and 90% of repacked movers keep theirs; median difference at most 1 mm; unattributed moves at most 2%. | "Every open 5 x 5 m patch of this street raised and lowered 5 cm in a 2D solver: N what-ifs in 1,152 runs, 12x fewer than one run each. M patches move a building by 1 cm, median D m away." | "Packing at 120 m held for X% of movers. We report the confirmed movers, and where shared ponds break independence." |
| **Screen:** misses at most 1% of dismissed what-ifs; at least 80% of remote movers flagged. Score both dismissal rules as they stand. | "A 10-minute fill model finds R% of the ground that moves a building in the solver and wrongly dismisses m%." | "The fill model misses X% of the ground that matters. The solver map is the product; the fill model is a prior." |

## 2. Fallback that cannot fail

- **Partial map:** because the order is random, 100 finished runs give about 1,200 exact what-ifs drawn uniformly from the tile. That is ten times the control experiment and still gives a miss rate with an interval.
- **Runner dies:** the talk in hand is already complete. It has packing verified at 14.5 what-ifs per run, the exact 13x repair, the 0.71 measurement result, and do-no-harm.
- **Crash protection:** resume by skipping existing files, wrap the runner in a restart loop, and run on mains power with `caffeinate`.

## 3. Schedule

This assumes a 22:00 start. Let the Pro's clean timing finish. Kill the 15 mm pool test.

| Machine | Order | Runs | Hours |
|---|---|---|---|
| Pro | 1. Map, 35 mm, lowered | 576 | 3.3 |
| Pro | 2. Confirm stage | up to 100 | 0.6 |
| Pro | 3. Map, 15 mm, lowered | 576 | 3.3 |
| **Pro total** | | **1,252** | **7.2 of 10** |
| Air | 1. Map, 35 mm, raised | 576 | 4.2 |
| Air | 2. Confirm stage | up to 100 | 0.7 |
| Air | 3. Map, 15 mm, raised, random order, hard stop 07:30 | 300 planned | 2.2 |
| **Air total** | | **976** | **7.1 of 10** |

Step 3 answers "one storm" at the storm where the screen is weakest and the one known miss sits.

**Before leaving, on both machines:** run the colours holding the 9 confirmed movers first. Require at least 8 of 9 detected. Kill and restart once to prove resume works.

## 4. Do not

- **No more pool tests.** The method needs known signs. Report the 35 mm one as a failed shortcut and cite Bettonvil and Kleijnen.
- **No do-no-harm replication.** The runner is unwritten and it leans on fill-model sizes, which failed. Say "one design".
- **No second tile.**
- **No fixing the dismissal rule after seeing the map.** That is tuning.
- **No changes after launch** to spacing, block size, depth or threshold.
- **No "18x", "21,000 runs" or "first".** Say "we did not find".
- **No new work** on absorption, friction or the learned correction.

## 5. Morning, only these

1. Run `map_score.py` and fill in the three slide sentences. This takes about 20 minutes.
2. If the confirm stage is short, run 40 true singles on the Pro. This takes 14 minutes.
3. Make one figure: the tile, movers coloured by sign, lines to the buildings they move, fill-flagged ground overlaid.
4. Make one table: runs, what-ifs, factor, and the screen's hits and misses.
5. The human skims Lowe 2021 and adjusts the "we did not find" wording.
6. No runs after 11:00. Numbers freeze at 11:30.