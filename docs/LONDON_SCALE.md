# London-scale plan: prediction and strategic interventions

Written Saturday 22:30. A plan, not a result. Numbers marked (measured) come from this repo; the rest are estimates to be checked.

## The shape of the problem

- Greater London is about 1,570 km². At 1 m that is 1.6 billion cells, or about **6,000 tiles** of 512 m.
- Everything we have built works one tile at a time. A 5 cm change to the ground reached at most about 75 m in the solver (measured). So tiles with a margin are independent jobs.
- Two tiers, as on the one tile: the fast fill model looks everywhere; the solver judges only where it is worth it.

## Three stages

| Stage | What runs | Cost per tile (measured on a laptop) | All of London | Output |
|---|---|---|---|---|
| 1. Predict | Fill model: critical rain depth for every building | Seconds | About 6,000 core-minutes | A London map of which buildings flood at which rain depth |
| 2. Screen | Fill model: every patch raised and lowered (the local-repair sweep) | 10 minutes on 8 cores | About 8,000 core-hours; a few hundred pounds of cloud CPU | For each at-risk building, the candidate ground that decides it |
| 3. Judge | Solver map, packed 150 m apart, only on tiles where stage 1 finds buildings at risk | 1,800 runs x 17 s = 8.5 GPU-hours per storm | Depends on the share of tiles at risk. At 20% of tiles: about 10,000 GPU-hours on laptop-class GPUs, far fewer on data-centre GPUs | The confirmed ground that moves each building, with direction and size |

Stage 3 is the expensive one and the one worth cutting. Two cuts that need no new science:
- Only run patches within 75 m of an at-risk building. On our tile that is a minority of the ground.
- Stop a tile early once its random-order prefix shows no movers (the run order is already a uniform sample).

## What must change from the hackathon code

1. **Tile edges.** A pond can cross a tile edge. Cut the city along watershed lines of the depression tree, not along a square grid, or run tiles with a halo and keep only the centre. Parallel depression filling of very large terrains is published work (Barnes 2016); use it, do not rebuild it.
2. **Sewers.** We use one constant loss for the whole tile. London needs at least a per-catchment loss, ideally from Thames Water's network model. This is the largest source of error and the data is not open.
3. **Buildings and thresholds.** We used building-edge points and a 10 cm depth. London needs real door thresholds, which is where a phone survey or street imagery comes in.
4. **Rain.** Uniform design storms are fine for ranking ground. Real events need radar rainfall.

## Strategic interventions

The unit of decision is not a patch but a programme: a borough has a budget and a list of streets.

1. From stage 3, each confirmed patch has a list of buildings it helps and buildings it harms.
2. Choose sets of patches that protect the most buildings per square metre changed, with no building made worse by more than 1 cm. This is the do-no-harm search we ran on one tile (5 of 5 helped, 0 harmed, one design).
3. Aggregate by street and borough, and report three lists: ground to lower or drain, ground to raise, and ground that must not be raised (it protects a neighbour today).
4. Rank where to survey first: the measured result is that knowing the chosen 1% of ground cut the uncertainty in the flooding rain depth by 29% in the solver, and a random 1% by nothing.

## How we would know it is right

- **July 2021.** Two storms flooded over a thousand London properties. Borough flood investigation reports and the London Flood Review record which streets. Test: do the buildings the model floods at those rain depths match the streets that flooded, better than the national map does.
- **Before and after.** Find streets where a kerb, hump or raised table was built and flooding changed. Does the model name that ground.
- **Field check.** Survey the named ground on ten streets with a phone and a level, and see whether the measured heights move the prediction the way stage 3 says.

## Order of work

| When | What | Needs |
|---|---|---|
| Week 1 | Stage 1 and 2 for one borough (Southwark, about 115 tiles) | Open LIDAR and building outlines; one cloud machine |
| Week 2 to 3 | Stage 3 on that borough's at-risk tiles; score against July 2021 records | Rented GPUs; the borough's flood investigation reports |
| Month 2 | Watershed tiling and per-catchment sewer loss; all of London stages 1 and 2 | Thames Water or GLA data sharing |
| Month 3 | London stage 3 on the at-risk tiles; intervention lists per borough | A borough partner to act on one street |

## What we do not know

- Whether the 75 m reach holds on steeper or flatter ground than Southwark.
- How much the constant-sewer assumption changes which ground matters, as opposed to how much rain floods it.
- Whether the patterns on one tile hold on a second. We have not run a second tile.
