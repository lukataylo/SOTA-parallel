# Prior work on terrain-feature control of urban surface-water flooding, where-to-survey methods, and fast depression-based flood screening

Reading guide. "Full text read" means I extracted and read the paper or report itself. "Abstract/snippet only" means the claim rests on a search-result summary or abstract and the full text was not opened (several publisher and repository sites returned HTTP 403 or bot checks: MDPI, CACM, ResearchGate, Southampton eprints, Duke, DOAJ, klimatilpasning.dk). The whole note rests on about 30 web searches and about 20 page fetches, of which roughly half the fetches failed. Per-topic search counts are given in each Gaps section.

## Claim-by-claim: nearest prior work and how it differs

### Takeaway
Claims (1) and (3) are the most exposed to overclaiming. "Rain depth needed before a location floods" from a depression (merge-tree) hierarchy already exists in Danish practice (Blue Spot Model level 2, 2010), in a commercial product (SCALGO Live point query and spill-point display) and in the algorithms literature (Rav, Lowe and Agarwal 2017). What I did not find is attribution of a per-building threshold to specific spill-point cells, propagation of LiDAR error to that threshold, causal confirmation in a 2D solver, or use of it to direct re-survey.

### Cited Findings

Claim 1 (per-building critical rainfall depth, controlled by a few square metres at spill points):
- Nearest: Danish Road Institute Blue Spot Model, level 2 "Rain sensitivity for individual depressions": a "'Risk map' with the amount of precipitation needed to fill low-lying areas. Assuming no drainage from depressions". It is per depression (depressions over 100 m3), for road stretches, on a 1.6 m grid over 7,500 km2. Not per building, and no attribution to spill cells (full text read). — [SWAMP Report 3, The Blue Spot Model, 2010](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf)
- Nearest commercial: SCALGO Live Flash Flood Map point query returns "The amount of rain required for the chosen point to flood", plus depth and depression volume; spill points carry volume, area and rain needed before the spill point is reached. This is per clicked point, not a per-building output, and the documentation page lists no building layer. — [SCALGO Live documentation, Flash Flood Map](https://scalgo.com/en-US/scalgo-live-documentation/analysis/flash-flood-map)
- SCALGO added display of spill-point locations on 1 Nov 2024: "When a depression overflows, the water leaves the depression through a spill point." — [SCALGO, Spill points on flash flood map and depression map](https://scalgo.com/en-US/scalgo-live-documentation/about/whats-new/spill-points-on-flash-flood-map-and-depression-map)
- Nearest algorithmic: Rav, Lowe and Agarwal, "Flood Risk Analysis on Terrains" (SIGSPATIAL 2017; CACM research highlight 2020) implement terrain-flood and point-flood queries on a merge tree whose leaves are sinks and whose internal nodes are saddles (snippet only; full text 403). — [dblp record](https://dblp.org/rec/conf/gis/RavLA17); [CACM version](https://cacmb4.acm.org/magazines/2020/9/246944-flood-risk-analysis-on-terrains/fulltext)
- Buildings plus fill-up rainfall as a GIS workflow: Balstrøm's ArcGIS lessons compare bluespots with building locations, and an extended model "also calculates the volumes of bluespots and the amounts of rainfall that would be required to fill them" (snippet only). — [ArcGIS Learn, Find areas at risk of flooding in a cloudburst](https://learn.arcgis.com/en/projects/find-areas-at-risk-of-flooding-in-a-cloudburst)
- Baby et al. (2021, Journal of Civil Engineering and Architecture) apply a bluespot screening model to Inverloch, Victoria; a search summary says the authors state results suffice to identify flood-risk thresholds for single buildings. I could not open the paper, so treat this as unverified. — [Structurae record](https://structurae.net/fr/litterature/article-de-revue/finding-areas-at-risk-from-floods-in-a-downpour-using-the-lidar-based-elevation-model)
- On decimetre-scale control of flooding by small street features (but not spill points of a depression hierarchy): de Almeida, Bates and Ozdemir (2018) found "localised, decimetric-scale alterations in the elevation of streets can lead to remarkable differences" in inundation, using a 2D shallow-water model on 10 cm terrain (abstract only). — [Bristol research portal](https://research-information.bris.ac.uk/en/publications/modeling-urban-floods-at-submeter-resolution-challenges-or-opport/)

Claim 2 (realistic LiDAR error moves the critical rainfall by tens of percent):
- Nearest: Abily et al. (2016) propagated a LiDAR-scale error (independent normal noise, standard deviation 0.2 m, on a 1 m DEM) through a 2D shallow-water model of Nice (17.8 km2, river flood). Output was maximum water depth at 20 points, not a rainfall threshold. Mean first-order Sobol indices: 0.40 for level of detail of above-ground features, 0.24 for grid resolution, 0.06 for measurement error (full text read). — [Abily et al. 2016, arXiv 1603.07279](https://arxiv.org/pdf/1603.07279)
- Lindsay and Creed (2006) perturb a DEM with Monte Carlo error fields and report the probability that each depression exists. Output is depression existence, not flood thresholds (secondary sources only). — [digital-rivers documentation citing the paper](https://serapeum-org.github.io/digital-rivers/main/examples/05_stochastic_depressions/)
- Aaron Lowe's 2021 Duke dissertation is reported to extend merge-tree flood-risk algorithms to uncertain terrains with Monte Carlo methods (snippet only; page blocked). This is the closest algorithmic precedent and should be read before claiming novelty. — [Duke dissertation record](https://dukespace.lib.duke.edu/items/241ec42f-c64b-487a-b422-d2cc5e716df1)

Claim 3 (identify controlling ground from a fill-spill-merge hierarchy in seconds; confirm causally in a 2D solver):
- Speed is established prior art: Fill-Spill-Merge processes a dataset of similar size to 4,176,000 cells in 8.7 s, against about 33 h for FlowFill (full text read). — [Barnes, Callaghan and Wickert 2021, Earth Surface Dynamics 9, 105-121](https://esurf.copernicus.org/articles/9/105/2021/)
- Spill points as named outputs are established: malstroem outputs pour points, "the point where water leaves a bluespot when filled to maximum capacity". — [malstroem README](https://github.com/Septima/malstroem)
- Editing street elevation in a 2D solver and observing changed flooding is established (de Almeida et al. 2018, above), but the edits were not chosen by a depression hierarchy.
- I found no study that picks cells from a depression hierarchy and then perturbs exactly those cells in a 2D shallow-water model as a causal test.

Claim 4 ("measure where it matters"):
- Nearest in spirit: Abily et al. produce spatial Sobol maps ranking which topographic uncertainty source dominates at each location; they rank sources, not cells to re-survey. — [Abily et al. 2016](https://arxiv.org/pdf/1603.07279)
- Adjoint sensitivity maps with respect to topography exist for 2D flood models (Monnier et al., "Inverse computational algorithms for flood plain dynamic modelling", Lèze river; abstract only): "original sensitivity maps with respect to the (friction, topography) fields are performed and discussed". — [DassFlow lineage, Pujol, Garambois and Monnier 2022, GMD 15, 6085](https://gmd.copernicus.org/articles/15/6085/2022/)
- I found no study that ranks terrain cells by influence on a flood outcome and then acquires survey data there.

Claim 5 (exact one-sweep sensitivity of the depression-filling solution):
- Nearest: in topological data analysis the persistence map is known to be piecewise linear with 0/1 partial derivatives. Carrière et al. (ICML 2021): "The output can be seen as a reindexing of the input" and "This implies that every partial derivative is either 1 or 0." Depression spill elevations are the death values of sublevel-set 0-dimensional persistence, so this result covers the spill-elevation part of the claim. The paper does not mention terrain, merge trees or hydrology. — [Carrière et al. 2021, arXiv 2010.08356](https://ar5iv.labs.arxiv.org/html/2010.08356)

### Inferences
- Safe wording for claim 1: the per-location "rain needed to flood" quantity is prior art; the contribution is tying it to buildings, localising it to specific spill cells, and quantifying the distance between the controlling cells and the building.
- Safe wording for claim 5: the derivative of spill elevations with respect to cell elevations follows from known persistence results; any novelty lies in the derivative of the volume-based rainfall threshold (which also depends on depression storage and contributing area) and in computing it in one sweep on a fill-spill-merge hierarchy. That decomposition is my inference, not something a source states.
- Abily's finding that measurement error ranks last (index 0.06) is a possible counter-argument to claim 2. It differs in three ways: river flooding with depths around 0.5 m, spatially uncorrelated error, and depth rather than a threshold as output. The team should address it directly.

### Gaps
- Rav, Lowe and Agarwal and Lowe's dissertation could not be opened. Whether they compute a minimum rain volume per query point, and what the uncertain-terrain experiments report, is unverified. This is the largest single risk to claims 1 and 2.
- No source found for per-building thresholds attributed to spill cells (3 searches), or for hierarchy-guided perturbation in a 2D solver (no dedicated search beyond those 3). Weak evidence of absence.

## What the fast depression-based and rapid inundation methods compute, at what scale, and their documented limitations

### Takeaway
All of these are static or quasi-static volume-balance methods on a depression hierarchy; several report rain depth to fill a depression or flood a point, none documents a per-building threshold or spill-cell attribution as a standard output. Validation against 2D models exists for Safer_RAIN and RFSM, and is absent from the Blue Spot report and malstroem README.

### Cited Findings

Blue Spot Model (Danish Road Institute, SWAMP Report 3, May 2010; full text read):
- Three levels: level 1 terrain screening for depressions; level 2 catchments and rain sensitivity; level 3 hydrodynamic modelling (a 1D-1D MIKE example at Brande). — [SWAMP Report 3](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf)
- Data: LiDAR grid "1.6 x 1.6 m ... and a height accuracy of 10 – 25 cm at well-defined surfaces"; 7,500 km2, 2.9 billion points, in mid and southern Jutland. — [SWAMP Report 3](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf)
- Level 2 output: "depressions greater than 100 m3 with indication of how many millimetres of rain needed to fill the depressions", tabulated for imperviousness of 20, 40, 50, 60, 80 and 100%; depressions needing under 25 mm are flagged for follow-up. — [SWAMP Report 3](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf)
- Stated limitations: the screening levels "are not suited for more detailed modelling of flood dynamics"; "If bridges are not removed they will appear as 'dikes' where water is likely to accumulate to create false blue spots"; "A resolution of 1.6 x 1.6 m used in this study may result in an inaccurate description of roads"; "Very detailed boundary conditions such as the shape and height of the curves may completely change the surface flow paths." — [SWAMP Report 3](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf)
- Funnel reported for Danish state roads: about 500,000 hollows at tier 1, about 5,000 at tier 2, 11 final locations (secondary summary). — [Climate-ADAPT tool page](https://climate-adapt.eea.europa.eu/en/metadata/tools/the-blue-spot-model-a-key-tool-in-assessing-flood-risks-for-the-climate-adaptation-of-national-roads-and-highway-systems)

Arc-Malstrøm and malstroem:
- Balstrøm and Crawford (2018), Computers and Geosciences 116, 64-73: a 1D screening method on geometric networks to detect "extents and capacities of local landscape sinks", "without hydrodynamic components"; applied to the Danish 0.4 m terrain model; said to apply mainly where runoff is largely 1D (abstract only). — [University of Copenhagen record](https://test01.ku.dk/:obvius/pureproxy/3974268/da/publications/arc-malstr%C3%B8m-a-1d-hydrologic-screening-method-for-stormwater-asse)
- malstroem (Septima, open source) computes filled DEM, flow direction and accumulation, bluespots, local watersheds, pour points, flow paths between bluespots, fill volume and spill-over at a specified rain incident, and approximate level and extent of partially filled bluespots. Rain is a scalar in mm or a raster. — [malstroem README](https://github.com/Septima/malstroem)
- Stated assumptions, verbatim: "malstroem assumes that the terrain is an impermeable surface"; "malstroem does not know the concept of time"; "the capacity of surface streams is infinite no matter the width or depth"; "Water flows from one cell to one other cell (the D8 method)"; "No attempt is made to model how water actually flows within the bluespots." — [malstroem README](https://github.com/Septima/malstroem)
- The README mentions neither building-level outputs nor a rain-depth-to-fill field, and gives no validation. — [malstroem README](https://github.com/Septima/malstroem)

SCALGO Live Flash Flood Map:
- "a simple, powerful, stationary event-based screening model"; "The rain is applied uniformly and instantaneously across the terrain"; no temporal component. Outputs: flooded areas, flow accumulation, watersheds, point query of rain required to flood, spill points. — [SCALGO Live documentation](https://scalgo.com/en-US/scalgo-live-documentation/analysis/flash-flood-map)
- Sewers are not in the default map; a Danish variant from 2022 adds infiltration and drainage (snippet). — [SCALGO, national flash flood map with infiltration and drainage](https://scalgo.com/en-US/scalgo-live-documentation/about/whats-new/national-flash-flood-with-infiltration-and-drainage-for-denmark)
- The underlying algorithm (Revsbæk, Raza, Rav, Arge) computes each depression's excess volume on a merge tree and processes the 1.6 m model of Denmark "in 2 hours on a standard workstation"; "We assume that water only flows on the surface of the terrain" (poster, full text read). — [MADALGO poster](https://cs.au.dk/fileadmin/site_files/cs/AA_pdf/Gerth_Madalgo_poster/16-rav.pdf)

Safer_RAIN (Samela et al. 2020, Water 12, 1514; abstract/snippet only):
- Hierarchical filling-and-spilling on a LiDAR DEM with spatially distributed rainfall and pixel-based Green-Ampt infiltration; case studies Lignano Sabbiadoro and Rimini; compared against ground evidence and a 2D hydrologic-hydraulic model; sensitivity and specificity "up to 71% and 99%". — [Samela et al. 2020](https://doi.org/10.3390/w12061514)
- Documented limitation from the authors' group: against 2D models it tends to underestimate flooded extent, attributed to no backwater effects and a single flow-path constraint. — [EGU26-13010](https://meetingorganizer.copernicus.org/EGU26/EGU26-13010.html)

RFSM and RFSM-EDA (HR Wallingford; 2008 paper full text read):
- RFSM spreads flood volumes from breached or overtopped defences across Impact Zones (depressions around accumulation points); the "communication level" is the level at which water spills to a neighbour. Input is defence volume, not rainfall; scale is floodplains up to 968 km2. — [Lhomme et al. 2008, FLOODrisk](https://eprints.hrwallingford.com/695/1/HRPP361-Recent_development_and_application_of_a_rapid_flood_spreading_method.pdf)
- Validation against TUFLOW at four sites (mean depth deviation, fit, bias): Carlisle +0.06 m, 98.4%, +1.2%; River Brit -0.06 m, 81.8%, -7.7%; Boston +0.04 m, 56.7%, +4.1%; River Lee +0.07 m, 54.3%, -23.6%. Boston: TUFLOW 15 h, RFSM 5 s. — [Lhomme et al. 2008](https://eprints.hrwallingford.com/695/1/HRPP361-Recent_development_and_application_of_a_rapid_flood_spreading_method.pdf)
- Limitation: the direct version predicts the final state only. RFSM-EDA (Jamieson et al. 2012) adds a diffusion-wave solver with acceleration term on sub-element impact zones and is described as "highly accurate for all but the shallowest of depths" on the Environment Agency 2D benchmarks (abstract only). — [Jamieson et al. 2012](https://eprints.hrwallingford.com/859)

Fill-Spill-Merge (Barnes, Callaghan and Wickert 2021; full text read in part):
- Routes a given water volume through a depression hierarchy; 90-2,600 times faster than Jacobi iteration; landscape-scale test sites (Sangamon River, Río Toro), not urban; no building output and no validation against observed floods found in the sections I read. — [Barnes et al. 2021](https://esurf.copernicus.org/articles/9/105/2021/)
- Authors note it can "assess which depressions are most important", and defer time-stepped use to future work. — [Barnes et al. 2021](https://esurf.copernicus.org/articles/9/105/2021/)

FwDET and HAND (snippets only):
- FwDET derives depth from an observed inundation extent plus a DEM; it has "considerable bias" where the two disagree. It needs an extent as input, so it gives no rainfall threshold. — [USGS publication record](https://pubs.usgs.gov/publication/70195403)
- A 2026 HESS study reports that purely elevation-based approaches can overestimate floodwater connectivity by neglecting microtopographic barriers unresolved in a 0.5 m DEM, infiltration and stormwater infrastructure. — [HESS 30, 2183, 2026](https://hess.copernicus.org/articles/30/2183/2026/)

### Inferences
- None of the six tool families documents sensitivity of its outputs to elevation error, even though the Blue Spot report itself states a 10-25 cm height accuracy and that kerb-scale detail can change flow paths.
- The common documented blind spots are time, sewers, backwater and momentum. A team using fill-spill-merge inherits them and should say so.

### Gaps
- Safer_RAIN full text not read: DEM resolution, runtime and exact benchmark set-up are unverified.
- Blue Spot Concept Report 181 (the companion report) could not be fetched (DNS failure).
- HAND in flat urban pluvial settings: 1 search, nothing specific found.
- 7 searches and 6 fetches cover this question.

## Stochastic depression analysis and Monte Carlo DEM-error studies; propagation to building-level thresholds

### Takeaway
Monte Carlo DEM-error work exists for depression existence, for flood depth at points, and for first-floor elevation, but I found nothing that propagates DEM error to a per-building rainfall threshold. That absence rests on 3 searches and is weak evidence.

### Cited Findings
- Lindsay and Creed (2006), "Distinguishing actual and artefact depressions in digital elevation data", Computers and Geosciences 32(8), 1192-1204: Monte Carlo error grids are added to the DEM, each realisation is filled, and the per-cell probability of being in a depression is the share of realisations in which it is. Implemented in Whitebox. — [digital-rivers documentation](https://serapeum-org.github.io/digital-rivers/main/examples/05_stochastic_depressions/)
- A USGS report citing it notes that DEM analysis without field verification can only classify depressions as likely or unlikely to exist. — [USGS SIR 2024-5134](https://pubs.usgs.gov/publication/sir20245134/full)
- Abily et al. (2016): 2,000 simulations; combined topographic uncertainties changed maximum depth by "a range that can be up to 0.71 m"; measurement error was never the top-ranked source at any of 20 points. — [Abily et al. 2016](https://arxiv.org/pdf/1603.07279)
- A 2016 Remote Sensing paper uses Monte Carlo simulation of LiDAR error to assess first-floor elevation uncertainty for depth-damage estimates (snippet only). — [Remote Sensing 8(7), 604](https://www.mdpi.com/2072-4292/8/7/604)
- Driemel, Haverkort, Löffler and Silveira (2011) treat each vertex elevation as an interval and compute minimal and maximal watersheds; deciding watershed membership is NP-hard in the surface-flow model. Worst-case bounds, not probabilistic, and no flood volumes. — [Flow Computations on Imprecise Terrains, arXiv 1111.1651](https://arxiv.org/pdf/1111.1651)

### Inferences
- Lindsay and Creed's method is the direct ancestor of any "perturb the DEM and refill" experiment; the new element would be the output variable (rainfall threshold per building) and a spatially correlated error model.

### Gaps
- Lindsay and Creed's own numbers (realisations, error magnitude, results) were not obtained; the hosted PDF has been decommissioned.
- Lowe (2021) on uncertain terrains not read (see above).

## Effect of kerbs, thresholds, camber, walls and other sub-grid features on urban pluvial model results

### Takeaway
It is well established that 10 cm-scale features (kerbs, camber) change modelled urban flooding, with reported effects of roughly a third on depth and velocity. The literature frames this as a resolution or feature-inclusion issue across the whole domain, not as a few identifiable controlling cells.

### Cited Findings
- Ozdemir et al. (2013), HESS 17, 4015-4030 (full text read): LISFLOOD-FP on terrestrial LiDAR at 10 cm, 50 cm and 1 m in Alcester, UK (10 cm grid of 3,616,663 cells). "Maximum water depths increase ∼ 37 % when the model resolution increases from 1 m to 10 cm"; velocities in kerb-side channels about 32% higher. Changing friction "is not sufficient to recover the results of the 10 cm simulation at 1 m resolution". — [Ozdemir et al. 2013](https://hess.copernicus.org/articles/17/4015/2013/hess-17-4015-2013.pdf)
- Same paper: "A 10 cm kerb height drop when sampled at typical airborne LiDAR resolutions (1–2 m) does not create gradients above 10 %, and such features are often not even correctly seen by the sensor (Sampson et al., 2012)." Survey positional accuracy was ±5 cm. — [Ozdemir et al. 2013](https://hess.copernicus.org/articles/17/4015/2013/hess-17-4015-2013.pdf)
- Fewtrell et al. (2011) benchmarked diffusive and inertial LISFLOOD-FP on terrestrial LiDAR from 50 cm to 5 m and stressed the need to represent camber and kerbs explicitly (snippet only). — [Bristol research portal](https://research-information.bris.ac.uk/en/publications/benchmarking-urban-flood-models-of-varying-complexity-and-scale-u/)
- de Almeida, Bates and Ozdemir (2018), J. Flood Risk Management 11(S2), S855-S865: decimetre-scale street alterations on 10 cm terrain change inundation markedly; authors propose engineering street surfaces as low-cost flood management (abstract only; quantitative results not obtained). — [Bristol research portal](https://research-information.bris.ac.uk/en/publications/modeling-urban-floods-at-submeter-resolution-challenges-or-opport/)
- Abily et al. (2016): inclusion level of above-ground features (walls, kerb-like concrete structures) had mean Sobol index 0.40, the largest of three sources. — [Abily et al. 2016](https://arxiv.org/pdf/1603.07279)
- Leitão et al. (2016) note that misrepresented bridges, tunnels or continuous walls in DEMs can bias flood estimates (snippet). — [Leitão et al. 2016, HESS 20, 1637](https://hess.copernicus.org/articles/20/1637/2016/hess-20-1637-2016.pdf)

### Inferences
- "A few centimetres to a decimetre matter" is prior art. The team's distinct point would be locality: which cells, how few, and how far from the affected building.

### Gaps
- Sampson et al. (2012), Yu and Lane, Hunter et al., Mason et al., and Schubert and Sanders were not retrieved; no findings are reported for them here.
- Door thresholds and speed humps specifically: 1 search, nothing found.
- 3 searches cover this question.

## Where to survey: survey design, value of information, targeted DEM improvement

### Takeaway
I found no study that ranks terrain cells by influence on a flood outcome and then collects elevation data there. This rests on 4 searches (two in extended mode) and is weak evidence of absence; adjacent work exists on sensitivity maps, sensor placement and cheaper local data capture.

### Cited Findings
- Spatial Sobol maps rank topographic uncertainty sources by location in a 2D urban flood model. — [Abily et al. 2016](https://arxiv.org/pdf/1603.07279)
- A 2024 Journal of Hydrology paper maps gradient-based sensitivity patterns with adjoint code in a 2D urban flood model and calibrates friction with high-water marks; target is parameter inference, not survey design (snippet only). — [Journal of Hydrology 2024](https://www.sciencedirect.com/science/article/abs/pii/S0022169424012812)
- A sensitivity-based flow-depth sensor network design exists for real-time flood modelling; it places water-level sensors, not topographic surveys (snippet only). — [Real-time flood inundation modeling with flow resistance parameter learning](https://www.researchgate.net/publication/387699706_Real-Time_Flood_Inundation_Modeling_With_Flow_Resistance_Parameter_Learning)
- Caution from meteorology: best observation targets were "located away from regions of greatest adjoint and ensemble sensitivity" (snippet only). — [Comparing adjoint and ensemble-sensitivity analysis](https://www.researchgate.net/publication/249621559_Comparing_Adjoint_and_Ensemble-Sensitivity_Analysis_with_Applications_to_Observation_Targeting)
- Leitão et al. (2016) assess UAV-derived DEMs for urban overland flow and argue UAVs enable frequent, local, affordable elevation updates; they do not say where to fly. — [Leitão et al. 2016](https://hess.copernicus.org/articles/20/1637/2016/hess-20-1637-2016.pdf)
- An EGU 2006 abstract describes a benefit analysis for the optimal number of cross-sections to survey for a 1D model (abstract only). — [EGU06 abstract](https://meetings.copernicus.org/www.cosis.net/abstracts/EGU06/08204/EGU06-J-08204.pdf)

### Inferences
- The observation-targeting result implies that high sensitivity alone does not define the best place to measure; sensitivity multiplied by prior uncertainty at that location is the relevant quantity. The team should frame "where it matters" that way.

### Gaps
- Smartphone or mobile LiDAR for kerbs and thresholds in flood models: 1 search, nothing found.
- Formal value-of-information or Bayesian experimental design for DEM surveys: 2 searches, nothing found.

## Sensitivity analysis: adjoint shallow-water models, automatic differentiation, and exact sensitivity of depression filling or merge trees

### Takeaway
Adjoint and automatic-differentiation sensitivities to topography exist for shallow-water models, and topological data analysis supplies both stability bounds and an exact piecewise-linear derivative for persistence. I found no paper stating an exact sensitivity of priority-flood or fill-spill-merge outputs to elevation (2 searches plus 1 fetch; weak evidence).

### Cited Findings
- DassFlow provides a 2D shallow-water forward solver and adjoint generated with the Tapenade automatic differentiation tool; a 2022 upgrade differentiates the whole tool chain. — [Pujol, Garambois and Monnier 2022](https://gmd.copernicus.org/articles/15/6085/2022/)
- Sanders and Katopodes derived a continuous adjoint and sensitivity equations for the shallow-water equations with bottom friction (as described in a later paper; original not retrieved). — [arXiv 2404.05556](https://arxiv.org/html/2404.05556v1)
- Persistence map derivative: each diagram coordinate is a copy of one input value, so partial derivatives are 0 or 1 on each cell of a semi-algebraic partition; the subdifferential depends on tie-breaking. — [Carrière et al. 2021](https://ar5iv.labs.arxiv.org/html/2010.08356)
- Stability: merge-tree interleaving distance is bounded by the sup-norm distance between the two functions. — [Functional data representation with merge trees, arXiv 2108.13147](https://arxiv.org/pdf/2108.13147)
- Merge-tree edit distances vary in stability under minimal vertex perturbation; authors say formal stability analyses "remain underexplored". — [Wetzels and Garth 2025, arXiv 2508.02352](https://arxiv.org/pdf/2508.02352)
- A SoCG 2025 paper notes a steepest-descent watershed method is unstable under minor terrain changes on low-relief terrain. — [SoCG 2025](https://drops.dagstuhl.de/storage/00lipics/lipics-vol332-socg2025/html/LIPIcs.SoCG.2025.70/LIPIcs.SoCG.2025.70.html)

### Inferences
- Stability theorems bound how far spill elevations can move (by at most the largest elevation change) but say nothing about volumes, so they do not bound a rainfall threshold in a flat city where small level changes shift large storage.
- The tie-breaking dependence noted by Carrière et al. applies to any "exact" sensitivity claim: the derivative is undefined where two candidate spill cells have equal elevation, which is where the controlling cell switches.

### Gaps
- Castaings et al. and the original Sanders and Katopodes papers were not retrieved.
- No search was run on differentiable flow-routing in landscape-evolution or machine-learning hydrology codes; such work may exist.

## UK designing-for-exceedance practice (CIRIA C635 and C738)

### Takeaway
UK guidance already treats kerbs as levers for steering exceedance flow, but I could not access C635 or C738 themselves, so whether practice identifies specific controlling kerbs or thresholds analytically is unanswered. This rests on 1 search.

### Cited Findings
- C635 (2006) gives good practice for design and management of urban drainage to reduce impacts of exceedance, covering overland flood conveyance. — [CIS record for C635](https://cis.ihs.com//CIS/document/279126)
- Practice description: "We may use highways to channel water, raise or drop kerbs to redirect water, and use car parks and green open space to store it." — [susdrain, drainage exceedance](https://www.susdrain.org/delivering-suds/drainage-exceedance/background/background.html)
- C738 (2014) came from project RP991 on why uptake of designing for exceedance had been slow; outputs are recommendations, lessons, case studies and a literature review. — [susdrain, encouraging uptake](https://www.susdrain.org/delivering-suds/drainage-exceedance/Encouraging-uptake/index.html)
- A SuDS source says there are no guidelines on the return period to use for exceedance design. — [susdrain, drainage design and standards](https://www.susdrain.org/delivering-suds/drainage-exceedance/stakeholders/drainage-design-and-standards.html)

### Inferences
- Because raising or dropping kerbs is a recognised intervention, the idea that kerb-scale ground controls flow routes is familiar to UK practitioners; the unverified question is whether they locate the controlling kerb by analysis or by site judgement.

### Gaps
- C635 and C738 text not read (paywall and sign-in). No design values, low-spot identification procedure or threshold-level guidance could be confirmed.
