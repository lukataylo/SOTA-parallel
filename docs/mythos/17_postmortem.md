# Mythos: postmortem (Sunday 19:00, after the results)

*Asked after the hackathon ended. Two corrections to this text are made in `docs/POSTMORTEM.md`: the 0 of 120 bound applies to 15,690 dismissed what-ifs (about 390 possible misses, not 195), and the Sunday 05:00 premortem did lead to four extra checks being run.*

# Postmortem: SoTA Scientific Parallelism Hackathon, 21–22 Nov 2026

We did not place. We entered a careful sensitivity study, run on laptops, at a contest about parallel hardware. The headline was 8x against our own code, with a baseline we never ran.

**Evidence limits.** We have no scores, feedback, or published results. Everything about the finalists is one second-hand line each.

## 1. Why we lost, ranked

| # | Reason | Known | Inferred | Confidence |
|---|---|---|---|---|
| 1 | Headline small and self-referential | 8.07x against our own solver; baseline extrapolated, not run | One finalist reportedly showed ~1000x | High |
| 2 | No parallel hardware shown | No cloud runs, no scaling plot; batching gave nothing on the laptop | Compute sponsors wanted to see scale | High |
| 3 | Scientific value hard to credit | Own solver, no outside validation, no sewers, one tile, one storm; median effect 1.7 cm; 53/98 persist at 70 mm | Judges discount centimetre effects from an unvalidated model | Medium-high |
| 4 | No ten-second story | 17 steps; the claim needs "what-ifs", colouring, and wall points explained | Finalists' claims fit one line | Medium |
| 5 | Our reshaping cut work, not exposed parallelism | 15,788 runs became 1,956, on one device | Judges read criterion 2 as hardware parallelism | Medium |
| 6 | Pitch delivery, field strength, judge taste | Nothing | Nothing | Cannot assess |

Reasons 1 and 2 were probably sufficient on their own.

## 2. What the finalists share

By the account, each took an existing model in a domain nobody needs explained (materials, energy, health) and parallelised a task or search around it. Against the criteria:

- **Correctness:** borrowed from a model judges already trust.
- **Reshaping:** their weakest criterion, but "expose existing parallelism" is the first route in the brief.
- **Speedup:** the baseline is the model's normal serial run, so it is external by construction.
- **Scientific value:** inherited from the model's existing use.

"They just parallelised an existing model" is probably fair as a description, but not as a dismissal. Their entries asked judges to trust one thing, the speedup. Ours asked them to trust three: a new solver, a new method, and a new question. An 8x resting on three unknowns loses to 1000x resting on one.

The inferred lesson is that judges rewarded a large, legible number on trusted science, on the kind of hardware the sponsors care about.

**Limits.** We do not know their baselines, their hardware, or whether the 1000x was honestly measured. We see only finalists, so similar entries may also have lost.

## 3. Decisions, in time order

| When | What we did | What was available then |
|---|---|---|
| Sat AM, problem | Took the brief's flood example but wrote our own solver | An established open flood code (LISFLOOD-FP, ANUGA, SFINCS; licences and GPU support to check). The brief said "credible baseline". |
| Sat AM, baseline | Our own code, extrapolated | Time the established code on our tile, once, for real. |
| Sat, compute rule | Applied "stay inside free limits" as "no cloud" | The provided GPUs were free. Ten 100x experiments were listed and none ran. |
| Sat, pivot | The fill model failed, so we left the storm axis | Only the shortcut failed. We could have dropped it and brute-forced storms on the provided GPUs, which is the brief's own example. |
| Sat–Sun, pass lines | Committed before runs, but all tested internal consistency | Lines for what judges score (external speedup, scaling), each with a pre-written consequence. |
| Sun, failed checks | Two failures (70 mm, reach beyond 75 m) hit the core claim; the headline stayed | Lead with the failure, or widen the colour spacing and rerun. |
| Sun after 05:00 | Slides, copy, and visuals; earlier, an app idea, an emulator, and a render | Close one named gap: a second tile, a measured baseline on a sub-area, or a comparison with the EA's published surface-water flood map. |
| Sun, headline | "8.07x", three significant figures on an unrun baseline | "About 8x fewer runs", checked by brute force on a sub-area. |

Two further points:

- **The 0/120 check is weaker than it looks.** Zero of 120 gives a 95% upper bound of about 2.5% on the miss rate. Across 7,810 dismissed squares that allows roughly 195 missed movers, more than the 84 we found.
- **The premortem came a day late.** It named all four gaps at 05:00 Sunday and nothing changed afterwards. It should have been the checklist at 10:00 Saturday.

## 4. What to keep

- Pass lines committed to git before the runs.
- Reporting failed checks alongside passed ones.
- A confirmation run for every claimed mover.
- Killing the fill-model plan quickly on evidence.
- Labelling the baseline as extrapolated.
- Real 1 m data, and a method borrowed from a sound source (sparse Jacobian colouring).

## 5. The counterfactual

**Entry:** "A probabilistic surface-water flood map of central London from 10,000 storms, in minutes."

- **Baseline:** an established CPU flood code, run and timed on our tile for one storm.
- **Ours:** the same local-inertial scheme ported from MLX to PyTorch or JAX. It is checked against the baseline on that storm, then storms are batched per GPU and spread across the provided GPUs.
- **Plot 1:** storms per hour against GPU count.
- **Plot 2:** exceedance probability at the 207 walls against ensemble size. This answers a real question: how many storms before the answer stops moving?
- **Second act, if time:** the colouring map across ten or more storms, which also addresses the 70 mm failure.

**Plausible number.** At 13 s per run, 10,000 storms is 36 laptop-hours. If a data-centre GPU gives 5x laptop throughput when batched and 32 were available, that is about 14 minutes, or 160x from scale-out alone. Against a single-core reference code, 100–1,000x wall-clock is plausible. Every factor here is an assumption, and I do not know the actual GPU allocation. Per-GPU speedup and scale-out must be reported separately.

## 6. Rules for next time

Each is checkable by Saturday noon.

1. An external baseline is named, installed, and timed on one case.
2. One job has run on the provided hardware.
3. The compute rule states its purpose ("no personal spend"), not a proxy for it.
4. The headline sentence is written down, and a stranger can repeat it back.
5. A target number is written down with arithmetic showing it is reachable, or the entry is framed as a negative result from the start.
6. The outside validation source is named and downloaded.
7. The domain model is a dependency, and we write no solver.
8. A presentation budget is fixed in hours, with a written list of things not to build.

## 7. What is still worth something

| Asset | Why | Smallest next step |
|---|---|---|
| Colouring for local perturbation ensembles | Real work reduction; multiplies with hardware | Brute-force 500 squares and measure the miss rate directly. |
| Locality failure along ponds | Shows fixed-radius colouring is wrong where water connects | Replace straight-line distance with flow-path distance and retest the 76–124 m cases. |
| Negative results (fill model 77%, derivative shortcut 55%) | Useful to anyone trying cheap flood sensitivity | A one-page note with the pass lines and figures. |
| The solver | Unvalidated, so currently worth little | Run one EA 2D benchmark case, or compare the tile with the EA surface-water map. |
| Five-patch design | Weak: one storm, one tile | Rerun at three storm depths and report what survives. |
| Pass-line habit | Transferable | Extract a template with a "consequence if failed" column. |
| Animated story, Q&A helper | Little | Archive them. |