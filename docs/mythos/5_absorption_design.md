===== model=claude-mythos-5-2 stop=end_turn in=4337 out=26679 =====

**Bottom line:** add absorption as "remove a volume of water at a place", with one new mechanism in the solver and a 50-minute go/no-go on the M4 Air at 18:45. Nothing in Bet 1 needs cutting. The honest claim will be about storage on flow paths; grass and tree canopies will almost certainly be nulls.

## 1. Physical representation

Use one mechanism for all four types: a per-cell sink acting on ponded water (rain lands on the cell first). It has two stages:
- **Stage 1:** an instant capacity S1 (surface ponding or open voids).
- **Stage 2:** a capacity S2 filled at rate f (soil or filter media).

Do not lower the ground for rain gardens. That keeps absorption runs free of height changes, so the two mechanisms stay separable.

| Type | S1 (mm) | f (mm/h) | S2 (mm) | Takes per storm | Confidence |
|---|---|---|---|---|---|
| Grass on London clay | 3 | 10 (3–20) | 15 | about 10 mm (5–20) | Medium |
| Permeable paving, lined, 300 mm sub-base at 30% voids | 90 (45–135) | n/a | 0 | 90 mm | Medium-high |
| Rain garden, underdrained | 150 (100–300) | 100 (50–300) | 100 (60–150) | about 250 mm | Medium-high |
| Tree pit with kerb inlet, 4 cells | 375 | n/a | 0 | 1.5 m³ per tree (0.5–3) | Low |

- **Roughness:** n = 0.035 for grass (range 0.03–0.1), unchanged elsewhere. Test it in a separate arm, because a rough patch can raise water upstream.
- **Existing 12 mm/h loss:** keep it everywhere, including on green patches. This slightly double-counts for grass, so the grass result is an upper bound.
- **Sources:** all values are from memory (Rawls's Green–Ampt soil table; the CIRIA SuDS Manual, C753). I trust the orders of magnitude, not the second digit. Check C753 before the slide.

On this tile a 30 mm storm leaves about 4,000 m³ of runoff. A 1,000 m² budget therefore removes at most:

| Type | Volume removed | Share of runoff |
|---|---|---|
| Grass | 10 m³ | 0.25% |
| Permeable paving | 90 m³ | 2% |
| Rain garden | 250 m³ | 6% |

Any large effect has to come from placement.

**Do not claim:**
- **Canopy interception.** It is 1–2 mm on the canopy footprint, under 5% of a cloudburst. Annual interception figures do not transfer. Set it to zero.
- **"Tree planting reduces flooding."** Only an engineered pit with an inlet does, as a small rain garden.
- **"Chances of a flood."** You compute thresholds in mm, not probabilities.
- **Guaranteed capacity.** All capacities assume the store is empty at the start. The model also assumes water on the cell gets in; real rain gardens need kerb inlets that a 1 m DEM cannot see.
- **Permanent removal.** Underdrains return the water to the same sewer later.
- **Cost.** Compare at equal area and equal captured volume instead.

## 2. The scientific question

**Height changes redirect water; absorption removes it. Do they have the same decisive ground?**

The fill model answers this exactly. For receptor b at its critical rainfall R*_b, let C_b be the cells whose marginal rain reaches b's pond, and A_b its rain-weighted area. Then:

- **Fixed depth a absorbed on patch P:** ΔR*_b = a · |P ∩ C_b| / A_b
- **Sink that captures volume v inside C_b:** ΔR*_b = v / A_b

Both are upper bounds, exact until another depression starts spilling in.

**Predictions to commit:**
1. **Different maps.** Absorption leverage is a broad plateau (all of C_b), non-negative everywhere. Height leverage is sparse spikes at passes, with both signs. Absorption is harm-free by construction in the fill model; check it in the solver.
2. **Grass does nothing at these budgets.** With A_b around 10,000 m², 1,000 m² of grass gives under 1 mm.
3. **Sinks work only where they fill.** That means under the pond or on spill paths, which run through the same passes that Bet 1 measures and Bet 3 raises. One strip, three uses.
4. **Robustness.** Because the map is a plateau, absorption placement should survive the 5 cm DEM errors that defeat height placement.
5. **Transit receptors benefit less than volume suggests.** A sink on the path fills before the peak arrives.

Predictions 4 and 5 and the A_b figure are my guesses.

## 3. Experiments, in priority order

All solver arms reuse the P1 baselines. The detection line is 1 cm, as in Bet 3.

| # | What | Where | Runs / time | Control | Pass line |
|---|---|---|---|---|---|
| E0 | Absorption map, A_b distribution, overlap with height map, ceiling table | CPU | about 30 min compute | Brute-force re-bisection on 100 patches | Formula within 2% on at least 95%. Kill if best 250 m³ placement lifts fewer than 5 receptors by 10%. |
| E1 | **Go/no-go**, single-receptor designs | GPU | 144 runs, 50 min | Three control arms (below) | Below |
| E2 | Budget designs at 250, 500, 1,000 m² | GPU | about 150 runs, 52 min | Random, park rule, lowest ground | Below |
| E3 | Transit receptors | GPU | 64 runs, 22 min | Same area 30 m off the path | At least 4 of 8 drop 1 cm on-path; at most 1 of 8 off-path |
| E4 | Robustness to DEM error | CPU, then GPU | 100 terrains in minutes; 48 runs, 16 min | Random design | Targeted beats random median 3x on at least 80% of terrains |
| E5 | Exchange rate with height | GPU | 6 runs, added to Bet 3 | Bet 3's own patches | Report only |

**E1 detail.** Use 12 receptors (8 storage-controlled, 4 transit) and 3 storms. Fix the unit size from E0 so the predicted median drop is 3 cm; probably about 100 m². Four arms of 36 runs each:
- **Targeted:** rain garden placed by the map.
- **Near-null:** same area within 100 m but outside C_b.
- **Random:** same area on random open ground.
- **Grass:** the targeted footprint with grass parameters.

Pass lines:
- At least 6 of 8 storage-controlled targets drop by 1 cm or more.
- Near-null and random move at most 10% of receptor-storm pairs.
- Median near-null effect is under half the targeted effect.
- No receptor rises by 1 cm.
- Targeted sinks reach at least 50% of capacity.
- Absorbed volume closes mass to 0.1%.

Grass is a committed prediction of no effect, not a pass line.

**E2 detail.**
- **Arms:** per budget, one targeted design, one lowest-ground, one park rule (largest open areas at least 20 m from buildings; commit the rule) and six random.
- **Extras:** permeable and grass variants at 1,000 m²; a 12-level ladder for the headline design; random designs at 2,000, 4,000 and 8,000 m² to find the equal-effect area.
- **Pass:** targeted 1,000 m² protects at least 5 receptors and harms none; random median is at most a third of that.

**E5 detail.** Put a rain garden on Bet 3's best patches and find how many m² match one 5 cm patch.

## 4. Searching for where to put the budget

1. **Contributing sets.** For each receptor, evaluate the fill model at R*_b, add a tiny volume to each leaf in turn, and record which leaves raise b's level. That is C_b and A_b. The cost is leaves × receptors × 0.5 ms, with no tree rebuild. Bet 2's reverse sweep gives the same thing as the derivative with respect to leaf inputs; use it as a cross-check.
2. **Throughput T(c).** Accumulate net rain downslope within each leaf. Add each full depression's overflow along the steepest path from its pass. Treat cells under b's pond as unlimited.
3. **Score.** score(c) = Σ_b 1[c ∈ C_b] · min(capacity, T(c)) / A_b.
4. **Greedy search.** Pick the best patch, subtract its capture from downstream throughput, and re-score each pick by exact re-bisection (about 10 ms). Maximise the sum of ΔR*_b, truncated at the design storm. Greedy is a heuristic here, not optimal.
5. **Transit receptors.** Add time-integrated flux to one baseline solver run per storm. Trace upstream from each receptor along that field. Rank cells by throughput.
6. **Verify.** Run 3 storms per design, then the 12-level ladder for the headline design. The ordering property makes that a valid bracket.

## 5. Pitch and number

"The same map that says which centimetres to measure says where a rain garden earns its space: 500 m² on the decisive flow paths protects [N] buildings and, unlike a height change, harms none. Grass and tree canopies barely move a cloudburst on London clay; storage on the flow path does."

**The number:** the placement multiplier, meaning the m² of randomly placed rain garden needed to match 500 m² placed by the map, solver-confirmed.

## 6. What to cut

GPU time is not the constraint. The whole programme is about 2.4 GPU hours, and both machines have overnight slack.

**Schedule**
- **Now:** a third agent builds E0 and the solver sink on a separate branch. With sinks off, the output must be bit-identical to the current solver.
- **18:45, M4 Air:** E1 runs before the second-tile replicate, which slips 50 minutes.
- **About 22:40, M4 Air:** E2 to E4.
- **M3 Pro:** unchanged. E5 is added to Bet 3 verification.

**Cut**
- Separate tree and grass arms beyond the single null.
- Roughness beyond 6 runs.
- The 250 m² budget if time is short.
- Any second-tile absorption run.
- All cost claims.

**Rules**
- If E1 fails or is not ready by 19:00, the extension becomes one slide line: the E0 ceiling table.
- If Bet 1's pilot dies at 17:45, absorption takes the M3 Pro.