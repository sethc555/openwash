# OpenWASH (working name)

> A trustworthy **safety guardrail** for reusing human waste — so closing the
> sanitation loop *helps* people instead of *reinfecting* them.

**Status:** v0.2 — safety substrate (validated) + a usable reuse-safety check + a techno-economic proof-of-thesis
**License:** Apache-2.0 (code — [`LICENSE`](LICENSE)) + CC-BY-4.0 (curated dataset & docs — [`LICENSE-DATA`](LICENSE-DATA)). Rationale + provenance in [`LICENSING.md`](LICENSING.md) / [`NOTICE`](NOTICE).

---

## Why this exists (the human point)

The suffering is fecal–oral disease: diarrhea is still a leading killer of children
under five, and soil-transmitted helminths — *Ascaris*, the exact organism this
engine is built around — infect roughly a billion people, stunting growth and
cognition. Safe **reuse** of excreta (into soil or fuel) is one of the few things
that makes sanitation affordable and *wanted* in poor places. But done wrong, reuse
is a **new disease vector** — unsafe sludge on a food crop reinfects the very people
it was meant to help ([Kumwenda 2019, Malawi](research/reading/SYNTHESIS.md)).

**The entire margin between reuse-that-helps and reuse-that-harms is a handful of
safety numbers** — and those numbers are scattered across WHO PDFs, easy to get
wrong, and exactly what an LLM will hallucinate. OpenWASH holds those numbers
honestly and puts them where the decision is made. It is the *guardrail*, not the
whole system: it doesn't build the toilet or fund the plant — it keeps the loop
from becoming the reinfection.

## What it is (three layers)

1. **The substrate** — a corroborated, sourced, tier-honest reuse-safety dataset +
   die-off engine. The moat (below).
2. **The guardrail** — [`engine/safe_reuse.py`](engine/safe_reuse.py): a plain-language
   *"is my reuse safe?"* check a field operator or health worker can actually run —
   material + treatment + where it's going → **SAFE / UNSAFE / NOT ENOUGH EVIDENCE**,
   with the reason and the specific fix. This is the substrate becoming an application.
3. **Proof-of-thesis** — a bottom-up techno-economic design study ([`research/`](research/))
   that took one reuse pathway all the way to the pipe and the household fee, and
   independently confirmed *why* the substrate scopes itself to safety (below).

## The moat, demonstrated

The [`engine`](engine/openwash.py) enforces four things on real data
([`data/`](data/)):

1. **No naked numbers** — every value cites a source + page.
2. **Computed corroboration tier** — trust is counted from independent source
   *lineages*, not asserted. It caught a real over-claim: the WHO 6/7-log
   irrigation target looks triple-sourced (Vol 4, Vol 2, SSP) but is one lineage
   echoed — honest tier `single_lineage`, not `multi_corroborated`.
3. **`design_target` ≠ `field_verified`** — the guideline value and whether
   deployment achieves it are separate fields. WHO's composting formula is field-
   *corroborated*; its passive-storage pathway is field-*contradicted*.
4. **Contested values surfaced, never averaged** — Sphere (≥1.5 m) vs EAWAG (≥2 m)
   pit clearance above the water table, both kept, resolved by policy not by mean.

The project turns these rules **on itself**: every place OpenWASH was wrong, caught it, and retracted
— in its numbers, its model, and its code — is consolidated in [`AUDIT.md`](AUDIT.md) (the honesty
ledger).

It has also been **adversarially verified** ([`research/reading/ADVERSARIAL.md`](research/reading/ADVERSARIAL.md)):
a 151-paper refutation scan tried to defeat every load-bearing value. The core safety numbers held
(log-reduction targets, helminth threshold, Ascaris persistence, ammonia kinetics — three further
corroborations added); what the attack legitimately dented or exposed is recorded, sourced, as
first-class [`data/limitations.yaml`](data/limitations.yaml) — the thermal ≥50 °C floor is contested
(Harroff 2019: mesophilic works), the die-off constants have a 2026 meta-analysis refresh target, and
the rotavirus-index assumption is a logged scope gap. The `dieoff thermal` screen self-flags its
contested status; the two follow-ups (thermal mesophilic contest, die-off-constant refresh against a
2023 meta-analysis) are since resolved. The AMR / micropollutant / heavy-metal gaps are now an
explicit **watch layer** ([`data/watch.yaml`](data/watch.yaml) + [`engine/watch.py`](engine/watch.py)):
a *flag* layer, not a model — there's no accepted reduction target for these, so it warns per reuse
pathway (and `systems.py` surfaces it) that passing the pathogen screen says nothing about them.

And the **constraint engine** ([`engine/dieoff.py`](engine/dieoff.py)) — the safety layer
the whole project turns on. It screens a storage/treatment regime for pathogen-reduction
sufficiency using first-order die-off kinetics seeded from WHO Tables 3.5/3.8. It is a
*screen, not a certifier*: it rules out insufficient designs and, when its optimistic model
disagrees with the conservative WHO categorical rule, sides with the conservative call. A
naive 6-month passive UDDT is correctly flagged **UNSAFE** — matching the Malawi field
failure — even though the bare log-linear model would pass it.

## The capability query (technology selection)

[`engine/select.py`](engine/select.py) runs the original wedge over a technology catalog
normalized from the EAWAG Compendium ([`data/technologies.yaml`](data/technologies.yaml),
54 technologies — the full Compendium set across all 5 functional groups): given a site
(scale, water-table depth, land, soil, skilled labour, power, water, offsite service) it
returns the technologies that **fit** and the
**disqualifying constraint** for every one that doesn't — then links each fitting
technology's reuse output back to the safety layer above. The four presets show it
discriminating: a high water table disqualifies deep pits (leaving UDDTs); no spare land
disqualifies ponds/wetlands (leaving compact reactors); no grid + low skill disqualifies
activated sludge (leaving ponds).

```
python engine/openwash.py validate    # provenance + tier honesty
python engine/openwash.py report       # corroboration audit
python engine/openwash.py siting       # the contested water-table value
python engine/openwash.py field        # design target vs deployed reality
python engine/dieoff.py  storage --temp 25 --days 180 --initial 10   # screen a storage design
python engine/select.py  --preset flood_plain                        # capability query
python engine/systems.py --preset flood_plain                        # build complete systems
```

Beyond selecting single technologies, [`engine/systems.py`](engine/systems.py) chains them into
**complete sanitation systems** — product-linked paths from user interface through
storage/treatment to reuse/disposal — then **enumerates every valid system and ranks them** by
appropriateness (simpler, lower-resource, and reuse-over-disposal score better), flagging the
reuse-safety checkpoint at each endpoint. It respects every site constraint through the whole
chain: a high water table disqualifies deep pits (flood plain → a urine-diverting dry system, no
pit); no reuse land forces disposal or offsite haul (dense urban); impermeable soil rules out
infiltration; and whether the site has a **managed offsite service** decides between hauling to
offsite treatment (dense urban *with* FSM → pour-flush → truck to offsite, score 3) and landfilling
onsite (same site *without* FSM → pit → landfill, score 5). So the output is a *ranked
recommendation* spanning onsite and offsite, not just a valid system.

## The guardrail — the substrate, made usable

The safety layer above is powerful but developer-facing. [`engine/safe_reuse.py`](engine/safe_reuse.py)
wraps it into a check a non-expert can run at the point of decision.

**No install — run it in a browser:** **[the interactive guardrail](https://sethc555.github.io/openwash/#try)**
(on the explainer page). Answer a few plain questions on a phone or laptop and get the verdict, the
fix, and a batch-verification plan. It runs the *same rules* as the engine — [`docs/guardrail.js`](docs/guardrail.js)
is a faithful port, and [`tests/parity.py`](tests/parity.py) checks it against the Python engine on
3,000+ designs on every commit (the `web_parity` attested claim), so it can never drift into a second,
unattested source of truth.

**Or from a terminal:**

```
python engine/safe_reuse.py            # answer a few plain questions, get a verdict
python engine/safe_reuse.py --demo     # worked examples: a safe and an unsafe reuse
```

You describe the material (faeces / urine / mixed blackwater / compost), the treatment
(storage time + temperature, ammonia/ash amendment + pH, or thermal composting), and
where it's going (crops eaten raw / restricted crops / non-food / soil). It returns
**SAFE-BY-SCREEN**, **UNSAFE**, or **NOT ENOUGH EVIDENCE** — always with the binding
pathogen, the log-reduction needed vs. achieved, the specific thing to change, and two
honest limits it never hides: it is a *screen, not a certificate* (verify by measurement),
and it says **nothing** about the chemical hazards in the [watch layer](data/watch.yaml)
(AMR, heavy metals, micropollutants). It says *unsafe* when it should, and *unknown* when
the evidence is thin — the opposite of a confident hallucination.

## Proof-of-thesis: the techno-economic study

The substrate narrowed its scope on a claim: **WASH fails on O&M, financing, governance,
and demand — not on missing specs; the technology is not the bottleneck.** A ~13-step
techno-economic design study tested that from the bottom up — taking one excreta-reuse
pathway all the way down to hardware, conveyance, operations, and financing — and re-derived
exactly it. The full record, including the over-claims it caught in its own numbers, is in
[`research/reading/ADVERSARIAL_ECON.md`](research/reading/ADVERSARIAL_ECON.md):

- **The engineering is cheap and solvable.** Every hardware idea worked; treatment is
  ~5% of operating cost. The design converges on a gravity, combined-blackwater,
  ammonia-sanitizing, ~90%-locally-fabricable system.
- **The binding constraints are institutional/financial** — capital structure, O&M and
  local ownership, and demand.
- **No product pathway self-funds it.** Nutrients have ~no market (recovered-nitrogen revenue
  offsets **<5% of opex**); fuel briquettes are the one product with real demand, but even so no
  pathway covers its cost. The honest break-even collection fee is **~$6/HH/month — and that is a
  floor** (it omits household-container capex, customer acquisition, and bad debt). **Safe excreta
  reuse is a subsidized public good** — public money is structurally required (upfront capital
  grant, or ongoing operating subsidy). The honest question is *who funds it*, not *how to make it
  pay for itself*.

Crucially, the study ran on the same honesty discipline as the substrate and kept catching
its **own** over-claims (a tuned +12 °C solar figure corrected to +4; nitrogen revenue over-claimed
at 40–70% of opex, actually <5%; a counterfactual "urea-avoided" credit booked as cash; 100% offtake
assumed) — recorded in [`research/reading/ADVERSARIAL_ECON.md`](research/reading/ADVERSARIAL_ECON.md)
and [`AUDIT.md`](AUDIT.md).
That is the point of the whole project applied to itself: refuse to launder an optimistic
number into a promise. In safety that prevents disease; in economics it prevents a system
built on a fantasy that can't be kept running.

## Layout

```
data/            sources.yaml (23) · reuse_safety.yaml (42 claims) · dieoff_kinetics.yaml
                 · technologies.yaml (54 techs) · costs.yaml · limitations.yaml · watch.yaml · model docs
engine/          safe_reuse.py (the guardrail — usable check) · openwash.py (safety table)
                 · dieoff.py (die-off screen) · select.py (capability query) · systems.py (system chaining)
                 · costs.py (cost lookup) · watch.py (non-pathogen hazards)
tests/           81 pytest checks — data integrity, corroboration, all 3 die-off regimes, capability
                 query, system chaining, limitations, watch layer, safe-reuse guardrail + verification
                 plan (+ regressions). `python -m pytest tests/`
docs/            index.html (the explainer + the no-install interactive guardrail)
                 · guardrail.js (the browser port, parity-checked against the engine)
research/
  reading/   SYNTHESIS (the evidence trail) · ADVERSARIAL (151-paper refutation scan)
             · ADVERSARIAL_ECON (the techno-economic study + the over-claims it caught)
claims.yaml      11 machine-verifiable claims — each reproduces iff it holds
attestation.json the re-runnable result of verifying them (11/11)
AUDIT.md         the honesty ledger — every over-claim caught, retracted, and pinned
```

> This is the open release: the sourced substrate, the engine, the guardrail, the tests,
> and the evidence/adversarial write-ups. The raw literature-scan dumps, the source-PDF
> mirror, and the illustrative techno-economic model scripts live in the project's working
> repository; every load-bearing conclusion from them is recorded in the reading/ docs above.

## Reproducible claims

The project applies its own honesty discipline to itself. Eleven load-bearing claims — that the engine
refuses naked numbers, that it caught a real over-claim, that it flags the Malawi field
contradiction as UNSAFE, that it says *"not enough evidence"* instead of guessing, that the die-off
model reproduces its published anchors, and that the browser guardrail matches the Python engine on
3,000+ designs — are declared in [`claims.yaml`](claims.yaml), each with a
command that **exits 0 if and only if the claim holds**. [`attestation.json`](attestation.json)
records the result (11/11). Trust is re-runnability, not our word — verify it yourself on a clean
checkout:

```
pip install -r requirements.txt
claimcheck verify claims.yaml          # or, without the tool: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/
```

This attests *computational reproducibility* — that the engine and dataset behave as described — not
the correctness of the underlying WASH science, which lives in the cited sources.

## Next

- ~~Grow the safety table toward the ~40-value target~~ ✓ (42 claims)
- ~~Add the die-off curve engine seeded by the `t90_*` constants~~ ✓ (`engine/dieoff.py`)
- ~~Add ammonia/pH terms to the kinetics~~ ✓ — `dieoff.py ammonia`, sourced from Nordin 2009
  (NH₃ speciation via Emerson pKa; rate calibrated to reproduce its four t99 anchor points) +
  Pecson 2007. It quantifies why ash/urea amendment (pH 9) sanitizes in ~50 days where plain
  storage needs a year.
- ~~Non-log-linear (shoulder/tail) Ascaris curve~~ — resolved by the evidence, not by adding one:
  Fidjeland 2015 *tested and rejected* a smooth-shoulder model (it over-predicted times ~2×) in
  favour of log-linear split at the lag breakpoint. So instead the engine (a) cross-checks the
  model against Fidjeland's independent t99 values (they fall on it) and (b) adds a **lag guard** —
  a "pass" reached in << t99 is flagged as relying on the optimistic early phase.
- ~~Sourced temperature scaling for the non-ammonia regime~~ ✓ — the die-off engine now covers the
  whole temperature space with three *sourced* regimes: ambient storage (WHO Table 4.5 categorical
  bands), ammonia amendment (Nordin/Fidjeland/Pecson), and **thermal ≥50 °C** (`dieoff.py thermal`,
  US EPA 40 CFR 503 time–temperature law, cross-checked against WHO/Haug). It even surfaces a WHO-vs-
  EPA disagreement: WHO's ">50 °C for 1 week" fails EPA's 13.2-day requirement at exactly 50 °C.
- ~~Normalize the EAWAG Compendium into the technology catalog and bolt the safety layer on top~~
  ✓ (`data/technologies.yaml`, 54 techs = the full Compendium set; the 3 not listed are semi-central duplicates of S.10/S.11/S.12).
- ~~Encode the product input→output linkage so the engine can chain technologies into whole
  *systems*~~ ✓ ~~return the optimal (ranked) system, not the first valid one~~ ✓ ~~apply land
  constraints to reuse endpoints + soil to infiltration~~ ✓ (`engine/systems.py`). Remaining:
  ~~add conveyance (sewers/transport) so systems span onsite→offsite~~ ✓ (C group + `offsite_service`
  capability). ~~Finish the catalog to all 57~~ ✓ (54 distinct techs = the full Compendium set).
- ~~Cost data~~ — sourced but deliberately *partial* (`data/costs.yaml` + `engine/costs.py`): real
  per-unit and per-capita anchors from Münch & Mayumbelo 2007 (Lusaka), each tagged with place/year/
  currency/scope. It's a **lookup, not a ranking dimension** — cost doesn't generalize across
  contexts, so faking a universal per-tech price list would violate the no-naked-numbers rule. (Bonus
  finding it surfaces: ecosan is *not* more expensive than conventional low-cost onsite sanitation.)
  A true cost-*ranking* still needs a normalized multi-context cost dataset, which doesn't cleanly exist.
- ~~Resolve the license question before curating~~ ✓ — resolved: the CC-BY-SA sources
  (Akvopedia/SSWM) were never used; the committed data is cited *facts* + our own schema/
  annotations (no rehosted source expression), so it ships **Apache-2.0 (code) + CC-BY-4.0
  (data/docs)** — permissive with attribution, unblocked for commercial/proprietary embedding.
  Full analysis + honest caveats (EU database rights; keep the no-rehost discipline; legal
  eyeball before a formal public launch) in [`LICENSING.md`](LICENSING.md).

See [`research/reading/SYNTHESIS.md`](research/reading/SYNTHESIS.md) for the full
evidence trail behind every claim above.
