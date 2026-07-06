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

## 3. What still holds (and what remains excluded — honestly)

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
