

===== TURN 1: independent view | model=claude-mythos-5-2 stop=end_turn in=4457 out=11836 =====

**Short version:** build a screen-then-simulate flood ensemble on the real Southwark tile, where a cheap conservative bound decides most storm-and-door cases and the GPU solver runs only on the rest. I put it at roughly 10-15% for first place. It rests on one untested thing: whether the dry bound still certifies anything on real terrain.

## 1. What wins

Most teams will take an example challenge, port it to the GPU with an AI agent, batch it over scenarios, and report 100-1000x against a slow Python or CPU baseline. That now takes hours, so it is table stakes. It scores on speedup, weakly on reshaping, and usually poorly on correctness and baseline credibility.

First place most likely goes to the team that shows three things together:

- **A real reshaping:** a change to what gets computed, not where it runs.
- **An honest baseline:** the obvious GPU port on the same hardware, not a CPU strawman.
- **A validated result on real data:** evidence the answer did not change, with assumptions stated.

Your edge is that you can afford validation and real terrain while others are still getting a solver to run. Your weaknesses are zero GPU numbers, synthetic-only evidence, and no hydrologist.

## 2. Ranking

The probabilities are rough, since I don't know the field size or quality.

| Direction | P(first) | Main way it dies |
|---|---|---|
| A. Screen-then-simulate ensemble on real terrain (idea 2 as screen, PDE on the remainder, idea 1 as stretch tier) | 10-15% | The bound certifies almost nothing on real terrain, or skipping saves under 2x |
| B. Min-max parallel fill as standalone (idea 1) | 4-6% | The baseline is 0.37 s in sequential C, rounds grow with size (29 to 239), and parallel priority-flood already exists (Barnes; check this) |
| C. Plain batched GPU ensemble plus local-street demo | 3-5% | Indistinguishable from five other teams |
| D. Switch to asteroid or docking challenge | 2-4% | You discard your head start |
| E. Worst-storm gradient search | 2-3% | Random search parallelises perfectly and gradient search is sequential; the storms were unphysical (1,000 mm/h) |
| F. Scan map | 1-2% | Off-theme, and your own evidence collapsed (92% to 37/30/95%, smoothing failed) |
| G. Regrade | <1% | Already failed its kill line |

Use E, F and G as one negative-results slide and nothing more.

## 3. Top choice: A

**Claim:** "For N storms on the 1 m Southwark terrain, a conservative volume screen plus a batched GPU solver gives the same per-location flood-probability table as simulating every storm, in X times less GPU time, with zero false-dry decisions."

**Baseline:** the same solver on the same GPU, batched over all N storms. Judges will accept it because it is the entry they see from everyone else, and it doubles as your ground truth for the screen. Report the 2-core CPU figure only as context.

Two things to fix before pitching:

- **Don't say "certified" or "guarantee".** The bound is hydrostatic, and moving water is exactly what broke your second certificate (190 of 462). Zero in 640 only bounds the violation rate below about 0.5%, on your own generator, after a post hoc repair. Call it a conservative screen with a measured violation rate.
- **The bound must count all rain that can reach each location.** On a real tile that means the upstream catchment, not the local street. This may wipe out coverage.

Experiments, in order:

1. **Screen coverage on the real tile (CPU, today by 16:00).** This is the cheapest and most decisive test.
   - Use fixed receptor points and a stated depth threshold; include the documented flood site.
   - Kill line: fewer than 30% of storm-and-receptor cases screened, or fewer than 20% of whole storms skippable. Then fall back to C plus B as an honest negative result.

2. **GPU throughput (today by 16:00, in parallel).**
   - Measure cell-steps per second, single and batched.
   - By my rough arithmetic, 1,000 one-hour storms on 1M cells is several GPU-hours at 30x your CPU rate. Size the domain so brute force finishes in under 2 GPU-hours.
   - Kill line: under 10x your CPU rate after an hour of tuning. Then shrink the domain or go to 2 m.

3. **Solver credibility (2 hours).**
   - Run lake-at-rest, mass balance, and one analytic test case.
   - Compare 1 m against 2 m. Kill line: wet/dry decisions agree under 95%. Then state resolution dependence as a limitation.

4. **Brute-force run (overnight Saturday).** Draw storms from a stated depth-duration distribution, subtract a stated drainage loss, and stratify by return period so nobody can say you padded with trivially dry storms.

5. **Soundness and speedup (Sunday morning).**
   - Kill line on soundness: any false-dry case. Diagnose it, add a principled margin, and report the rate; do not patch silently.
   - Kill line on speedup: under 2x end-to-end. Then present it as a negative result with the coverage curve.

6. **Stretch: partial-fill basin graph as a middle tier.** Kill line: not matching the solver on synthetic streets by Saturday 22:00. This is where the real "fundamental reshaping" points are, but it is untested.

7. **Reality check.** Does water appear at the documented flood street? This is an anecdote, not validation; say so.

## Where the evidence is too thin

- **Field and judges:** I can't tell how many teams there are, or whether the judges lean towards hardware or science.
- **Real-terrain behaviour:** viaducts in the LiDAR and sewer-driven flooding could make the Southwark results physically wrong in ways neither of us would spot. Ask a mentor on Saturday, not Sunday.
- **Rules on prior work:** check whether pre-existing code is allowed, and disclose it either way.


===== TURN 2: critique and final | model=claude-mythos-5-2 stop=end_turn in=17322 out=11362 =====

Your position beats my first answer on the reshaping, but its headline claims are the weakest part. Build the factorised cascade and change what it claims.

## Where your position is wrong

1. **The storm space collapses.** A static fill model with street-scale uniform rain depends on about two numbers per storm: depth and, through drain losses, duration. A million storms then evaluate the same 2-D table a million times, and a judge will see that quickly. "Millions of storms per second" is a vanity number.

2. **The tail-risk payoff is overstated.** At 1-in-10,000 the error is dominated by the rainfall tail and model bias (sewers, the static assumption), not Monte Carlo noise. Sampling 10^8 times gives false precision.

3. **The solver costs per storm, not per pair.** It simulates the whole domain, so a storm is skipped only if every receptor is decided. The end-to-end speedup is roughly one over the fraction of storms with any receptor in the band. Nobody has measured that, and it could be near 1.

4. **The fill tier's error is two-sided.** "Errs toward false alarms" and "190 of 462 still-pond violations" point in opposite directions. Water running down a slope past a door is a false-dry mechanism a fill model cannot see. The 12 cm band also had 1 violation in 62 in the first batch and is synthetic-only.

5. **Rungs (a) and (b) are not independent.** The volume certificate is the fill model's no-outflow limit. Both rest on the hydrostatic assumption and fail the same way.

6. **Your CPU baseline will probably beat your GPU on the graph tier.** Fill-spill-merge on a few hundred basins should take microseconds per storm in C. Report that honestly; the GPU earns its place in the solver tier.

7. **"Without time-stepping" is not new.** Rapid fill-and-spill flood models exist in UK practice (HR Wallingford's RFSM, from memory; verify). The novelty has to be the cascade with measured error, not the fill model.

Your risk 4 (judges seeing "skip the simulation" as a dodge) I rate lower than you do, provided the solver stays in the pipeline as the arbiter.

## Where I now disagree with my first answer

- I made the volume screen the core and partial fill a stretch. That is backwards: the screen alone is a thin reshaping, probably worth 2-5x. Partial fill should be the main build and the screen the fallback.
- My kill lines mixed pair-level and storm-level coverage. Only storm-level matters.
- My claim had the same collapse problem. If storms differ only in depth, a competent baseline would bisect rather than run N storms. The ensemble must vary something the solver feels and the fill tier does not: the temporal profile.

## The single entry: "Time-step only where it matters"

Build a two-fidelity flood ensemble on the real Southwark tile:

- **Fill tier:** a batched fill-spill-merge model gives each receptor's settled water level for every storm.
- **Band:** a two-sided band, measured on real terrain against the solver, marks which storms are undecided.
- **Solver tier:** the batched GPU solver runs only on undecided storms.
- **Probability estimate:** P(flood) = P(sure wet) + P(band) × P(wet | band), with the last term estimated by the solver.
- **Baseline:** the same solver on the same GPU over all storms. This run doubles as ground truth.

Implement partial fill as a bottom-up sweep over the depression tree, vectorised over storms. Don't spend time on min-max elegance there.

## Plan

| When | Work | Gate |
|---|---|---|
| Sat 14:00-15:00 | Get on the GPU and time the solver, single and batched. In parallel, an agent downloads the tile, cuts a domain of about 500 m including the documented flood street, and places 50-200 receptors with a stated threshold. | Under 10x CPU rate: go to 2 m |
| 15:00-16:00 | Build the basin graph on the real tile and each receptor's volume bound over its full upstream catchment. Ask a mentor about viaducts and sewers. | Bounds don't spread across the plausible storm range: cut the receptor set |
| 16:00-19:00 | Build batched partial fill. Use Barnes's Fill-Spill-Merge code as oracle if it builds, else the settled solver on synthetic streets. | Decisions match under 98% by 19:00: drop to the volume-screen-only entry |
| 19:00-20:00 | Solver checks: lake at rest, one analytic case, 1 m against 2 m. Eat. | |
| 20:00-22:00 | Write the storm sampler (depth, duration, profile; stated drainage loss). Run a 64-storm pilot through both tiers on the real tile and set the two-sided band from it. | Most pilot storms have a receptor in the band: expect the negative result |
| 22:00-23:30 | Launch the full brute-force run on fresh storms, chunked and resumable, sized to finish by 07:00. Draft the slide skeleton. | |
| 23:30-07:00 | Sleep. | |
| Sun 07:00-09:00 | Score false-dry count, storms skipped, and wall-clock for both routes. | |
| 09:00-11:00 | Run the large fill-tier ensemble with a solver subsample of the band. Time the C baseline for the fill tier. | |
| 11:00-12:00 | Decide the pitch. | Under 3x or any unexplained false-dry: negative-result pitch |
| 12:00-14:00 | Figures: probability map, cascade diagram, cost table, documented-street check. | |
| 14:00-16:00 | Slides, including one failures slide (scan map, regrade, worst-storm search). Write the README. | |
| 16:00-17:30 | Rehearse, record a backup video, submit. | |

## Three numbers for the final slide

1. **Speedup:** end-to-end, for the same per-receptor probability table, against the brute-force batched solver on the same GPU.
2. **Soundness:** false-dry decisions out of N held-out storm-receptor cases, with the band width in cm measured on real terrain.
3. **Science:** the critical storm (or flood probability with interval) at the documented flood street, and whether it is consistent with the recorded event.

## If the speedup does not materialise

Say this: "We tested whether a static fill model can replace time-stepping for flood ensembles on real London terrain. It decides only X% of storms. In the rest, moving water sets the outcome, the band is Y cm wide, and the solver still dominates, so the end-to-end gain is Z times. Here is where the band comes from, which terrain features predict it, and the exact parallel fill that still loses to sequential C below size B."

That is a measured negative result with a mechanism, which the judging slide explicitly rewards.
