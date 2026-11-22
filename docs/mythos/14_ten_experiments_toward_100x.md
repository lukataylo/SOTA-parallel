# Mythos: ten experiments toward 100x, and which to build (Sunday 08:30)

## Short answer

100x from the rethink alone is not reachable by 11:00. The rethink (packing) stands at 8.1x, about 28x if the 75 m raised half passes at 10:20, and about 45x at best if denser packing works. A three-digit figure is possible only as packing times filling a bigger card. That is a legitimate product, but a careful judge will discount the second factor, because the baseline could fill the card too.

So the agent should build three things under stop rules, and the human should rehearse.

## Before anything runs

- **Ask the organisers (one minute).** "Use no more compute than is provided" sounds like an event rule as well as ours. If rented GPUs are out, stop here.
- **The port check failed its own line** (0.113 mm against 0.1 mm). Record it as a fail. Do not move the line. Cloud results are checked against cloud solo runs, and against the laptop only on 1 cm decisions.
- **Trap: the shared time step.** If the stack takes one time step from its deepest member, members stop being independent and no longer match their solo runs. Each member needs its own time step and clock.

## Ten experiments

"Stack" means advancing many simulations together as one array on one card. Costs assume about 4 cents per A100-minute; check the price page. The stacking gain S is unmeasured, and all chances are my judgement.

| # | Idea | Arithmetic from our facts | Known or new |
|---|---|---|---|
| 1 | **Stack packed terrains.** Run many different terrains as one array on a card that one tile cannot fill. Each member is a packed run. | One tile is 262,000 cells and fills the laptop. An A100 moves roughly ten times more memory per second. My guess is S = 5 to 20 against one-at-a-time on the same card. | Known. New only combined with packing. |
| 2 | **Dense pack at 50 m.** Put squares 50 m apart, one sign per run, and accept that neighbours interact. Split only the runs where a building moves. | Only 0.6% of what-ifs move anything, so most runs come back clean. About 79 per run gives 200 screen runs plus about 150 confirm and trace, so about 45x. Confirm and trace runs do not shrink, so packing alone can never pass about 100x. | Pooled testing and colouring are known. This use is new. |
| 3 | **Additivity audit.** Price any multi-square design by adding rows of the map, with no run. Test on 128 random designs plus 32 built to break it (squares on the same pond). | One design was additive to 0.18 mm. The map costs 1,956 runs once, so break-even is 1,956 designs. Choosing 5 of 84 squares gives 31 million designs. | Superposition is known. Testing it at kerb scale is new. |
| 4 | **Storm ladder.** More rain never gave less water, so run 32 storm sizes in one stack. Every storm in between is bounded by its neighbours. | 1,000 storm sizes need about 40 runs, so about 25x. The figure grows with the number of storms asked for, so it is soft. | Known practice. The bounds make it checkable. |
| 5 | **2 m screen, 1 m confirm.** Run the packed screen on the 2 m grid and confirm flagged squares at 1 m. | At 75 m: 451 screen runs ÷ 7 = 64, plus about 113 confirms, is 177 run-equivalents, so up to 89x. | Known (coarse-fine). |
| 6 | **Self-checking windows.** Run each what-if on a small window fed at its edges by the unchanged run in the same stack. A tripwire flags any window the change escapes from. | A 64 m window gives 64 per run-equivalent against 35 for packing, under 2x. A 128 m window gives 16, which is worse. Packing is already windowing with perfect edges. | Nesting is known. I have not seen the tripwire version but cannot check now. |
| 7 | **Active tiles.** Update only tiles that hold water. | Rain exceeds loss in every storm, so every open cell is wet. The 15 to 25% figure is cells over 1 cm. Ceiling is about 2x. | Known. |
| 8 | **Local time step.** Let the few deep pits take small steps and the rest larger ones. | Wave speed goes as the square root of depth. √(2.0/0.6) = 1.8, so the ceiling is 1.8x. | Known. |
| 9 | **Parallel in time.** Cut the hour into slices, start each from a 2 m guess, run side by side, correct, repeat. | Gain is at most slices ÷ passes, and at most 7. Each slice takes a stack slot that another what-if would use at full efficiency. | Known (parareal). |
| 10 | **Half precision.** Use 16-bit numbers. | 16 bits resolve about 1.5 cm at 20 m ground level, and our signal is 1 cm. Ceiling is 2x anyway. | Known. Dead on arithmetic. |

| # | Baseline (same card) | Line to commit first | Build | GPU | Number by 11:00 | If it fails, we say |
|---|---|---|---|---|---|---|
| 1 | Same code, one run at a time | Each stacked member within 0.01 mm of its solo run at all 207 receptors | 40 min | 20 min, $1 | 70% | "One tile fills this card too." |
| 2 | One run per what-if (a run count) | All 98 known movers found; new ones confirmed solo; all confirm and trace runs counted | 20 min | 30 min, $1 | 60% (passes: 40%) | "Packing breaks between 75 and 50 m, the 49 m reach of a change." |
| 3 | Simulate each design, stacked | At least 90% of random designs within 1 mm at every building; same-pond set reported apart | 30 min | 30 min, $1 | 70% (passes: 50%) | "Effects add when apart, not when they share a pond." |
| 4 | One run per storm, stacked | 0 held-out results outside their bounds; flooded/not agrees 99% | 15 min | 10 min, under $1 | 75% | "Monotonicity breaks at storm X." |
| 5 | 1 m packed map | Screen flags at least 95% of the 98 movers | 40 min | 10 min, under $1 | 45% (passes: 25%) | "Third screen to fail: a 5 cm kerb needs a 1 m grid." |
| 6 | 75 m packing | Window results within 0.1 mm of full runs | 2 h or more | — | 10% | Show the arithmetic only. |
| 7 | Solo dense run | 0.1 mm | 90 min | — | 15% | "Rain-on-grid leaves no dry cells to skip." |
| 8 | Solo run | 0.1 mm, mass conserved | 2 h | — | 10% | "Thirteen times shallower buys under four times the step." |
| 9 | Stacked what-ifs | — | — | — | 5% | "With a queue of runs, parallel across runs beats parallel in time." |
| 10 | — | — | — | — | 0% | One line of arithmetic. |

Experiments 6 to 10 should not be built. Their arithmetic is a slide of its own: five routes costed and closed.

## Ranking and the top three

By value times chance: 3, 2, 4, 1, 5, then the rest. Build order differs, because everything on the cloud depends on experiment 1.

| Order | Build | Window | Stop rule |
|---|---|---|---|
| 1 | Stack (1) | 08:30 to 09:15 | Stop all cloud work if stacked does not match solo by 09:15. If S is under 3, report it and continue; run counts do not depend on S. |
| 2 | Dense pack at 50 m (2) | Launch by 09:50 | Abandon if not launched by 09:50 or not traced by 10:40. Any known mover missed is a fail, stated as such. |
| 3 | Additivity audit (3) | Build while 2 runs | Abandon if designs are not running by 10:20. |

- **Reserve:** the storm ladder (4) takes over if 2 or 3 stops early.
- **Self-contained audit:** run the 168 single-square solos on the cloud for experiment 3, so it needs no laptop numbers.
- **Budget:** hard stop at $15. Nothing launches after 10:50.

## Allowed definitions and slide sentences

1. **Stack.** Speedup is simulations per hour stacked, divided by simulations per hour one at a time, on the same card, code and precision, with every member matching its solo run.
   - Slide: "On one A100, stacking B terrains runs S times more simulations per hour than one at a time. A laptop gains nothing, because one tile fills it."
   - It is throughput. A single prediction is no faster.
2. **Dense pack.** Speedup is 15,788 divided by all runs, including confirm and trace, given all 98 known movers are found.
   - Slide: "At 50 m the same map takes N runs, not 15,788. Checked against the 150 m map: M of 98. Run on a rented GPU."
3. **Additivity.** This is not a solver speedup.
   - Slide: "A design built from mapped squares is priced by addition. K of 128 random designs matched the solver within 1 mm at every building."
   - Never quote a "million x".

## What multiplies with packing

| Experiment | Multiplies? | Why |
|---|---|---|
| 1 Stack | Yes | Fewer runs times cheaper runs. A strict baseline stacks too, and against that only the packing factor remains. |
| 2 Dense pack, 6 Windows | No | They replace packing. All three are limited by the reach of a change. |
| 5 2 m screen | Partly | It cuts screen runs only, not confirms. Never multiply by 7. |
| 3 Additivity, 4 Storms | No | They answer different questions. Movers did not persist at double rain. |
| 7, 8 | In principle | The ceiling is under 2x. |
| 9 | No | It competes for the same stack slots. |

The honest combined claim is "N times fewer runs, and each run S times cheaper when stacked on an A100", shown as two factors. To state it, measure three things:

- **Time:** a sample of packed stacks and a sample of solo runs on the same card. Label the total as extrapolated.
- **Movers:** the cloud solver names the same movers on a sample of packed runs.
- **Run count:** the real 75 m count with confirm and trace, not 35 ÷ 8.8 × 8.1.

Never multiply a laptop time by a cloud factor.

## Presenting cloud results honestly

- **One separate slide:** "Does it scale on a datacentre GPU?"
- **State the rule change:** "Saturday we said laptop only. Sunday 08:20 we chose to test one rented card. Nothing else in this talk uses it."
- **Show the working:** baseline on the same card, the card and cost named, lines committed first.
- **Keep the laptop numbers untouched.**

## My honest view

- **Chance of 100x:** about one in three that the product passes 100 by 11:00. It needs the 75 m half to pass and S of at least 3.6, or S of at least 12.4 on the confirmed 8.1x.
- **Even then:** do not headline "100x". Show the two factors and the strict-baseline figure, and let the judges multiply.
- **Largest figure I would defend without caveat:** 8.1x now, about 28x after 10:20 if the half passes, and about 45x as a cloud-only result if 50 m passes.
- **Is it worth the time?** For the agent, yes; the cost is about $5 and the failures are informative. For the human, no. Three five-minute check-ins at 09:15, 10:20 and 10:50, and rehearse the rest.

The entry already scores on correctness, reshaping and negative results. A rushed 100x that a judge takes apart costs more than it earns.