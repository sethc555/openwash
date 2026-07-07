# OpenWASH data model (v0.1)

Two hand-curated YAML files + a single-file engine. No database yet — this is the
"prove the moat before building the machine" spike.

- `sources.yaml` — the upstream registry. Each source has a **`lineage`**.
- `reuse_safety.yaml` — the excreta/urine/wastewater reuse safety table (~42 claims).
- `dieoff_kinetics.yaml` — pathogen die-off parameters (T90 + temperature rates) that seed the constraint engine.
- `../engine/openwash.py` — loads, validates, and queries the safety table.
- `../engine/dieoff.py` — the constraint engine: screens storage/treatment regimes for pathogen-reduction sufficiency.

## The four design decisions (each forced by the reading, see `../research/reading/SYNTHESIS.md`)

### 1. No naked numbers
Every value carries `sources: [{ref, page|locator}]`. The engine errors if a value has
no resolvable source. A number without provenance does not get committed.

### 2. Tier is *computed*, not asserted
Each source has a `lineage`. Two documents with the **same lineage are not independent**
— one restates or derives from the other, so they don't compound into higher trust. A
source ref may carry `restates: <lineage>` to mark it as an echo (e.g. the WHO SSP manual
reproduces the WHO 2006 reduction targets verbatim).

The engine counts **distinct independent lineages** and computes:
- `multi_corroborated` — ≥ 2 independent lineages agree
- `single_lineage` — several documents, but one derivation (authoritative, not independent)
- `single_sourced` — one source

It then compares this to the human-entered `claimed_tier` and flags **over-claims**. This
caught a real one: the 6/7-log irrigation target appears in WHO Vol 4, Vol 2, *and* SSP, and
was written up as "three sources agree" — but all three share the `who_2006_reuse` lineage,
so the honest tier is `single_lineage`. The setback (Sphere + EAWAG) is the genuine
`multi_corroborated` value. Run `openwash.py report` to see the audit.

### 3. `design_target` ≠ `field_verified`
The `target_vs_field` claim shape keeps two facts separate:
- **design_target** — the guideline value *under assumed conditions* (well-corroborated), and
- **field** — whether deployed reality achieves it (`corroborated` / `contradicted`), with its
  own evidence, tier, and caveat.

Forced by the die-off literature: WHO's thermophilic-composting formula is corroborated by an
independent field study (Manga 2020), but the *passive-storage* pathway is **contradicted** in
deployment (Kumwenda 2019, Malawi — 12-month sludge still above helminth limits, Salmonella
regrowing). A naive engine would stamp the design number "safe" and ship false confidence.

### 4. Contested values are surfaced, never averaged
The `contested` shape keeps every candidate with its source. Sphere says pit-bottom clearance
above the water table is ≥ 1.5 m; the EAWAG Compendium says ≥ 2 m. The engine shows both and
applies a stated `resolution` (here `use_most_conservative` → 2 m). It never emits 1.75 m —
the average is nobody's recommendation.

## Claim shapes (exactly one per claim)

```yaml
# simple value
value: {value, unit, qualifier?, sources: [{ref, page?, locator?, restates?}], claimed_tier}

# sources disagree
contested:
  candidates: [{value, unit, sources: [...]}, ...]
  resolution: use_most_conservative
  resolved: {value, unit}

# guideline vs deployment
target_vs_field:
  design_target: { ...value block... }
  field: {status: corroborated|contradicted, finding, sources: [...], tier, caveat}
```

`value` may be a scalar, a range `{min, max}`, a mean `{mean, sd}`, a list, or text.

## The constraint engine (the safety layer, not a nice-to-have)

`dieoff.py` turns the die-off constants into a screen for the naive "just store/bury it"
design. It models first-order (log-linear) inactivation, `LR(t) = k(T)·t`, seeded from
WHO Table 3.5 (T90) and Table 3.8 (temperature rates). Three honesty rules are built in:

1. **Matrix-correct** — Table 3.8 rates are from *liquid* matrices; they're only applied to
   liquid queries. A faeces-storage query falls back to the matrix-correct faeces T90.
2. **Screen, not certifier** — the first-order model is *optimistic* (real Ascaris die-off
   has tails and is non-monotonic in the field). It rules OUT insufficient designs
   (necessary condition); it never certifies safety.
3. **Sides with the conservative signal** — when the optimistic model and the WHO categorical
   storage rule disagree, the engine screens the design out and says so. This is why a
   6-month passive UDDT at 25 °C is correctly flagged UNSAFE (WHO rule needs ≥ 12 months),
   matching the Kumwenda field finding — even though the bare log-linear model would wave it
   through.

## Commands
```
python engine/openwash.py validate    # provenance + tier-honesty check
python engine/openwash.py report       # corroboration audit (claimed vs computed)
python engine/openwash.py query --use unrestricted_irrigation --crop leaf
python engine/openwash.py siting       # includes the contested water-table value
python engine/openwash.py field        # design target vs deployed reality

python engine/dieoff.py storage --temp 25 --days 180 --initial 10   # plain-storage screen
python engine/dieoff.py ammonia --ph 9 --total-ammonia 360 --temp 25 --days 30   # ash/ammonia amendment
python engine/dieoff.py ammonia --validate                          # model vs Nordin/Fidjeland anchors
python engine/dieoff.py thermal --temp 55 --days 3                  # composting/pasteurisation (>=50 C, EPA 503)
python engine/dieoff.py predict --organism ascaris --matrix faeces --days 400 --temp 25
python engine/dieoff.py table --temp 20 --days 90

python engine/select.py  --preset flood_plain    # capability query (single-tech selection)
python engine/systems.py --preset flood_plain    # chain technologies into complete systems
python engine/costs.py   --list                  # sourced (partial, context-specific) cost anchors

python -m pytest tests/                           # 74 checks — run from repo root
```
`costs.yaml` holds sourced cost anchors (Münch 2007, Lusaka) with full place/year/currency/scope
context — a lookup, not a ranking (cost doesn't generalize). `tests/` guards every invariant above.
`technologies.yaml` (54 techs from the EAWAG Compendium, all 5 functional groups) is keyed by an
input→output product vocabulary; `select.py` filters technologies by site constraints (water
table, land, soil, skill, power, water, offsite service), `systems.py` follows the product links
to build and rank complete interface→treatment→reuse/disposal/offsite systems and attaches the
reuse-safety checkpoint at each endpoint. Requires `pyyaml` (in `../research/.venv`).

## Scope honesty
The safety table is the excreta-reuse *safety* slice — the sharpest, most defensible cut. The
technology catalog is 54 techs — the full Compendium set across all 5 functional groups. The
die-off constants (`t90_*`) seed the constraint engine (temperature/time → helminth-egg
viability); `Ascaris` is the binding pathogen and every thermal/storage rule is really an
Ascaris-kill rule. `systems.py` enumerates and **ranks** complete systems (not just the first
valid one) and applies land constraints to reuse endpoints and soil to infiltration. There is
also a usable **reuse-safety guardrail** (`engine/safe_reuse.py`) and a techno-economic
proof-of-thesis study in `../research/` — see the top-level `README.md`.
