===== model=claude-mythos-5-2 stop=end_turn in=5316 out=12698 =====

**Verdict: not ARIA-worthy on Sunday. It becomes worth a seed when the claim changes from "we can find the ground that matters in a model" to "measuring that ground predicts a real flood better", with a named experiment that could kill it.** Nothing about ARIA was checked tonight; my recollections and confidence are in section 7.

## 1. The honest gap

A programme director would pass because nothing here has touched the world. Every result is one model agreeing with another on the same terrain file, on one tile, with sewers as a constant, buildings as walls, and no real flood to compare against. What holds is a screen for which ground can matter, and every test of how much failed. Speed and "rain needed to flood a point" are prior art, and the novelty claim rests on abstract-level searches with Lowe's dissertation unread. It is also a method without a thesis: no stated belief that would change what is possible if true. And one builder with no hydrologist cannot yet say whose streets and data would test it.

## 2. The thesis

**Strongest: the measurement thesis.**

> Which buildings flood first in a cloudburst is decided by a few percent of the ground, most of it not at the building. The largest correctable error in building-level prediction is centimetre-scale relative height at those places (kerbs, thresholds, dropped crossings). If so, a model can name the square metres worth measuring, a phone-grade instrument can measure them, and measuring a chosen 1% of a city improves who-floods-first prediction more than re-surveying all of it. This is wrong if controlling ground is not sparse beyond this tile, if national LiDAR is already right at those cells, or if sewer behaviour swamps terrain.

- **Supports:**
  - 2.7% of open ground moves any building, and 78% of that is more than 5 m away.
  - 0 of 87 dismissed patches moved anything in the solver.
  - Short-range error moves critical rainfall 9 to 10 mm per 5 cm.
  - A chosen 1% cut the spread 40% in the fill model, against 0% for a random 1%.
- **Contradicts:**
  - The solver pilot interval (0.46 to 1.01) includes no effect, and it has no random arm.
  - The first selection method failed (24%).
  - The 3 m correlation length is unsupported; at the 65 to 100 m one variogram gives, the effect is about 3 mm.
  - Abily et al. ranked measurement error well below resolution and feature inclusion.

**Why strongest:** it needs only the part that held (which ground), not the part that failed (how much). It also contradicts where the field spends money and has a cheap control arm.

**Computation thesis (best proven, least ambitious).** Depression hierarchies admit exact, local, millisecond counterfactuals, so exhaustive what-if over a city is laptop-scale and is a no-miss screen for a full solver.
- **Supports:** 441,324 depths identical to brute force; about 200x faster; 342,316 what-ifs in 10 minutes; 0 missed.
- **Contradicts:** speed is prior art; Lowe is unread; recall was 66% as a flood screen; the derivative approach failed.
- This is a paper and an engine for the measurement thesis, not a programme.

**Intervention thesis (largest payoff, weakest evidence).** Square-metre, centimetre-scale changes chosen exhaustively under a no-harm constraint protect buildings at a tiny fraction of the cost of drainage capacity.
- **Supports:** five patches helped five buildings and harmed none, while the naive set harmed seven; direction was right in 21 of 21; one patch moves 29 of 32 buildings.
- **Contradicts:** it is one design; two patches are within 2 m of their beneficiary; the largest rise was 0.95 cm against a 1 cm line; flip predictions failed (9 of 20, 7 of 12); it depends most on the sewers you have not modelled.
- Treat it as the follow-on if the measurement thesis survives.

## 3. What would have to be true (measurement thesis)

The kill thresholds are my proposals; fix them before the data arrives.

| Must be true | How we find out | Cost | Kill result |
|---|---|---|---|
| Sparsity holds elsewhere, under Environment Agency assumptions | 50 to 100 tiles of national 1 m LiDAR with floodable buildings and their friction and losses | 1 person, 1 to 2 months, GPU-weeks, no fieldwork | Controlling ground above about 20% on most tiles, or controlling cells change for most buildings once buildings are floodable |
| The chosen-ground effect survives the solver | Tonight's full run with a random arm, repeated on other tiles | GPU-days | Ratio of 0.9 or worse, or random 1% does as well |
| National LiDAR is wrong at the chosen cells, at short range | Total-station survey of the chosen 1% and a random 1% on 3 to 5 streets | A surveyor, 2 to 4 weeks in the field, tens of thousands of pounds | Relative error under about 2 cm, or correlated over tens of metres |
| Sewers do not swamp terrain | Coupled sewer-surface model on one or two catchments with water-company asset data, varying gully blockage against terrain | A hydraulic modeller, 3 to 4 months, a data agreement | Drainage uncertainty moves who-floods-first several times more than the chosen ground, or changes which cells are chosen |
| Measured ground predicts a real flood better | Blind hindcast on streets with property-level records: uncorrected, chosen 1%, random 1% | 2 to 3 people, about 6 months, partner data | No gain over the random arm in separating flooded from dry neighbours |
| The measurement is cheap | Phone LiDAR against total station at about 30 kerb-to-threshold sites | 1 person-month | Phone error above about 3 cm over 3 to 5 m (kills the phone route, not the thesis) |

## 4. Is it ARIA-shaped?

**Not as it stands. The measurement thesis could be seed-shaped; the rest is something else.**

- **High-risk:** the thesis is probably false at national scale. Sewers may dominate, and published sensitivity work points the other way.
- **Unconventional:** the model directs the survey; the instrument is a phone; the work was done by one builder with AI agents against pre-set pass lines and logged failures.
- **Who would not fund it:**
  - UKRI peer review would want a hydrologist as lead, validation data, and an answer to Abily first.
  - The Environment Agency buys against a nationally consistent method and cannot take building-level claims.
  - A startup has no buyer, because nobody owns kerb heights and building-level claims carry liability.
- **What it is otherwise:** the computation thesis is a paper plus an open-source tool. The intervention thesis, once validated, is a council or water-company pilot. If no programme director's space covers urban water, quality will not matter and a research-council or Defra flood R&D route is the realistic one.

## 5. First 6 months, about £300k to £400k

Most of the money is three people for six months; the rest is survey, data and compute.

- **Milestone 1 (month 2), generality in silico.** Pass: controlling ground at or below 5% on at least 80% of 50 tiles under Environment Agency assumptions. In the solver, the chosen 1% must cut spread by at least 25%, with an interval excluding zero and at least three times the random arm. Read Lowe in week 1.
- **Milestone 2 (month 4), field measurement on three streets.** Pass: short-range relative error at chosen cells of at least 3 cm RMS against LiDAR, and phone within 2 cm of total station over 5 m. A fail ends the measurement thesis; the intervention thesis could continue.
- **Milestone 3 (month 6), blind hindcast.** Pass: the chosen-1% correction ranks flooded against dry properties better than both the uncorrected model and the random-1% arm, with the metric and line fixed before unblinding.

**Missing people:** a hydraulic modeller with coupled sewer-surface experience; a geomatics surveyor who knows LiDAR terrain error; someone inside a flood authority who can open records and streets.

**Partner:** a London borough holding property-level records from the July 2021 surface-water floods, plus Thames Water for the network. The date and the existence of such records are recollection. The site must move, because Blackfriars has no real flood to test against.

**The experiment that ends the project:** milestone 3. If measured ground does not beat random ground against a real flood, stop.

## 6. Tomorrow and by 26 November

**Do or say:**
1. **Lead with the belief, the control and the failure.** For example: "A few percent of ground decides who floods first. Chosen 1% beat random 1%. Every test of how much failed. Here is the experiment that would kill it."
2. **Measure real ground before the 26th.** Spend one day at Blackfriars with the phone and a borrowed level on the chosen cells and a random set. Whether LiDAR and reality disagree there is the first real-world data point.
3. **Close the cheap holes and arrive with a site.** Read Lowe, finish the solver run with its random arm, replicate the no-harm design, run a second tile with floodable buildings. Name the hindcast street and the partner you have approached.

**Loses them in the first minute:**
1. Opening with 6 ms, 200x or the app. Speed is prior art and it reads as a product.
2. Any claim they can puncture: "nobody has done", "predicts floods", thresholds in mm, or the 31% pilot without its interval.
3. Letting them discover by asking that it is one tile with no real flood and constant sewers. Volunteer these as gaps.

## 7. Nearest ARIA programmes, and how sure I am

**Reasonably sure:**
- Programme directors each own an opportunity space and launch a programme inside it with a published thesis.
- Seeds of up to about £500k fund work inside a space but outside its programme.
- The agency says it wants work other funders would not back and accepts stopping projects.

**Unsure:**
- Whether "what would have to be true" is ARIA's own phrase.
- The current list of spaces, and whether any seed call is open.
- Anything about the Summit.

**Nearest, with low confidence in fit:**
- **Scoping Our Planet.** As I recall it is led by Gemma Bale and Sarah Bohndiek and is about sensing the Earth system. Its programme, Forecasting Tipping Points, concerns ice sheets and ocean circulation. The link is only "where to measure".
- **Future Proofing Our Climate and Weather.** As I recall it is Mark Symes's space and is about climate intervention. It is not a fit.
- **AI-scientist work.** I recall ARIA funding some in 2025, and the Summit's name suggests it. How this was done (agents, pass lines, logged failures) may interest them more than the flooding.

I recall no space with urban flooding in its thesis.