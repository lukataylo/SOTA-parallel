===== model=claude-mythos-5-2 stop=end_turn in=16925 out=31321 =====

## Decisions

1. **No baseline change tonight, so zero forced reruns.** Every result stands under the disclosed assumptions. Sensitivities go on the CPU fill model, plus one solver arm of about 30 runs.
2. **Buildings (walls vs upstands) is the assumption most able to break the headline.** Test it in the fill model tonight.
3. **Bet 1 headline error model becomes nested (short plus long), scored on relative levels.** The existing 5 cm / 3 m result stays, relabelled as the "unresolved kerb-and-threshold structure" scenario.
4. **Lead with P1, not Bet 1.** P1 does not depend on the error model, has controls and pre-committed lines, and sits in the largest gap the literature search found.
5. **Hold the Bet 1 solver pilot until the error model is fixed.** Pause Bet 3 while P1 is on the Air.
6. **The human reads Lowe's 2021 dissertation tonight.**

Three of the research notes reached me cut off: the EA note stops before the LIDAR accuracy section, the prior-work note stops at SCALGO, and the SuDS note stops at the Berlin study. I am relying on your summary for the variogram and the EA 5 cm figure. Items marked (guess) are my estimates, not sourced.

## 1. Model assumptions

| Assumption | Decision | Reason |
|---|---|---|
| Drainage 12 vs 18 mm/h, runoff 70 vs 100% | Leave, disclose, report in net rain with a conversion table | It only relabels the rain axis: gross = (net + loss × duration) / coefficient. Ranks and controlling cells are unchanged, as are % cuts at a given duration. This holds if the loss comes off the rain rate, not ponded water. |
| Roof rain | Leave; fill-model sensitivity on CPU | Tile-average net rain is 0.65 × (i − 12) for us against 0.7i − 12 for the EA. They are equal at 84 mm/h, and ours is 14% higher at 40 mm/h. Only the spatial placement differs. |
| Buildings | Fill-model sensitivity tonight; solver arm only if the gate trips | It is the only item that can move the spill points themselves. |
| Manning n | Leave 0.015; one solver arm at 0.02 on a P1 subset (10 patches per class, middle storm, about 31 runs) | It has no effect in the fill model. In the solver it matters only where flooding is flow-through rather than ponding. |
| Threshold | Leave 0.10 m; recompute at 0.15 and 0.30 m from saved depths | This is post-processing. Check now that P1 saves peak depth at receptors, not just pass/fail. |
| Road lowering | Leave, disclose, cite as evidence | It is the EA's patch for kerbs missing from the DTM. Run it in the fill model only if you already hold a road mask. |
| Viaducts | Check each arch against imagery now (10 minutes), then leave | A closed arch is a false dam. Also check that no P1 patch or top-ranked Bet 1 cell sits on the viaduct line. |

**Why buildings matter most.** With walls, a terrace row can dam water to any depth and the spill point is forced into a gap. With 0.3 m upstands, the same depression can spill through the footprint. The "controlling cell" then becomes a modelled floor level, not surveyed ground.

- **Test:** rerun the fill model with footprints at mean ground + 0.3 m, with roof rain off and then on.
- **Gate, committed before looking:** if more than 20% of receptor buildings change controlling spill cell, add upstands to the 31-run solver arm; otherwise disclose the percentage.
- **Defence of walls:** it was the EA's 2010 method and is still common in 2D urban models.

**Drainage needs one honest sentence in the write-up.** The EA calls drainage its largest uncertainty. Moving from 12 to 6 or 20 mm/h shifts every threshold by 6 to 8 mm over a 60-minute storm, which is more than our 5.9 mm terrain spread. Under a uniform loss that shift is common to all buildings and preserves their order. So the claim is that terrain controls which building floods first and which ground decides it, not the absolute threshold.

Also disclose two things: there is no inflow from outside the tile, and our storms are 15 to 60 minutes against the EA's 1, 3 and 6 hours.

## 2. Terrain error model

**Headline model:** two components.
- **Long:** sd about 15 cm, Gaussian-filter sigma 20 to 30 m (guess). For a Gaussian-shaped covariance, that sigma corresponds to a variogram range of 65 to 100 m.
- **Short:** sd about 2.5 cm at sigma 1 to 3 m. This reads the EA's "at most 5 cm relative" as roughly two sd, which is my reading.
- **Near buildings:** a doubled sd is a sensitivity only; no source gives a number.

**Fix the scoring first.** I am assuming "FIXED reference level" means an absolute level that does not move with the perturbed ground at the building. If so, a long-wavelength error acts as a datum shift between terrain and threshold, which is an artefact, since the real door sill moves with the real ground. Score the sweep both ways: fixed, and with the reference riding on the long component at the building.

**Fix the measurement model too.** At sigma of 10 m or more, a surveyed cell informs its neighbours. If "measured" only zeroes the error at the cell, the targeted-versus-random comparison is meaningless there. Condition the field on the measured cells (kriging on about 2,600 points is cheap).

**Prediction (guess), which you should commit before reading results:**
- **Fixed reference:** spread does not collapse and may rise 1.5 to 3 times from 3 m to 60 m, because coherent error over a ponded area no longer averages out.
- **Riding reference:** spread peaks at 3 to 10 m. It falls to about a third of the peak at 30 m and a sixth at 60 m. For two points 20 m apart, the sd of the level difference is 7 cm at sigma 3 m, 2.3 cm at 30 m and 1.2 cm at 60 m.
- **Sigma 1 m:** lower spread than at 3 m, with an upward bias in median critical rain from spurious pits.

**If it collapses, say this:** "Long-wavelength LiDAR error is nearly harmless to per-building thresholds because it moves building, storage and spill crest together. What matters is relative level over tens of metres and structure the DTM does not resolve." This agrees with Abily (measurement noise index 0.06, feature detail 0.40) instead of fighting it.

**Robust framing: yes, adopt it.** The unknown is kerb-and-threshold structure, and three sources support it:
- The EA lowered roads by 0.125 m and lists dropped kerbs, walls and speed bumps as absent from the DTM.
- The Blue Spot report says kerb shape "may completely change" flow paths.
- de Almeida found decimetric street edits matter.

A kerb that is present or absent (0 or 12.5 cm) has an sd of 6.25 cm; uniform over 0 to 12.5 cm gives 3.6 cm. So 5 cm at a few metres is a defensible stand-in. Disclose that we applied it everywhere, whereas real structure sits on road edges and thresholds.

Also report sensitivity as mm of critical rain per cm of short-range relative error, with an sd sweep at 2.5, 5 and 10 cm to check linearity. Readers can then plug in their own sd.

## 3. Novelty

All "new" claims should read "we did not find, in about 50 searches with most full texts unreadable".

- **P1 / Bet 1 claim:** attribution of a building's threshold to specific spill cells, the distance from those cells to the building, and causal confirmation in a 2D solver against null and random controls. Also the held-out test that surveying a targeted 1% beats a random 1%.
- **Bet 2 claim:** the derivative of the volume-based rain threshold (storage and cascade terms) in one sweep, checked against finite differences. Say plainly that the spill-elevation part follows from known persistence results, and that it is exact only away from spill-order switches.
- **Bet 3 claim:** nothing as first. The text I received does not cover a no-harm constraint, and "do not increase risk elsewhere" is a standard planning principle. Describe it as a constrained search.
- **Absorption claim:** cell-scale patches chosen from the depression tree before any solver run, and location versus volume at a fixed 250 m³.

**Wording to avoid:**
- "first to compute rain needed to flood a point or building"
- "per-building" as a novelty in itself
- "in seconds" as a contribution
- "LiDAR noise moves thresholds by tens of percent"
- "first to propagate terrain error"
- "new exact gradient"
- "first 2D-solver SuDS optimisation" (CONFIGURE)
- "source-receptor" as ours (Newcastle)
- "many small beats few large" as ours (Rehman)

**Most dangerous unread source: Lowe 2021.** Check four things:
1. Does a query return the rain needed to flood a point, including upstream cascades?
2. In the uncertain-terrain chapter, what is the error model (independent or correlated) and the output (flood probability or threshold distribution)?
3. Is there any attribution of uncertainty to particular saddles or cells, or any remark on where to collect data?
4. Is there any hydrodynamic validation, or any buildings?

If point 3 is yes, Bet 1 becomes "an application with a solver check".

## 4. Running plan

1. **P1 continues untouched.** At the current rate (about half a minute per run) the Air alone finishes around 18:50, sooner once the M3 Pro takes its half.
2. **If the CPU jobs share the Air, pause Bet 3 now.** It has the weakest novelty and no result. Resume it overnight; if there is nothing usable by Sunday 10:00, it becomes a paragraph.
3. **CPU tonight:** the upstand and roof fill runs, the sweep scored both ways, the nested model, threshold recomputation, and bootstrap intervals on the cuts.
4. **GPU queue after P1:** the 31-run n arm (about 15 minutes), then the Bet 1 pilot once under the final error model (about 45 minutes), then E1 after the absorption-parameters thread reports.
5. **No new solver runs after Sunday 11:00.**

**New headline, conditional on P1 passing:** "Screening tools already say how much rain floods a point. We show which few square metres set that number for each building, how far away they are, and that a 2D solver agrees when exactly those cells are changed and not otherwise." Bet 1 follows as the application. If P1 fails, that is still reportable, since the screening tools it tests publish no such check.

## 5. Selection criterion

**Partly yes; keep the criterion and change the procedure.** Variance explained is sensitivity squared times prior variance, including what a cell tells you about its correlated neighbours. That is the meteorology point already. Three changes:

- **Redundancy:** top-1% by marginal score picks clusters that explain the same variance. Select greedily: pick, condition the ensemble, re-score. Batches are fine.
- **Sampling noise:** with 600 members, spurious correlations are about 0.04. Restrict candidates to each building's upstream subtree.
- **Error model:** retrain the scores under the nested model. Selection then moves away from peak sensitivity on its own wherever prior sd is larger.

If Bet 2 lands, the score is available analytically from its gradient and the error covariance. "One sweep replaces 600 terrains" would be a real result.

**Reporting.** The 40.2% is at the line within noise, not clearly over it. If the ensemble method was introduced after the patch method failed, say so. Evaluate any new selection on fresh held-out terrains with the line committed first.