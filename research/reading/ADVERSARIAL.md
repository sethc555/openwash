# OpenWASH — adversarial verification (2026-07-04)

_Ran a refutation-focused Semantic Scholar scan (`research/s2_refute_results.md`, 151 papers)
trying to DEFEAT each load-bearing value in the substrate. Verdict per attack vector below:
what survived, what got dented, and what turned out to be a scope gap the substrate doesn't
cover at all._

## Verdict summary

| Attacked value | Outcome | Strongest challenger |
|---|---|---|
| 6/7-log irrigation targets | **survives** (but rotavirus-indexed — see gap) | Ito 2017 (scenario-specific LRVs, same QMRA frame) |
| ≤1 helminth egg/g threshold | **value survives, verifiability dented** | Ravindran 2019, Maya 2019 (assay recovery/viability) |
| Ascaris T90 / persistence | **survives, corroborated** | Naidoo 2018–20, Manga, Fidjeland |
| Ammonia model (Nordin) | **survives, further corroborated** | Decrey 2015/17, Fidjeland 2016, Muizzati 2023 |
| Urine 6-mo storage | **survives, refined** | Ahmed 2017, Decrey & Kohn 2017 |
| Setback 30 m / clearance | **survives, caveat reinforced** | Islam 2016, Hinton 2024, Gwenzi 2023 |
| WHO 2006 superseded? | **no** — SSP (2015) reproduces it, no replacement | — |
| **Thermal ≥50 °C model** | **DENTED — too conservative at mesophilic temps** | **Harroff 2019; Espinosa 2020 (updated curves)** |
| Die-off constants currency | **DENTED — a 2026 meta-analysis exists** | **Muoghalu 2026; Espinosa 2020** |

## Genuine hits (folded into `data/limitations.yaml`)

### 1. The thermal model is too conservative at mesophilic temperatures — partial defeat
Harroff et al. 2019 (*Water Research X*, OA) tested this head-on: current guidelines hold that
"thermal treatment alone cannot inactivate Ascaris eggs below 45 °C," and Harroff shows that is
**incorrect** — mesophilic (< 45 °C) treatment *does* inactivate Ascaris given time, and the
conservative rules "may hamper development of simple, but effective sanitation." My engine's EPA-503
regime has a hard **≥ 50 °C floor** and redirects everything below it to storage/ammonia — so it
excludes valid mesophilic thermal designs. Espinosa et al. 2020 (*IJHEH*, 57 cites, OA) is a
systematic review/meta-analysis that builds **updated** time–temperature "safety zones" for four
pathogen groups — a more current basis than EPA 503 (1993).
→ For a *safety screen*, erring conservative is the right bias (it rejects, doesn't wave through),
but the substrate now records this as a **contested** value and points at the newer curves.

**RESOLUTION (followed up):** I tried to swap the 1993 EPA floor for the Espinosa 2020 meta-analytic
curves — and the sourcing produced a better answer than the swap. The mesophilic-helminth curve is
**not robust enough to adopt**: Espinosa had few qualifying helminth studies, and the onsite
meta-analysis finds temperature only weakly predictive of decay below ~50 °C. So instead of
inventing a mesophilic rate, the engine now has **three bands**: ≥50 °C → EPA-503 pass/fail (rapid,
well-supported); **40–50 °C → a sourced *advisory*** (inactivation achievable given extended time
per Harroff 2019 / Naidoo 2020, but no robust curve, so no number); < 40 °C → ambient/ammonia
regimes. The `dieoff thermal` command implements all three. This is the honest resolution — the
contest is answered without fabricating precision the literature can't support.

### 2. The die-off constants are from WHO 2006 — refreshed against a 2023 meta-analysis ✓
My binding constant was WHO Vol 4 Table 3.5 (Ascaris T90 = 125 d, k = 0.008/day).

**RESOLVED (followed up):** The open-access 2023 pooled onsite-sanitation meta-analysis (Musaazi et
al., *Water Research X*, N = 56 Ascaris studies) finds Ascaris **more persistent** than the WHO
single value — median k = **0.0042 log₁₀/day** (T90 ≈ 238 d), T99 = **429 d** — so WHO's number was
*optimistic* (too fast) for a safety screen. The die-off engine now uses the meta-analytic k for the
ambient Ascaris screen; two bonuses fell out: (a) the meta T99 = 429 d **corroborates** WHO's
conservative categorical >1-yr rule (which the verdict logic already sided with), and (b) the
first-order model and the categorical rule now **agree** (both flag 6-month storage UNSAFE) where
before they disagreed and the engine had to override the optimistic model. The meta-analysis also
independently confirms two of our existing findings: temperature is *not* predictive of decay below
~50 °C (the thermal contest), and urea+lime at pH 10–12 accelerates Ascaris (the ammonia model).

## Scope gaps the attack exposed (the substrate is silent on these)

### 3. Antimicrobial resistance (AMR / ARGs) — entirely absent
The safety layer is pathogen-focused (helminth/bacteria/virus) and says nothing about antibiotic
resistance genes, which (a) are a core reservoir in every WWTP (Zhu et al. 2025, *Nat. Commun.*,
105 cites — 20 core ARGs in all plants sampled), (b) survive/rebound through composting and
digestion (multiple 2024–25 *Water Res.*/*J. Hazard. Mater.* papers), and (c) transfer from
reused sludge **into crop tissue** (Li et al. 2024, *EST* — ARGs in tomato xylem). Bürgmann et al.
2018 (155 cites) frames sanitation as "an essential battlefront in the war on AMR." A reuse-safety
substrate that ignores AMR is incomplete. **Out of scope for v0.1, logged as a first-class gap.**

### 4. Micropollutants / pharmaceuticals in reuse — absent
Monetti et al. 2022 (*Water Res.*): urea hydrolysis + long-term urine storage sanitizes pathogens
but is **insufficient to remove anthropogenic micropollutants** (pharmaceuticals). The substrate's
urine-storage safety addresses pathogens only. Same theme in Carter 2024 for the broader
sanitation circular economy. **Scope gap.**

### 5. Norovirus vs the rotavirus index organism — an embedded assumption
The 6/7-log targets are **rotavirus-indexed** (WHO 2006). Newer QMRA (Ito 2017) sometimes indexes on
norovirus — lower infectious dose, higher persistence — which can shift required reductions. The
targets are scenario-specific (which the substrate captures), but the *index-organism choice* is an
undocumented assumption. Logged.

### 6. Helminth-egg guideline verifiability
The ≤1 egg/g *value* survives, but its **enforcement** depends on egg-recovery + viability assays
with variable/incomplete recovery (Ravindran 2019; Maya 2019 quick-viability method; Rudko 2017
surrogate). Measured compliance can therefore understate true viable-egg load — a caveat on every
verification threshold in the safety table.

## What this pass did NOT defeat
The core safety numbers held: the log-reduction targets, the helminth threshold *value*, Ascaris
persistence, the ammonia kinetics (three independent corroborations added), urine storage, and the
setback defaults (whose "context-dependent, can be insufficient in vulnerable hydrogeology" caveat
was strongly reinforced by the pit-latrine/groundwater literature, not overturned). The substrate's
provenance/tier discipline meant there were no *hidden* over-claims for the attack to find beyond the
ones the engine already flags.
