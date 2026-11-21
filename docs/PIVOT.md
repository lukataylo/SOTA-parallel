# Pivot, Saturday afternoon: "The Decisive Centimetres"

This replaces the cascade entry in `docs/BRIEF.md`. The shared files, rules, directories and status files stay as they are. Read `status/air.md` for the measurements behind this.

## Why we are changing

The fill model was meant to screen storms so the solver could skip them. On the real tile it gets the settled water level right (98.4% agreement with the solver's final depth) and the peak wrong (it misses 29% of flooded cases, because water in transit sets the peak on flat ground). And a storm can only be skipped when all 207 receptors are decided, which almost never happens. We are not pitching that as a negative result. We are using what it showed.

## The new claim

In a flat city, each building has a critical rainfall depth. That depth is controlled by a few identifiable square metres of ground (the spill points between dips), it can be computed without time-stepping, and it moves by more than the height survey can resolve. The full solver confirms the predicted flips when those few square metres are changed.

What that produces:

1. **A critical rainfall depth per building,** from the fill model, corrected for water in transit if the correction passes its gate.
2. **The controlling ground for each building:** which pass, and how many centimetres change the answer.
3. **An uncertainty budget:** how far the critical depth moves under realistic LiDAR error, from very many terrain-by-storm scenarios that only the fill model can afford.
4. **Causal confirmation:** the solver, run with and without a small terrain change at the predicted spot, flips the building as predicted.

## Go/no-go, next two hours

**Kill line:** the solver confirms fewer than 14 of 20 predicted flips, or the median shift in critical depth under 5 cm terrain noise is below 10%.

If settled-depth flips confirm and peak flips do not, the entry continues only if the transit correction passes by Saturday 20:00: held-out peak error under 2 cm at the 90th percentile.

## MacBook Pro M3 agent

1. **Let the 64-storm pilot finish and commit it.** Do not launch the 1,000-storm brute-force run; it is no longer the baseline.
2. **Rerun the first 16 pilot storms saving the depth time series at every receptor** (every 30 s is enough) to `results/pro/pilot_timeseries.npz`. The Air agent fits the transit correction from this.
3. **Run intervention pairs.** The Air agent will commit `shared/interventions.npz`: for each case, a storm (a rain profile), a receptor, and a small terrain change (cell indices and height change in metres). Run each storm on the unchanged and the changed terrain and save peak and final depth at all receptors to `results/pro/interventions.npz`. The first batch is 20 cases, about 15 minutes.
4. **Order check.** Run 4 pairs where one storm is the other scaled up by 10 to 30%, with the same end time, and report whether the larger storm is at least as deep at every receptor. (The Air agent's envelope test already found the upper bound unbroken in 10 groups, worst case 0.2 mm; this is the clean version.)
5. Afterwards: locate critical depths with the solver by bisection for 3 to 6 storm shapes, for comparison with the fill model's.

## MacBook Air M4 agent

1. Critical net rain depth for every receptor that has one, from the fill model.
2. For each, brute-force small patches (plus and minus 5 cm) on upstream passes to find the ones that flip it. Write 20 predicted flips to `shared/interventions.npz`.
3. 200 noisy terrains (spatially correlated error; check the Environment Agency's stated accuracy) for the spread of critical depth.
4. When the time series lands: fit the transit correction on 12 storms and test on 4.

## What stays true

- Do not write "certified" or "guaranteed".
- Every assumption goes in your status file.
- A gate that fails is reported as it is.
