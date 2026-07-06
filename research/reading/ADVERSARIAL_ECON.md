# Adversarial review — the barrel-yard economic & physical model

Companion to [`ADVERSARIAL.md`](ADVERSARIAL.md) (which attacked the *safety data* and
kinetics — those held). This pass attacked the **new barrel-yard model** built in
`research/barrel_yard_model.py`, `collection_logistics.py`, `pilot_pnl.py`,
`pilot_siting.py`, `pnl_sensitivity.py`. Three independent adversarial agents
(code/units, physics/biology, economic realism) plus hand-checks. **The model was
materially wrong in its optimistic direction, and has been corrected.** This file
records how it was defeated and what changed — the same honesty the corroboration
engine enforces on the safety table, applied to our own economics.

## Verdict

Two conclusions **survive**, one headline **does not**:

- ✅ **Treatment is a rounding error** (~3–5% of opex); **collection is ~95%**; the fee is
  set by **depot distance**, not the reactor. (Arithmetic verified by hand — no unit error.)
- ✅ The corroboration/safety layer and its kinetics are unchanged and still hold.
- ❌ **The optimistic economics — "$1.95/HH/mo, N-revenue covers 40–70% of opex, cheaper
  than CBS, black drums de-fang climate" — were false.** They rested on a tuned thermal
  parameter and a fictional revenue engine. Corrected fee: **~$5–7/HH/mo (a floor),
  N-revenue offsets <5% of opex, and — like every real CBS operator — it needs subsidy.**

## Findings (ranked) and fixes applied

### T1 — Thermal uplift was tuned (+12 °C); defensible is ~+4 °C  ·  FIXED
`solar_uplift()` used **U = 8 W/m²K** (labelled "light wind") and **aperture = 0.8 m²**.
- U=8 is the *dead-still-air floor*: radiative alone ≈5.7 + free convection ≈2.6 ≈ 8.3.
  McAdams outdoor h_w = 5.7 + 3.8·V → any real 2 m/s breeze gives U ≈ 15–19. (Verified by
  hand.)
- Aperture 0.8 m² **exceeds the drum's beam silhouette** (d·h ≈ 0.49 m²), and GHI already
  carries the horizontal cosine projection → double-count. Defensible ≈ 0.5 m².
- **Fix:** `DRUM` now U=15, aperture=0.5 → **nominal +4.0 °C** (range +3 to +7). Because the
  kinetics go as `5^(T/10)`, the old +12 error was a **~3–5× error in cure/barrels/land** in
  exactly the cool climates the "de-fang" pitch targeted. Black drums are now a **modest
  ~2–3× cure reduction**, not a near-elimination. `sweep`/`crossover`/`pilot_siting` all
  re-propagate the corrected uplift; the "climate de-fanged" narrative is downgraded.

### K1 — Kinetics extrapolated past calibration → fantasy 1–2-day cures  ·  FIXED
`k_ammonia` (Q10=5, linear in NH3) is fit to Nordin 2009 (4–34 °C). The model forced batch
temps to 40–42 °C (old +12 uplift) and NH3(aq) to ~290 mM, producing **1-day Ascaris cures**.
- Temperature: 8 °C beyond the top anchor.
- Concentration: the law is linear, but the data **saturate** — at 34 °C, Nordin 250 mM →
  t99 5.9 d vs Fidjeland 440 mM → 6.4 d (nearly double the NH3, *same* kill). The `--validate`
  claim that "Fidjeland's t99 values fall on the model" is **false for that row** (model ~3.5 d
  vs sourced 6.4 d, 1.8× too fast).
- **Fix:** `cure_days` now **clamps T ≤ 34 °C and NH3(aq) ≤ 250 mM** to the calibration range.
  No more sub-2-day cures; hot-case cure is now ~6–11 d.

### R1 — The revenue engine was fictional  ·  FIXED (honest defaults)
The P&L booked **100% of recovered N as cash at $0.8/kg (synthetic-urea parity)**. But the
two flagship operators the sites are drawn from **do not sell nitrogen**: Sanergy → black-
soldier-fly protein + low-N compost sold by the tonne (Regen Organics/Evergrow); Sanivation →
fuel briquettes (N combusted). Real excreta product is a bulky soil conditioner, not N at
parity, and cold-market offtake is low (Swayimane: 80% of farmers initially unwilling).
- **Fix:** `OFFTAKE_FRACTION 1.0 → 0.25`; realized N price `$0.8 → $0.35`; **surplus urine
  handled on-site, not centrally sold** (only the faecal product's N is booked). N-revenue
  falls from $54.9k to ~$1.8k/yr (<2% of opex).

### R2 — "urea-avoided" counted as cash  ·  FIXED
$18.5k/yr (34% of the old "revenue") was a **counterfactual** saving vs a urea-dosing op you
never run. **Fix:** `COUNT_UREA_AVOIDED 1.0 → 0.0` by default (toggle retained).

### R3 — Missing real CBS cost lines  ·  PARTIALLY FIXED
Collection modelled only labour+fuel+vehicle (~63% of real CBS direct cost; SOIL/Tilmans 2015).
Omitted: benefits (~13%), consumables/container-servicing (~12%), facilities, admin/overhead.
- **Fix:** `COLLECTION_OVERHEAD_MULT = 1.5`. **Still excluded** (so the fee is a *floor*):
  household-container capex, customer acquisition, bad-debt/defaults.

### U3 — Central urine haulage is the ecosan sinkhole  ·  FIXED (design change)
1.2 L/cap/day urine = **12 t/day** for 10k people, ~80% of hauled mass, worth only ~$7/m³ of N;
tanker haulage often exceeds product value (Etter/Maurer 2011; VUNA/eThekwini). **Fix:** urine
surplus is now handled **on-site** — removing both its phantom revenue *and* its haul cost.

### C1 — Crossover concentrator didn't scale → prose inverted at 100k  ·  FIXED
The solar-concentrator route was a flat cost regardless of population, so hardcoded prose
("urine yard wins across any land price") **inverted at pop=100k**. **Fix:** both routes now
scale (drum-handler count with inflow; concentrator in modular 10k-person units), and the
crossover **computes** the land-price break-even instead of asserting it.

### C4 — `run()` capex stored urine in thousands of drums  ·  FIXED
`run()` bought ~3,375 drums for a 180-day urine buffer (~$50k of a $62k capex), inconsistent
with `pilot_pnl`'s bulk tanks. **Fix:** `run()` now uses 60-day bulk storage ($0.08/L), matching.

### C3 — Latent `None`-cure crash  ·  FIXED
When NH3 < threshold, `cure_days` returns `None`, which crashed `run()`/`pnl()`/`sweep`.
**Fix:** all three now guard it and report infeasibility.

### Also caught (self, during build)
The fee **tornado harness itself had a bug**: the depot-distance axis was a no-op (it mutated
`COL.C` while `pnl()` reads the SITE dict), reporting ±$0.00 for what is actually the #1 lever.
Fixed before this review.

## What the corrected model says

| | Before (optimistic) | After (honest) |
|---|---|---|
| Black-drum uplift | +12 °C | **+4 °C** |
| Hot-site cure | 1–2 d | **6–11 d** |
| N-revenue vs opex | 40–70% | **<5%** |
| Kumasi break-even fee | $1.95/HH/mo | **$6.22/HH/mo (a floor)** |
| vs real CBS | "cheaper than $3–8" | **inside $3.21–12; Clean Team charges ~$9 in Kumasi** |
| Self-funding on N? | implied yes | **no — needs fee + subsidy, like every CBS operator** |

The honest through-line is unchanged and, if anything, sharper: **the reactor was never the
problem. Sanitation viability is collection logistics + demand for the product + subsidy — the
exact O&M/economics bottleneck the whole research pass identified.** The barrel yard makes
treatment cheap and safe; it does not make the hard parts go away.

Key sources: McAdams / Duffie & Beckman (thermal); Nordin 2009, Fidjeland 2015 (kinetics
saturation); Etter/Maurer 2011, VUNA (urine haulage); Frontiers 2019 & World Bank (CBS not
cost-recovering); Tilmans 2015 (SOIL cost structure); Kellogg/HBS "Sanergy 2.0" 2024; Diener/
Koné 2011 (Dakar FSM $11.63/cap/yr); Swayimane 2022 & MDPI Sustainability 2019/20 (offtake/WTP).
