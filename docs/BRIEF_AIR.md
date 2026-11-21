# Brief for the MacBook Air M4 agent: terrain, fill step and scoring

Read `docs/BRIEF.md` first. You own the shared inputs, the fast fill model, and the final scoring. The Pro agent is blocked on your shared files, so those come first.

## Why this is on your machine

Everything here is CPU work on small graphs and one 512 x 512 grid. The Air also stays with the human for questions and slides.

## Job 1: shared inputs (by Sat 15:30)

Write the files listed in the shared contract in `docs/BRIEF.md`. Read `data/README.md` before touching the terrain.

- **Terrain.** Raise building cells into walls using the `buildings` mask, so the interpolated pits under footprints cannot hold water. Check the result by eye and note anything odd under the railway viaducts.
- **Receptors.** 50 to 200 cells on open ground next to building edges that face a street, spread across the domain, plus the mapped entrances. Include and label the documented flood site: Blackfriars Road by Southwark station, where a burst main flooded the road. Its exact cell is not established; choose the lowest stretch of Blackfriars Road near the station and record how you chose it.
- **Storms.** A 64-storm pilot and a main set of about 1,000, with fixed seeds, drawn from the stated ranges. Stratify by total depth so the set is not padded with storms that are trivially dry or trivially wet. Storms must differ in timing as well as depth, because timing is what the simulator feels and the fill model does not.

## Job 2: the volume bound on real terrain (by Sat 16:30)

For each receptor, compute the rain depth below which it cannot flood: all rain that can reach it, over its whole upstream catchment, cannot fill the ground around it to the threshold.

Report in `status/air.md`:

- the bound for every receptor, and how the bounds spread across the 10 to 120 mm storm range;
- the fraction of storm-receptor pairs the bound decides, and the fraction of whole storms it decides for every receptor at once.

If the bounds are all near zero or all above 120 mm, the screen decides nothing useful. Say so plainly; that is a finding.

## Job 3: batched partial fill (by Sat 19:00)

Build the fill model for a storm that stops partway: given a rain volume, water fills dips, overflows at spill points into neighbours, and merges ponds.

- **Do the terrain work once.** Build the depression tree for the real tile (priority-flood and the code in `prior/test1_minmax.py` are the starting point).
- **Then evaluate all storms together.** A bottom-up sweep over the tree, vectorised over storms, is enough. Do not spend time on an elegant parallel formulation here.
- **Oracle.** If Barnes's Fill-Spill-Merge code builds quickly, use it. Otherwise compare against the settled state of the JAX solver on synthetic streets from `prior/floodlab.py`.
- **Gate:** flooded-or-not decisions match the oracle in at least 98% of cases. If not by 19:00, stop, write up why, and fall back to the volume bound as the only screen.

Also time a plain single-threaded version. If the vectorised or parallel version is slower, report that; it is expected at this size and it is an honest result.

## Job 4: the band and the pilot (Sat 20:00 to 22:00)

When `results/pro/bruteforce_pilot.npz` exists:

- Compare fill depth with the simulator's peak depth at every receptor for all 64 storms.
- Set a two-sided band around the threshold from that comparison. Water flowing past a receptor on a slope is a miss the fill model cannot see, so check the dry side as carefully as the wet side.
- Report the fraction of pilot storms with no receptor in the band. This predicts the speedup. Write it at the top of `status/air.md`.

The band is set on the pilot and tested on the main set. Do not re-tune it on the main set.

## Job 5: scoring (Sun 07:00 to 09:00)

With the main brute-force results:

- **Misses:** storm-receptor cases the cascade called dry that the simulator flooded. Diagnose every one.
- **Storms skipped** and the end-to-end wall-clock of the cascade, including the fill step and the simulator runs on undecided storms.
- **Speedup** against the brute-force wall-clock on the same machine.
- **The documented site:** the smallest storm that floods it, and how that compares with the record.

## Two literature checks (fit them in before Sat 19:00)

Both come from memory and affect what we may claim as new. Find the primary sources and write two or three lines each in `status/air.md`.

1. Rapid fill-and-spill flood models already in UK practice (recalled as HR Wallingford's RFSM).
2. Parallel priority-flood or parallel depression-filling algorithms (recalled as work by Barnes).

## What you are not doing

- The time-stepping solver and the overnight run belong to the Pro agent.
- No scan map, no regrading, no gradient storm search.
