# Mythos: a parallelism speedup against an existing baseline, on the provided compute (Sunday 05:30)

**1. Verdict on the brief**

On brief with a reframing, plus one small experiment that makes the reframing true rather than asserted.

The sentence: "Flood risk is uncertain in the rain and in the ground. One run already fills the GPU, so we rethought how simulations run in parallel: nine ground scenarios share one grid, because water forgets a 5 cm change within about 125 m. The answer changes with the storm, so this is done per rainfall scenario."

Persist failing is the tie to rainfall, not an embarrassment. The 64-storm ensemble stays in as the rainfall axis already in hand.

**2. Baseline**

"One simulation per changed square per storm, which is how the published CityCAT study (arXiv 2311.00420) mapped where green space matters."

- **Held fixed:** same MLX solver, same laptop, same 35 mm storm, same grid, same 15,788 what-ifs, same 1 cm verdict. Only the number of what-ifs per simulation changes.
- **Our cost:** 1,956 runs, which includes the confirm and trace runs.
- **Baseline cost:** mean measured seconds per single run (from the singles already on disk) times 15,788. Say "extrapolated from measured singles; we did not run 55 hours."
- **CityCAT:** we borrow their practice, not their timings.

**3. Plan**

The Air alone at about 240 runs per hour finishes around 09:10.

*Now to 06:45 (no runs; persist keeps running):*
- Mark the 05:20 cloud table "withdrawn, not run".
- Commit the lines below.
- Compute baseline seconds per run from the logs.

*Primary: Dense, 06:45 to 07:50.* This is the parallelism scaling test and is already committed.
- **Runs:** 226, plus at most 30 trace runs.
- **Line:** unchanged from the 05:04 commit.
- **Pass:** "At 75 m spacing, 35 what-ifs per simulation with the same answers."
- **Fail:** "At 75 m packing loses X%. The reach of water sets the factor; 150 m is near the limit here."
- Either way the slide is a two-point curve, 8.8 and 35 per run, with the physical limit marked.

*Secondary: 70 mm slice, 07:50 to 08:40.*
- **Runs:** one unchanged run at 70 mm, then the first 80 colours in seed-2026 order, raised and lowered (160 packed runs, about 1,400 what-ifs). Then each mover alone, at most 40 runs, in seed order.
- **Line:** at least 90% of slice movers keep their verdict alone, the same line as the 35 mm map. The count of movers not on the 35 mm list is reported with no line.
- **Pass:** "Packing holds at 70 mm at the same spacing. K movers, M of them new. Each storm needs its own map, and each map costs one eighth."
- **Fail:** "Water reaches further in a bigger storm. The spacing, and so the speedup, must be set per storm; at 70 mm we measured X."

*Then the remaining committed checks:*
- **Random dismissed, 08:40 to 09:10.** Cut to the first 120 of the same seeded draw and recommit before running. The line stays 0 moves. The claim becomes "the map misses under 2.5%". If behind, stop by the clock, never by results.
- **Design, 09:10.** One run as committed.
- If the Pro wakes, it takes Random dismissed at the full 240.

Killed:
- **B:** uniform rain touches every cell, so there is nothing to pack.
- **C:** it is not parallelism.
- **D:** the reach of a 5 cm change is not the reach of the flow, so the halo argument is wrong.
- **E:** backup slide only.
- **F:** one labelled line, "pre-hackathon JAX solver on the same laptop's CPU 105M cell-steps/s, ours on its GPU 340-450M", never multiplied into the 8.

**4. Cloud**

- No Modal runs. The scaling table is withdrawn by instruction.
- The A100 check gets one disclosure line in the README: "Before the compute limit was set, one 20-second port check ran on a rented A100. No number from it is used."
- It does not appear in the talk and no throughput figure from it is quoted.

**5. Cuts and the title sentence**

Cut:
- the quick estimate and its screen rules, down to one line ("a fast prior finds 77%");
- the bisection cascade;
- the cloud;
- the throughput tables.

Keep one negative result: "Batching gave nothing; one run saturates the GPU. That is why the parallelism had to come from the physics."

Title sentence: "Same solver, same laptop, same storm: 15,788 ground what-ifs in 1,956 simulations instead of 15,788. That is 8 times fewer GPU-hours (55 to 7), because scenarios 150 m apart run in parallel inside one grid."

**6. The trap**

A judge says: "Your 8x is for one storm, and you just showed the map does not transfer. So thousands of rainfall scenarios cost thousands of maps."

- Say it first, as our finding.
- Claim 8x per storm only. Never multiply by a number of storms.
- Never put "thousands of rainfall scenarios" on a slide.
- Never headline the 35 per run or the CPU-to-GPU factor.