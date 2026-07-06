# OpenWASH — Reading Synthesis

_Compiled 2026-07-04 from six parallel reads of the local corpus (WHO 2006 Vols 2 & 4,
WHO SSP manuals, EAWAG Compendium 2nd ed, Sphere Handbook 2018, CAWST BSF manual, and the
141-paper Semantic Scholar die-off/failure literature). Every number below traces to a
per-source extraction in this folder; those in turn cite page numbers. WHO Vol 2/4 values
were transcribed from the PDF pages, not the OCR._

---

## 0. Headline

The reading does three things the earlier abstract-level review could only assert:

1. **It makes the corroboration engine concrete** — we can now point at specific values that
   3 independent WHO documents agree on (a "multi-corroborated" tier), and at least one where
   two respected sources **disagree** (Sphere vs the Compendium on water-table clearance). That
   disagreement is signal, not noise — exactly what the substrate is supposed to surface.
2. **It confirms the safety table is real and small** — the excreta/urine reuse thresholds
   consolidate to a few dozen values, all sourced. First cut is in §3.
3. **It sharpens the epistemic line the whole project turns on** — WHO's die-off *formulas* are
   well-corroborated, but the *deployed outcomes* are not, and the corpus contains the field-harm
   proof (Malawi). The substrate must encode "target under assumed conditions" ≠ "verified field
   result." §4.

One strategic correction to an earlier call: **the EAWAG Compendium is a richer design substrate
than I credited.** It carries hard numbers (HRTs, loading rates, dimensions, removals, setbacks,
storage times) for all 57 technologies — see §5. The gap is not "no index exists"; it's "the index
exists as prose in a PDF, not as queryable per-field data with provenance." That is a narrower,
truer, and still-real gap.

---

## 1. Corroboration events (the engine, demonstrated on real data)

### 1a. Multi-corroborated (≥3 independent sources agree) → high tier
| Value | Sources that agree | 
|---|---|
| Unrestricted irrigation requires **6 log** (leaf/lettuce) / **7 log** (root/onion) pathogen reduction | WHO Vol 4 p.85 · WHO Vol 2 Table 4.1 p.85 · WHO SSP Fig 4.1 |
| Health target **≤ 10⁻⁶ DALY / person / year** | Vol 4 p.83 · Vol 2 Table 4.2 · SSP glossary |
| Treated material verification **≤ 1 helminth (Ascaris) egg** (per g TS faeces / per L wastewater) | Vol 4 p.84 · Vol 2 Table 4.1/4.4 · die-off lit (WHO baseline) · Compendium T.16 |
| **Urine 20 °C ≥ 6 months → safe for all crops** | Vol 4 Table 4.6 p.91 · Compendium S.1/D.2 p.58/142 |
| **Composting ≥ 50 °C for ≥ 1 week** sanitizes | Vol 4 p.89 · Compendium D.4 p.146 · Manga 2020 field (48–60 °C, >38 d, achieved it) |
| Dried faeces storage **1.5–2 yr (2–20 °C) / > 1 yr (> 20 °C)** for Ascaris | Vol 4 Table 4.5 p.90 · Compendium S.7/D.3 p.70/144 |
| Tolerable infection risk (rotavirus dev. 7.7×10⁻⁴; Cryptosporidium 2.2×10⁻³) | Vol 4 p.83 · Vol 2 Table 4.2 |

That first row is the proof of concept: three separate WHO publications, produced by different
teams a decade apart, independently give **6/7 log**. In OpenFeedstock terms, that's an MPN whose
rating three datasheets confirm — trust it.

### 1b. Contested (respected sources disagree) → surface both, don't average
| Parameter | Sphere 2018 | EAWAG Compendium | Verdict |
|---|---|---|---|
| **Pit bottom clearance above groundwater table** | **≥ 1.5 m** (Excreta std 3.1, p.115) | **≥ 2 m** (Single Pit S.2 p.60; VIP S.3 p.62; Soak Pit D.7 p.152) | **Genuine 0.5 m disagreement.** Both are defaults-when-no-test. Sphere is a humanitarian minimum; Compendium is a design-practice figure. The substrate should show both with a "contested — use the more conservative (2 m) absent a site infiltration test" note. This is the single best worked example of why averaging would be wrong: 1.75 m is nobody's recommendation. |
| **Latrine setback from any water source** | ≥ 30 m | ≥ 30 m | **Corroborated.** |

### 1c. Same technology, internally consistent across the Compendium
ABR appears twice (S.10 onsite / T.3 semi-centralized) with identical specs (BOD ≤ 90 %, HRT
48–72 h, upflow < 0.6 m/h, 3–6 chambers) — a self-consistency check the substrate can enforce.

---

## 2. The safety-critical siting constraints (the "don't ship a disease vector" layer)

The naive "just dig a trench" failure mode is bounded by three numbers, all now sourced:

- **≥ 30 m** horizontal from any drinking-water source (Sphere p.115; Compendium S.2/S.3/S.6/D.7/D.8) — corroborated.
- **≥ 1.5–2 m** vertical between pit bottom and the wet-season groundwater table (**contested**, see 1b).
- Both are **fallback defaults**; Sphere explicitly prefers a **site infiltration/permeability test** to set the distance, and says to *increase* setback in fissured rock/limestone (fast preferential flow) and *decrease* in fine soils. → the constraint engine's soil/hydrogeology input is not optional polish; it's the thing that makes the setback number meaningful.

---

## 3. The excreta/urine reuse safety table — v0.1 first cut

Consolidated, sourced, tiered. This *is* the narrow v0.1 deliverable the whole investigation pointed to.

### 3a. Health-based targets
| Parameter | Value | Source | Tier |
|---|---|---|---|
| Tolerable disease burden | ≤ 10⁻⁶ DALY/person/yr | Vol 4 p.83; Vol 2 T4.2; SSP | multi |
| Design tolerable infection risk (rotavirus) | 10⁻³ /person/yr | Vol 2 §3/Table 3.19 | single |
| Verification: treated faeces/sludge | < 1 helminth egg/g TS **and** < 1000 E. coli/g TS | Vol 4 p.84 | multi |
| Verification: wastewater, unrestricted | < 1 egg/L; < 10³ E. coli/100 mL | Vol 2 T4.5; Vol 4 p.84 | multi |
| Tighten where children < 15 exposed | ≤ 0.1 egg/L | Vol 2 T4.1 p.85 | single |

### 3b. Required pathogen reduction by exposure (log₁₀)
| Scenario | Reduction | Source |
|---|---|---|
| Unrestricted — leaf crops (lettuce) | 6 | Vol 4/Vol 2/SSP (multi) |
| Unrestricted — root crops (onion) | 7 | Vol 4/Vol 2/SSP (multi) |
| Restricted — labour-intensive | 4 | Vol 2 T4.1 |
| Restricted — highly mechanized | 3 | Vol 2 T4.1 |
| Localized drip — low-growing | 4 | Vol 2 T4.1 |
| Localized drip — high-growing | 2 | Vol 2 T4.1 |

### 3c. Multi-barrier credits — how you *reach* 6–7 log without full treatment (Vol 2 Table 4.3, p.89)
| Barrier | Log credit |
|---|---|
| Wastewater treatment | 1–6 |
| Drip irrigation (low/high-growing) | 2 / 4 |
| Pathogen die-off on crop (per day withheld) | 0.5–2 /day |
| Produce washing / disinfection / peeling | 1 / 2 / 2 |
| Cooking | 6–7 |
| Spray buffer zone (50–100 m) / drift control | 1 / 1 |
| **Not credited:** PPE, handwashing (recommended, unquantified) | — |

### 3d. Storage/treatment to sanitize excreta (Vol 4 Tables 4.4–4.6)
| Method | Condition | Effect |
|---|---|---|
| Ambient storage 2–20 °C | 1.5–2 yr | eliminates bacteria; ≤ Ascaris risk |
| Ambient storage > 20–35 °C | > 1 yr | schistosome < 1 mo; 10–30 % Ascaris survive ≥ 4 mo; near-complete by 1 yr |
| Alkaline | pH > 9 for > 6 mo | absolute elimination (temp > 35 °C, moisture < 25 %) |
| Composting | > 50 °C for > 1 week | full sanitization (minimum; longer if temp not assured) |
| Urine | 20 °C ≥ 6 mo | → all crops (≥ 1 mo → processed crops only) |

### 3e. The binding constraint — Ascaris T₉₀ (days for 1-log die-off), Vol 4 Table 3.5 p.59
Ascaris **125 ± 30 d in faeces, 625 ± 150 d in soil** — 2–4× more persistent than any bacterium
or virus in the table. Every storage/composting requirement above is really an Ascaris-kill
requirement. This is the single most important number in the safety layer.

---

## 4. The epistemic finding — formula vs field (this is the spine, not a footnote)

**The mechanism is corroborated; the deployed outcome is not.**

- **Corroborated (engineered):** Manga 2020 (tropical Uganda) — FS + bulking agent, thermophilic
  **48–60 °C sustained > 38 days**, achieved **complete sanitization** incl. viable helminth eggs.
  WHO's "> 50 °C for a week" pathway is sound *when the regime is actually reached and held.*
- **Not corroborated (deployed/passive):** Kumwenda 2019 (Malawi) — real EcoSan latrines, 12 months
  post-sealing, sludge households are told to put on food crops:
  - Hookworm **5–10 eggs/g** (limit ≤ 1)
  - Ascaris still > 1 egg/g in **12 %** of units — and it **rose** (1.5 → 2.3) before falling to 0.4
  - Salmonella **increased 71 → 456 CFU/g** (regrowth, not decay)
  - The units never reached any assumed regime: **pH 8.7 (not > 12), NH₃ ~90 (not ~280 mg/L), no thermophilic phase at all.**
  - Authors: the ~6-month guidance is **insufficient**; even ≥ 12 months didn't fully sanitize.

**Implication for the substrate design.** A naive corroboration engine, seeing Vol 4 + Vol 2 + the
Compendium all say "6-month urine storage / storage-based faeces sanitization," would stamp it
`multi-corroborated` and ship false confidence. The reading shows the field distribution is wide
and non-monotonic, keyed on whether the deployed unit *reaches* the assumed pH/NH₃/temperature.
So a value in this dataset needs **two distinct fields**, never collapsed:
- `design_target` — the guideline value under assumed conditions (well-corroborated), and
- `field_verified` — whether deployed reality achieves it (thin, scattered, often *no*),

plus the die-off caveat and Manga's explicit **"tropical composting data is a recognised gap"**
carried as a first-class provenance note. This is the difference between a substrate that is
honest about health-safety uncertainty and one that launders a guideline number into a guarantee.

---

## 5. The technology substrate — what the Compendium already gives us

57 technologies across 5 functional groups (U/S/C/T/D), each keyed by a controlled **product
vocabulary** (excreta, faeces, urine, brown/black/greywater, effluent, sludge, compost, pit humus,
dried faeces, biogas…), with **output-of-one = input-of-next** linkage. Nearly every sheet carries
real design numbers. Examples directly relevant to the capability query:

| Tech | Design numbers the substrate could key on |
|---|---|
| S.2 Single Pit | 40–60 L/person/yr solids; ≥ 3 m deep; **≥ 30 m from water, ≥ 2 m above table** |
| S.9 Septic Tank | 50 % SS, 30–40 % BOD, 1-log E. coli; HRT 48 h; desludge 2–5 yr |
| S.10/T.3 ABR | BOD ≤ 90 %; HRT 48–72 h; 2–200 m³/d; 3–6 chambers |
| T.8 HF Constructed Wetland | **5–10 m²/person**; gravel 3–32 mm; bed 0.5–1 m; slope 1 % |
| T.5 Waste Stabilization Ponds | anaerobic BOD ≤ 60 % / facultative ≤ 75 %; maturation pond does pathogens |
| T.16 Co-Composting | 1:2–1:3 sludge:waste; ≥ 55–60 °C; **< 1 viable helminth egg/g TS** |
| D.2 Urine application | ~40–110 kg N/ha; 1 person's urine → 300–400 m²/yr; dilute 3:1 for veg |

This is the capability-query backbone (population → sizing → applicability) in prose form.
**What's missing to make it a substrate:** it's a PDF, the I/O products are icon glyphs not fields,
units are inconsistent, there's no consolidated pathogen-reduction table, and it carries no
per-field provenance/tier. Structuring *that* — plus bolting on the corroborated safety layer from
§3 — is the actual OpenWASH build. Not a greenfield; a normalization + provenance + safety overlay.

CAWST fills the one deep well the Compendium is thin on — BSF construction detail (30 L filtration
sand ≤ 0.7 mm, 5 cm standing water, 0.4 L/min flow, ≥ 1 h pause, ~30-day ripening) — but notably
**its technician manual gives no numeric pathogen log-reductions** (those live in separate CAWST
fact-sheets), confirming the "document-shaped, not schema-shaped" diagnosis.

---

## 6. What the reading changes for v0.1

1. **Build the safety table in §3 as the v0.1 core.** It's ~40 sourced values, it demonstrates the
   corroboration engine (§1a), and it includes a real contested value to exercise the
   disagreement-surfacing (§1b). This is the smallest thing that proves the moat.
2. **Encode `design_target` vs `field_verified` as separate fields from commit one** (§4). This is
   the design decision the field literature forces; retrofitting it later would be painful.
3. **Treat the Compendium as the technology-catalog seed to normalize**, not a gap to fill from
   scratch (§5). The honest framing: OpenWASH = a queryable, provenance-tagged, safety-overlaid
   normalization of the Compendium + WHO safety layer. Narrower and more defensible than the README.
4. **The Ascaris T₉₀ (§3e) is the constraint engine's first hard formula** — temperature/time/pH →
   helminth-egg viability. Everything else in the safety layer derives from it.

Open items flagged by the readers: CAWST cost worksheet is blank (no currency figures); Compendium
excludes greywater/stormwater in depth; the field-harm evidence rests on a single low-n study
(strong as existence proof, weak as a distribution).
