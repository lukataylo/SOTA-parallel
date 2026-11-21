# Extension: absorbing ground (rain gardens, permeable paving, grass, tree pits)

Requested by the human on Saturday afternoon. Experiment design by Mythos, in full at `docs/mythos/5_absorption_design.md`. Pass lines below are fixed before each experiment runs.

## The question

Height changes redirect water; absorption removes it. Do they have the same decisive ground? Can a small rain garden on the right flow path do what a large one placed at random cannot?

## How absorption is represented

One mechanism for every type: a sink on a cell that takes water standing on it, in two stages. Stage 1 is an instant capacity (surface ponding or open voids). Stage 2 is a further capacity that fills at a limited rate (soil or filter media). The ground is not lowered, so absorption and height changes stay separable.

| Type | Instant capacity | Rate | Slow capacity | Takes per storm |
|---|---|---|---|---|
| Grass on London clay | 3 mm | 10 mm/h | 15 mm | about 10 mm |
| Permeable paving, lined, 300 mm sub-base | 90 mm | n/a | 0 | 90 mm |
| Rain garden, underdrained | 150 mm | 100 mm/h | 100 mm | about 250 mm |
| Tree pit with kerb inlet | 375 mm over 4 cells | n/a | 0 | 1.5 m3 per tree |

**These values are Mythos's recollection, not checked figures.** A research thread is checking them against the CIRIA SuDS Manual tonight. The existing 12 mm/h loss stays everywhere, which slightly double-counts for grass, so any grass result is an upper bound.

## What we will not claim

- Tree canopies reduce cloudburst flooding. Interception is 1 to 2 mm on the canopy footprint. It is set to zero.
- "Chances of a flood". We compute rainfall thresholds in mm, not probabilities.
- That capacity is always available. Every store is assumed empty at the start, and the model assumes water on the cell gets in.
- Permanent removal, or anything about cost.

## Predictions committed before running

1. The absorption leverage map is a broad plateau (every cell whose water reaches the building's pond), never negative. The height leverage map is sparse spikes with both signs.
2. Grass does nothing measurable at budgets of 1,000 m2 or less.
3. Sinks work only where they fill: under the pond or on spill paths.
4. Absorption placement survives 5 cm terrain error better than height placement does.
5. Buildings flooded by moving water benefit less than the volume suggests.

## Experiments and pass lines

| # | What | Where | Pass line |
|---|---|---|---|
| E0 | Absorption map from the fill model; contributing area per building; ceiling table | Air CPU | The formula "rise in critical rain = captured volume / contributing area" is within 2% of exact re-solving on at least 95% of 100 test placements. **Kill** if the best 250 m3 placement lifts fewer than 5 buildings by 10%. |
| E1 | Go/no-go in the solver: 12 buildings (8 ponding, 4 moving-water), 3 storms, 4 arms (targeted rain garden, same area nearby but off the contributing ground, same area at random, grass on the targeted footprint). 144 runs | GPU | At least 6 of 8 ponding targets drop by 1 cm or more. Near-null and random arms move at most 10% of building-storm pairs. Median near-null effect under half the targeted effect. No building rises by 1 cm. Targeted sinks reach at least 50% of capacity. Mass balance including absorbed water closes to 0.1%. |
| E2 | Budgets of 250, 500, 1,000 m2: targeted against random, lowest-ground and a "parks" rule | GPU | Targeted 1,000 m2 protects at least 5 buildings and harms none; random median is at most a third of that. |
| E3 | Buildings flooded by moving water: sink on the path against the same area 30 m off it | GPU | At least 4 of 8 drop 1 cm on-path; at most 1 of 8 off-path. |
| E4 | Robustness to terrain error | CPU then GPU | Targeted beats random median 3x on at least 80% of terrains. |

**Rule.** If E1 fails or is not ready, the extension becomes one line on a slide: the E0 ceiling table.

## The number this adds, if it works

The placement multiplier: how many square metres of randomly placed rain garden match 500 m2 placed by the map, confirmed in the solver.
