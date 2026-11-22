# Postmortem: why this entry did not place

*Written Sunday 22 November 2026, the evening the hackathon ended. Reviewed with Mythos; its full answer is in [`mythos/17_postmortem.md`](mythos/17_postmortem.md).*

We did not place. In one sentence: we entered a careful sensitivity study, run on two laptops, with an 8x gain against our own code, in a contest about what science can do on parallel hardware.

## What we know and what we don't

- We have no scores and no feedback from the judges.
- No results were published when this was written. What we know about the finalists is what we saw in the room, one line each:
  1. Atomic microscopy, about 1000x faster by parallelising the task.
  2. Battery degradation simulation, sped up by a parallel search.
  3. Cancer cell detection, sped up by a parallel search.
- Our reading in the room: each took an existing, trusted model and parallelised the work around it.
- We do not know their baselines, their hardware, or how the 1000x was measured. We also only saw the finalists; similar entries may have lost too.

Everything below about the judges' reasons is inference.

## Why we lost, most likely first

| # | Reason | What we know | Confidence |
|---|---|---|---|
| 1 | The headline was small and measured against ourselves | 8.07x against our own solver. The baseline was extrapolated (12.6 s x 15,788), never run. A finalist showed about 1000x. | High |
| 2 | We showed no parallel hardware | Everything ran on two laptops. No cloud run, no scaling plot. One run already filled the laptop GPU, so running more at once gained nothing. The event was backed by compute companies and offered GPUs. | High |
| 3 | The science was hard to credit | Our own solver, no check against an observed flood, no sewer network, one tile, one storm for the full map. Typical effect 1.7 cm. Only 53 of 98 findings held at twice the rain. | Medium to high |
| 4 | The claim took too long to say | It needs "what-if", "wall point" and "packing" explained first. The finalists' claims fit one line. | Medium |
| 5 | Our reshaping cut the work; it did not use more hardware | 15,788 runs became 1,956 on the same device. The judges may have read "reshape to expose parallelism" as "make it run on many units". | Medium |

Reasons 1 and 2 were probably enough without the others.

## What the finalists had in common

Read against the four criteria:

| Criterion | Finalists (as described) | Us |
|---|---|---|
| Correctness | Borrowed from a model the field already trusts | A solver we wrote, checked only against itself and a JAX reference |
| Reshaping | Weakest point, but "expose existing parallelism" is the first route in the brief | Strongest point, but new and needing explanation |
| Speedup | Baseline is the model's normal serial run, so it is external by construction | Baseline is our own code, not run |
| Scientific value | Inherited from the model's existing use | Had to be argued from scratch |

"They just parallelised an existing model" is a fair description and a poor excuse. Those entries asked the judges to trust one thing: the speedup. Ours asked them to trust three: a new solver, a new method and a new question. An 8x that rests on three unknowns loses to a 1000x that rests on one.

## Where we went wrong, in time order

Each row gives the option that was open at the time, not one that needed hindsight.

| When | What we did | What we could have done |
|---|---|---|
| Sat morning, problem | Took the brief's flood example and wrote our own solver | Use an established open flood code as the model, so correctness is borrowed |
| Sat morning, baseline | Our own code, extrapolated | Install an established code and time it on our tile, once, for real. The brief said "credible baseline". |
| Sat, compute | Ran nothing on cloud GPUs. Ten experiments aimed at 100x were listed and none ran. | Run one job on the GPUs the event provided, on the first morning, and plan around that hardware |
| Sat, pivot | The fast fill model disagreed with the solver, so we left the storm axis for the ground axis | Only the shortcut had failed. We could have dropped it and run thousands of storms directly on GPUs, which is the brief's own example. |
| Sat to Sun, pass lines | Written before the runs, but all of them tested our own consistency | Also write lines for what the judges score: a speedup against an outside baseline, and scaling with hardware |
| Sun, failed checks | Two failures hit the main claim (53 of 98 at 70 mm; moves reaching 76 to 124 m). The headline stayed as it was. | Lead with the failure, or widen the spacing and re-run |
| Sun morning to 15:00 | Much of the time went on slides, wording and visuals. Earlier, time went on a phone app idea, an emulator and a 3D render. | Close one named gap: a second tile, a baseline really run on part of the tile, or a comparison with the Environment Agency surface-water map |
| Sun, headline | "8.07x": three figures on a baseline we never ran | "About 8x fewer runs", checked by brute force on part of the tile |

Two more points.

- **The random check is weaker than it sounds.** 0 of 120 dismissed what-ifs moved a wall. That bounds the miss rate at about 2.5%. Of 15,690 dismissed what-ifs that still allows about 390 misses, more than the 98 we found. We said "miss rate under 2.5%"; we should also have said what that means in counts.
- **The premortem came too late to matter.** At 05:00 on Sunday it listed what winners usually have and we lacked: a gain of ten times or more against an outside baseline, a scaling plot on real parallel hardware, a check against something outside our own model, and a ten-second story. We used it to run four more internal checks. None of the four gaps was closed. That list belonged at 10:00 on Saturday.

## What we got right

- Pass lines committed to git before the runs they judge, and never moved afterwards.
- Failed checks reported next to passed ones.
- Every finding re-run apart from its partners before we claimed it.
- The fill-model plan dropped quickly once the evidence was against it.
- The baseline labelled as extrapolated wherever it appears.
- Real 1 m terrain, and a method with a sound source (colouring for sparse Jacobians, 1974).

## What would have had a better chance

Same person, same weekend, same flood work:

**"A probability map of surface-water flooding for central London from 10,000 storms, in minutes."**

- **Baseline:** an established CPU flood code, run and timed on our tile for one storm.
- **Ours:** the same scheme on the event's GPUs, checked against that code on that storm, then storms batched on each GPU and spread over all of them.
- **Plot 1:** storms per hour against number of GPUs.
- **Plot 2:** chance of flooding at each of the 207 wall points against number of storms. This answers a real question: how many storms are needed before the answer stops moving?
- **If time allowed:** the packed ground map on top, across several storms. That would also have dealt with the 70 mm failure.

A rough size for the number: 10,000 storms at 13 s is 36 laptop-hours. With, say, 32 data-centre GPUs each five times a laptop, that is about 14 minutes, or about 160x from scale alone. Against a single-core reference code, 100x to 1000x is plausible. Every factor in that sum is a guess; we never learned how many GPUs were on offer. Gain per GPU and gain from more GPUs would have to be reported separately.

## Rules for next time

Each can be checked by noon on the first day.

1. An outside baseline is named, installed and timed on one case.
2. One job has run on the hardware the event provides.
3. Any rule about compute states its purpose (for example "no personal spend"), so it is not applied more widely than meant.
4. The headline sentence is written down, and a stranger can repeat it back.
5. A target number is written down with the sum that shows it can be reached. If it cannot, the entry is framed as a negative result from the start.
6. The outside data we will check against is named and downloaded.
7. The domain model is someone else's. We do not write a solver.
8. Hours for slides are fixed in advance, with a written list of things we will not build.
9. The premortem is done on the first morning, not the last.

## What is still worth something

| Piece | Why | Smallest next step |
|---|---|---|
| Packing nearby-only changes into one run | It cuts real work and multiplies with any hardware | Run 500 squares one at a time and measure the miss rate directly |
| Moves that travel along ponds | Shows a fixed distance is the wrong spacing rule where water connects | Space by distance along the water, not in a straight line, and re-test the 76 to 124 m cases |
| The negative results (fill model 77%, derivative 55%) | Useful to anyone trying a cheap route to flood sensitivity | A one-page note with the lines and the figures |
| The solver | Not checked against anything outside, so worth little yet | Run one Environment Agency 2D benchmark case, or compare the tile with the published surface-water map |
| The five-patch design | One storm, one tile | Re-run at three storm depths and report what survives |
| Pass lines before runs | The habit carries to any project | Keep the template, and add a column: "what we do if this fails" |
