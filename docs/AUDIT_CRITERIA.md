# Audit of the depth-change screen: lines fixed before any solver run

Written by the Pro agent, Saturday 21:05. No solver run of these cases exists yet. Cases: `shared/audit.npz`, built by `fill/audit_make.py` (seed 2026).

## Why

The pool test showed the whole-tile map's rule (no change in critical rain) misses ground that moves a building. The Air found that the stricter rule, "the fill model predicts a depth change of 1 mm or more at some building at this storm", caught 39 of 53 movers, and that 14 of 232 unflagged suspects still moved a building. Those suspects were picked near buildings that had already moved, so 6% is not a rate. This experiment measures the rate on ground chosen at random.

## Design

- **Sample.** The tile is cut into 5 x 5 m blocks; 6,797 have an open centre cell, giving 13,594 what-ifs (each block raised or lowered 5 cm). 3,400 are drawn uniformly at random without replacement. Nothing is excluded.
- **Screen under test.** A what-if is flagged at a storm if the fill model predicts a depth change of 1 mm or more at any receptor more than 7.5 m from the block centre. Otherwise it is dismissed. At 35 mm: 172 flagged, 3,228 dismissed. At 15 mm: 305 flagged, 3,095 dismissed.
- **Runs.** The what-ifs are packed at least 120 m apart into 278 terrains (2 to 18 each, median 14), in sample order. Packed and single runs agreed to 0.2 mm at this spacing (`docs/G_CRITERIA.md`). Plus one unchanged terrain per storm, run on this machine.
- **Storms.** 35 mm net first, then 15 mm net (the control experiment's middle and smallest storms).
- **A mover.** A what-if moves a building if a receptor more than 7.5 m and at most 60 m from its block centre changes peak depth by 1 cm or more against the unchanged run. With 120 m spacing at most one block lies within 60 m of a receptor, so no split runs are needed. A receptor that moves 1 cm with no block within 60 m is reported separately as unattributed.

## Lines, per storm

- **Miss rate of the screen:** movers among dismissed what-ifs. Pass: at most 1% (the failure line already in `docs/G_CRITERIA.md`). Mythos's stricter line for claiming 90% recall is at most 2 misses in about 3,000; that is reported too.
- **Recall:** flagged movers divided by all movers in the sample. Reported with its count; no line, because the number of movers is not known in advance.
- **Precision:** movers among flagged what-ifs. Reported; no line.
- **Reported whatever happens:** every missed mover with its distance to the building and the size of the change, and the 95% interval on the miss rate.

## Limits known in advance

- One tile, 5 cm changes, 5 x 5 m blocks, two triangular storms.
- A dismissed block that moves a building only together with a neighbour 120 m or more away would be attributed to whichever is nearer; the packed-run check says such interactions are under 0.2 mm.
- Receptors within 7.5 m of a block are not tested, as in the control experiment.
