# AUDIT — the honesty ledger

OpenWASH enforces four honesty rules on every safety number (no naked numbers; a corroboration
tier computed from independent lineages; design-target kept separate from field-verified; contested
values surfaced, not averaged). This file applies that same discipline **to the project itself**:
it records every place OpenWASH was wrong, caught it, and retracted — in its own numbers, its own
model, and its own code.

Nothing here is a soft "limitation." These are corrections: claims that were made, found false, and
withdrawn. The ten claims in [`claims.yaml`](claims.yaml) (attested 10/10 in
[`attestation.json`](attestation.json)) are what survived this process, not what preceded it.

> **Principle.** A wrong public claim costs more than several careful ones earn. Everything below was
> corrected *before* release, in the optimistic-was-wrong direction — which is the direction that
> matters, because it's the one an author is biased not to look for.

---

## 1. The safety data & corroboration layer

**Attacked, and it held — with one self-caught over-claim.** A 151-paper adversarial refutation scan
([`research/reading/ADVERSARIAL.md`](research/reading/ADVERSARIAL.md)) was run against the safety
thresholds and die-off kinetics. The load-bearing numbers survived. The one correction came from the
engine turning its rules on its own dataset:

- **Over-claim: "three independent WHO sources" for the unrestricted-irrigation log-reduction target
  → downgraded to a single lineage.** The synthesis originally treated WHO 2006 Vol. 2/Vol. 4 and the
  2022 Sanitation Safety Planning manual as three corroborating sources. They are not: the later
  documents *restate* the 2006 guideline rather than independently deriving it. The corroboration
  engine computes `single_lineage`, not `multi_corroborated`, and `validate()` emits an `OVER-CLAIM`
  warning. The retraction is recorded inline in the dataset (`data/reuse_safety.yaml`), and it is now
  a passing test (`test_overclaim_downgraded_to_single_lineage`, `test_validate_flags_the_overclaims`)
  — the mistake is pinned so it cannot silently return.

*This is the feature working:* the tool caught its own author restating a source and mistaking the
echo for corroboration.

---

## 2. The techno-economic & physical model

**Attacked by three independent adversarial passes (code/units, physics/biology, economic realism)
and found materially wrong in its optimistic direction — corrected.** Full write-up:
[`research/reading/ADVERSARIAL_ECON.md`](research/reading/ADVERSARIAL_ECON.md). The headline that did
**not** survive: *"$1.95/HH/mo, nitrogen revenue covers 40–70% of opex, cheaper than container-based
sanitation, black drums de-fang cold climates."* It rested on a tuned thermal parameter and a
fictional revenue engine. Retractions:

| # | Claim as made | What was wrong | Corrected to |
|---|---|---|---|
| **T1** | Black-drum solar uplift **+12 °C** | Used the dead-still-air heat-loss floor (U=8) and an aperture (0.8 m²) larger than the drum's own silhouette (0.49 m²) — a double-count. Any real breeze gives U≈15–19. | **+4 °C** (U=15, aperture 0.5). Because kill scales ~5^(T/10), the old error was a **3–5× overstatement** of treatment in exactly the cool climates the pitch targeted. |
| **K1** | Ammonia cures in **1–2 days** | Kinetics (fit to Nordin 2009, 4–34 °C) were extrapolated to 40–42 °C and ~290 mM NH₃; the data actually **saturate** — double the ammonia, same kill. Sub-2-day cures were fantasy. | **6–11 days.** `cure_days` now **clamps T ≤ 34 °C and NH₃(aq) ≤ 250 mM** to the calibration range. |
| **R1** | 100% of recovered N sold at **$0.80/kg** (urea parity) | The real operators these sites are drawn from **don't sell nitrogen** — they sell bulky soil conditioner or burn it as fuel; cold-market offtake is low. | Offtake 1.0→**0.25**, N price →**$0.35**, urine handled on-site. N-revenue fell from $54.9k to ~$1.8k/yr — **<5% of opex**. |
| **R2** | "Urea avoided" booked as **$18.5k/yr cash** | A counterfactual saving against a urea-dosing operation you never run — not revenue. | Counted as **$0** by default. |
| **R3** | Collection = labour + fuel + vehicle | ~63% of real CBS direct cost; omitted benefits, consumables, container-servicing, admin. | **×1.5 overhead.** Still excludes household-container capex, customer acquisition, bad debt — so the fee is a **floor, not an estimate**. |
| **U3** | Central urine sold as revenue | 12 t/day of urine for 10k people is ~80% of hauled mass, worth ~$7/m³ — haulage often exceeds product value. | Urine handled **on-site**; both its phantom revenue and its haul cost removed. |
| **C1** | "Urine yard wins at any land price" | The concentrator route didn't scale with population, so the hardcoded conclusion **inverted at pop=100k**. | Both routes scale; the crossover **computes** the land-price break-even instead of asserting it. |

**Net effect on the headline number:** Kumasi break-even fee **$1.95 → $6.22/HH/mo (a floor)**;
self-funding on nitrogen **implied yes → no**. Like every real container-based-sanitation operator,
it needs a fee *plus* subsidy.

### A conceptual error, not just a parameter
The model briefly framed the design as a **fuel-vs-nitrogen trade-off** — burn the solids for fuel
*or* keep the nitrogen. That fork is false: the nitrogen is in the **liquid**, the fuel value is in
the **solids**, so you can burn *and* keep the N. The real wall is different and harder — **the
nitrogen has no profitable exit**, cold markets won't pay parity for it. Correcting the framing made
the economics *worse*, not better, which is why it's in this ledger.

### Bugs caught by self-review during the build
- **The sensitivity ("tornado") harness had a dead axis.** The depot-distance lever — actually the
  **#1 cost driver** — mutated the wrong dict and reported ±$0.00. Fixed before the economic review.
- **Latent crash:** when ammonia fell below threshold, `cure_days` returned `None` and crashed three
  callers. Now guarded and reported as infeasible.
- **Capex inconsistency:** `run()` bought ~3,375 drums for urine buffering (~$50k of a $62k capex),
  inconsistent with the bulk-tank model elsewhere. Reconciled to 60-day bulk storage.

---

## 3. Round 2 — the audit turned on the guardrail and the attestation itself (2026-07-06)

After the attestation shipped, four independent adversarial auditors (safety-data/corroboration,
die-off/guardrail, claims-vs-tests meta-audit, numbers-consistency) re-attacked the *live* repo.
Every finding below was **hand-verified before it was fixed**, and each fix is pinned by a new
regression test (suite 64 → **68**). This round found a genuine operator-facing false-safe and one
attested claim that was partly hollow — exactly the things the tool exists to refuse.

| # | Defect (verified) | Failure it caused | Fix |
|---|---|---|---|
| **HIGH** | **Ammonia false-safe.** `screen_ammonia` inferred NH₃ from **pH alone**, hard-coding a 200 mM dose. | An operator following the tool's own "add ash/lime to pH ≥9" advice with **lime (zero nitrogen)** got **SAFE_SCREEN** with essentially no ammonia present. | Require a **measured** total ammoniacal-N; without it → **UNKNOWN** ("measure your dose — pH can't confirm it"). |
| **HIGH** | **Attestation theater.** The `dieoff_reproduces_anchors` thermal test recomputed the EPA-503 formula *inline* and asserted it equalled its own output — it **never called the engine**. | Deleting the engine's thermal constant left the test green: "reproduces published anchors" was, for the thermal half, a tautology. | New single engine home `dieoff.epa_thermal_days()` (used by guardrail + test); test now calls it and checks against **independent** WHO (">1 wk") and Haug (1–2 d) points. Claim prose narrowed; the non-existent "Vinnerås" source dropped. |
| **HIGH** | **README economics contradicted this very file.** Quoted a **"~$2/HH/mo"** fee (the retracted $1.95; honest floor is **$6.22**), an unsupported **"18% fuel"** figure, and misdescribed the over-claim as *fuel 40–60%→18%* (real: *nitrogen 40–70%→<5%*). | The public pitch published numbers the project's own audit had withdrawn. | README rewritten to match §2 exactly. |
| **MED** | **Storage screen less conservative than its own model.** `screen_storage` returned SAFE on the WHO rule-floor even where the first-order model left **>1 egg/g** (30 °C / 365 d → residual ~1.17). | A false-safe by the system's *own* conservative-signal rule, at the band boundary. | SAFE now requires the rule **and** the model to agree; if the model residual > target, the conservative signal governs → UNSAFE. |
| **MED** | **Urine screen ignored temperature.** WHO storage times (~20 °C) were applied to any temperature. | A **4 °C** urine store on a raw-crop route read the same **SAFE** as 20 °C. | Below ~20 °C on a stored route → **UNKNOWN** ("these times assume ~20 °C"). |
| **MED** | **Corroboration `restates` latent bug.** A restatement *added* its target lineage to the independent set, phantom-crediting a lineage even when no primary of it was cited. | Could bless a false `multi_corroborated` (not yet triggered — worked only by luck of the data). | Independence now comes from **primaries only**; an echo can never manufacture a new lineage. |
| **MED** | **Corroboration audit scope gap.** The tier over-claim check ran only on top-level `value` blocks. | `target_vs_field` / `contested` blocks carrying a hand-typed `claimed_tier` escaped the "computed, not trusted" guarantee — ~⅓ of claim shapes. | Audit now covers **every** `claimed_tier`-bearing block. |
| **LOW** | **Data error.** The 57 °C thermal cross-check recorded `epa_days: 1.1` (Haug's low end) where the EPA-503 formula gives **1.38**. | A mislabeled anchor (masked from the guardrail, which never uses it). | Corrected to 1.38; Haug's 1–2 d noted as the independent bracket. |
| **scope** | **Claim scope over-reach.** `no_naked_numbers` said "the dataset" but tested only the reuse-safety table; the `malawi` claim's prose overstated the *mechanism* (the UNSAFE is the WHO categorical rule, not a field-over-target arbitration — the design target itself already calls 6 months insufficient). | Prose broader than the test. | Added `test_kinetics_constants_are_sourced` and extended the claim to the kinetics; rewrote the malawi statement to the true mechanism. |

**Found but NOT "fixed" — because they are honest limitations, not bugs (recorded, not papered over):**
- **Unmarked shared ancestry.** The 30 m water setback is `multi_corroborated` (Sphere + EAWAG, distinct lineages), but both may echo an older engineering convention the tracker can't see. The lineage engine catches **marked** echoes (`restates`), not unmarked common ancestry — so tier honesty still rests partly on annotation. This is the layer's real boundary: *honest by discipline, not fully by construction.*
- **`field.tier` is editorial.** The `field` block's `field_corroborated` / `field_contradicted` is a label paired with `status:`, describing whether field evidence matched the design target — **not** a lineage-computed corroboration tier, and the engine does not claim to compute it.
- **The binding number is single-sourced.** `t90_ascaris_faeces` (125 ± 30 d) is honestly labeled `single_sourced`; the meta-analytic refresh (Musaazi 2023) is already applied in the *ambient decay* path (a regression test pins that it's slower/more conservative than the old WHO value).

## 4. Round 3 — re-attack the fixes, and the layers Round 2 never hit (2026-07-07)

Round 2's fixes are fresh code, so they got re-attacked; and the technology-**selection** and
**systems** layers — barely touched before — got a first real adversarial pass. Four auditors again,
findings hand-verified, each fix pinned by a regression test (suite 68 → **74**).

**The Round-2 fixes held** — no new false-safe was introduced; the ammonia/storage/urine/corroboration
changes all fail safe at their boundaries. The new pass found one genuine safety-checkpoint gap and a
handful of smaller issues:

| # | Defect (verified) | Failure it caused | Fix |
|---|---|---|---|
| **HIGH** | **A reuse endpoint dropped its pathogen flag.** `systems.py` only attached the `⚑` pathogen screen to reuse products in `REUSE_HINT`; **biosolids** (land-applied sludge, D.5) wasn't in it, and **in-situ biomass** endpoints (an arborloo, D.1) have no reuse product at all. | Both were scored and labeled "reuse-complete" and got the *chemical* watch flag, but the **pathogen/helminth screen was silently dropped** on the exact land-application pathway that most needs it. | `biosolids` added to `REUSE_HINT`; the flag now fires on **every** reuse endpoint (a fallback covers biomass/arborloo). A test asserts no reuse endpoint across any preset escapes it. |
| **MED** | **Fail-open on unknown site data.** The water-table and reuse-land gates only fired when the site *provided* the value; a missing value silently passed. | A custom site that omitted water-table depth got **deep pits cleared**; omitting land cleared reuse endpoints. | Fail-**closed**: unknown water-table → a deep pit is disqualified (`water_table_unknown`) pending the value; same for land/reuse-land. |
| **MED** | **Watch layer skipped dried faeces.** `dried_faeces` wasn't in any hazard's product list. | Direct dried-faeces land reuse — a primary route for the gut resistome and drug residues — carried **no AMR/micropollutant flag**. | Added `dried_faeces` to the AMR and micropollutant hazards. |
| **LOW** | **Round-2's data fix was incomplete.** `cmd_thermal` still printed a hardcoded `57 °C→1.1 d` labeled "(in kinetics data)" while the data now says 1.38 — the CLI misquoted its own source. | Cosmetic (not a guardrail value), but it made Round 2's "corrected to 1.38" slightly over-stated. | The cross-check line now reads from the data; the EPA-503 high-solids constant moved **into** the kinetics data as a sourced number (was hardcoded in two places) and is now audited by the "no naked numbers" kinetics test. |
| **LOW** | **Pure-echo corroboration edge.** After the Round-2 restates fix, a value cited *only* by two restatements of different lineages could still compute `multi_corroborated`. | Latent (no such value in the data), but an over-corroboration path by construction. | Independence now comes from primaries only; a pure echo yields no independent lineage → never `multi`. |
| **LOW** | **Dead urine branch + a hidden load assumption.** `verification_plan`'s urine step was unreachable (urine dispatches as `storage`), and the storage SAFE verdict silently assumed ~40 eggs/g initial load. | Wrong verification label for urine; a very heavy Ascaris load could pass on the 40-egg assumption. | Reordered so urine gets its own step; the SAFE verdict now **states the assumed initial load** ("a heavier load needs longer"). |

**Recorded, not "fixed" (honest limitations):** the S.12 biogas cold-climate constraint in the data is
advisory-only (no site-temperature field enforces it), and one cost row (S.7 vault) carries a
whole-toilet figure — both disclosed, neither safety-gating. The **initial-load** assumption remains a
guided-path simplification (now disclosed, not eliminated).

## 5. What still holds (and what remains excluded — honestly)

**Survives the audit, sharper for it:** treatment is a rounding error (~3–5% of opex); collection and
demand and subsidy are the binding constraints; the safety substrate, the corroboration engine, and
the die-off kinetics are unchanged and reproduce their published anchors. *The reactor was never the
problem.*

**Deliberately still excluded (so no number here over-promises):**
- The break-even fee is a **floor** — it omits household-container capex, customer acquisition, and
  bad-debt/defaults. Real fees run higher.
- Individual peer-reviewed sources' publisher domiciles/licences weren't checked one-by-one (see
  [`LICENSING.md`](LICENSING.md)); it's the only residual EU-source exposure, weak but unresolved.
- OpenWASH is **a screen, not a certifier** — it rules out unsafe reuse designs and states what to
  measure. It is not a medical device, not a guarantee, and not a substitute for testing before
  reuse, and it does not address non-pathogen (chemical / AMR) hazards.

---

*The audit is never "done." New claims get a `claims.yaml` entry; corrections get an inline
retraction and, where possible, a pinning test. The record staying open is the point — a closed audit
is just an unexamined one.*
