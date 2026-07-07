#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH v0.1 engine — load, validate, and query the reuse safety table.

The point of v0.1 is to prove the moat on real data:
  1. provenance is enforced (no naked numbers),
  2. corroboration tier is COMPUTED from source lineage, not trusted from the
     `claimed_tier` field — so the engine catches over-claims (e.g. "3 WHO docs
     agree" is really 1 independent lineage echoed 3 times),
  3. contested values are surfaced with both candidates, never averaged,
  4. design_target and field (deployed reality) are kept as separate facts.

Usage:
  python engine/openwash.py validate
  python engine/openwash.py query  --use unrestricted_irrigation --crop leaf
  python engine/openwash.py siting
  python engine/openwash.py field
  python engine/openwash.py report        # corroboration audit of every claim
"""
import sys, os, argparse, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load():
    with open(os.path.join(ROOT, "data/sources.yaml")) as f:
        sources = yaml.safe_load(f)["sources"]
    with open(os.path.join(ROOT, "data/reuse_safety.yaml")) as f:
        data = yaml.safe_load(f)
    return sources, data

# ---- helpers ---------------------------------------------------------------
def fmt_val(v):
    if isinstance(v, dict):
        if "min" in v: return f"{v['min']}–{v['max']}"
        if "mean" in v: return f"{v['mean']}±{v.get('sd','?')}"
        return str(v)
    if isinstance(v, list): return "; ".join(fmt_val(x) if not isinstance(x, dict) else
                                             ", ".join(f"{k}={val}" for k,val in x.items()) for x in v)
    return str(v)

def fmt_value_block(vb):
    q = vb.get("qualifier", "")
    return f"{q}{fmt_val(vb['value'])} {vb.get('unit','')}".strip()

def cite(ref_obj, sources):
    r = ref_obj["ref"]
    loc = ref_obj.get("locator")
    pg = ref_obj.get("page")
    tag = sources.get(r, {}).get("org", r)
    year = sources.get(r, {}).get("year", "")
    bits = [f"{tag} {year}".strip()]
    if pg: bits.append(f"p.{pg}")
    if loc: bits.append(loc)
    s = ", ".join(bits)
    if ref_obj.get("restates"): s += f" [restates {ref_obj['restates']}]"
    return s

def value_blocks(claim):
    """Yield (label, value_block) for every value-bearing block in a claim."""
    if "value" in claim: yield ("value", claim["value"])
    if "target_vs_field" in claim:
        yield ("design_target", claim["target_vs_field"]["design_target"])
        # field block has sources too but no `value`+tier the same way
    if "contested" in claim:
        for i, c in enumerate(claim["contested"]["candidates"]):
            yield (f"candidate[{i}]", c)

# ---- corroboration: the core logic ----------------------------------------
def independent_lineages(value_block, sources):
    """Distinct INDEPENDENT lineages backing a value. A source that `restates`
    another lineage is an ECHO — it reinforces that lineage but can NEVER manufacture
    a new independent one, even when no primary of that lineage is separately cited.
    (The old code did `lineages.add(s['restates'])`, which phantom-credited a lineage
    whenever a restatement's primary was absent — a latent over-corroboration bug.)"""
    primary, restated = set(), set()
    for s in value_block.get("sources", []):
        if s.get("restates"):
            restated.add(s["restates"])            # an echo — not independent
        else:
            primary.add(sources.get(s["ref"], {}).get("lineage", s["ref"]))
    # Independence comes only from primaries. Restatements stand in ONLY when a value is
    # cited solely by echoes (rare edge) — and then they count as that one echoed lineage.
    return primary or restated

def computed_tier(value_block, sources):
    lin = independent_lineages(value_block, sources)
    nsrc = len(value_block.get("sources", []))
    if len(lin) >= 2: return "multi_corroborated"
    if nsrc >= 2:     return "single_lineage"       # multiple docs, one lineage — echoed, not independent
    return "single_sourced"

# ---- validation ------------------------------------------------------------
def validate(sources, data):
    errs, warns = [], []
    ids = set()
    for c in data["claims"]:
        cid = c["id"]
        if cid in ids: errs.append(f"{cid}: duplicate id")
        ids.add(cid)
        shapes = [k for k in ("value","contested","target_vs_field") if k in c]
        if len(shapes) != 1:
            errs.append(f"{cid}: must have exactly one of value/contested/target_vs_field (has {shapes})")
            continue
        # no naked numbers + source resolution
        blocks = list(value_blocks(c))
        if "target_vs_field" in c:
            blocks.append(("field", c["target_vs_field"]["field"]))
        for label, vb in blocks:
            srcs = vb.get("sources", [])
            if not srcs:
                errs.append(f"{cid}.{label}: naked number — no source"); continue
            for s in srcs:
                if s["ref"] not in sources:
                    errs.append(f"{cid}.{label}: unknown source '{s['ref']}'")
                if not s.get("page") and not s.get("locator"):
                    warns.append(f"{cid}.{label}: source {s['ref']} has no page/locator")
        # contested sanity
        if "contested" in c:
            vals = [cand["value"] for cand in c["contested"]["candidates"]]
            if len(set(map(str,vals))) < 2:
                errs.append(f"{cid}: marked contested but candidates don't differ")
        # tier audit (the interesting part) — computed vs claimed for EVERY block that
        # carries a claimed_tier (value, design_target, contested candidates), not just
        # the top-level `value`. The "tier is computed, not trusted" guarantee must cover
        # target_vs_field and contested shapes too, or a third of claims escape it.
        for label, vb in value_blocks(c):
            claimed = vb.get("claimed_tier")
            if not claimed:
                continue
            comp = computed_tier(vb, sources)
            if claimed == "multi_corroborated" and comp != "multi_corroborated":
                loc = cid if label == "value" else f"{cid}.{label}"
                warns.append(f"{loc}: claims '{claimed}' but only {comp} "
                             f"(lineages: {sorted(independent_lineages(vb, sources))}) — OVER-CLAIM")
    return errs, warns

def cmd_validate(sources, data):
    errs, warns = validate(sources, data)
    n = len(data["claims"])
    print(f"OpenWASH reuse_safety v{data['meta']['version']} — {n} claims\n")
    if errs:
        print(f"✗ {len(errs)} ERRORS:")
        for e in errs: print(f"    {e}")
    else:
        print("✓ no errors — every value has a resolvable source (no naked numbers)")
    print(f"\n{len(warns)} tier/provenance flags:")
    for w in warns: print(f"    ⚠ {w}")
    return 1 if errs else 0

# ---- queries ---------------------------------------------------------------
def cmd_report(sources, data):
    print("Corroboration audit — computed tier vs claimed (lineage-based)\n")
    print(f"{'claim':<38}{'claimed':<20}{'COMPUTED':<20}lineages")
    print("-"*100)
    for c in data["claims"]:
        cid = (c["id"][:36]+"…") if len(c["id"]) > 37 else c["id"]
        if "value" not in c:
            shape = "contested" if "contested" in c else "target_vs_field"
            print(f"{cid:<39}{'-':<20}{shape:<20}(special shape)")
            continue
        claimed = c["value"].get("claimed_tier","?")
        comp = computed_tier(c["value"], sources)
        lin = sorted(independent_lineages(c["value"], sources))
        flag = "  <== OVER-CLAIM" if (claimed=="multi_corroborated" and comp!="multi_corroborated") else ""
        print(f"{cid:<39}{claimed:<20}{comp:<20}{','.join(lin)}{flag}")

def cmd_query(sources, data, use, crop=None, labour=None):
    print(f"CAPABILITY QUERY: use={use} crop={crop} labour={labour}\n")
    # find matching log-reduction requirement
    match = None
    for c in data["claims"]:
        if c["category"] != "log_reduction_requirement": continue
        sc = c.get("scenario", {})
        if sc.get("use") != use: continue
        if crop and sc.get("crop") and sc["crop"] != crop: continue
        if labour and sc.get("labour") and sc["labour"] != labour: continue
        if (crop and sc.get("crop")==crop) or (labour and sc.get("labour")==labour) or (not crop and not labour):
            match = c; break
    if not match:
        print("  no matching reduction requirement."); return
    req = match["value"]["value"]
    print(f"  Required reduction: {req} log10")
    for s in match["value"]["sources"]:
        print(f"    src: {cite(s, sources)}")
    print(f"    computed tier: {computed_tier(match['value'], sources)}\n")
    print("  Barrier menu to reach it (each credit summed must total the requirement):")
    for c in data["claims"]:
        if c["category"] == "barrier_credit":
            print(f"    - {c['parameter']:<52} {fmt_value_block(c['value'])}")
    print("\n  Example valid combination (WHO Box 4.1 logic): treatment 4 + field die-off 1 + washing 1 = 6 log.")
    print("  Verification: measure treated wastewater at <=1e3 E. coli/100 mL and <=1 helminth egg/L.")

def cmd_siting(sources, data):
    print("SITING CONSTRAINTS (the 'don't ship a disease vector' bounds)\n")
    for c in data["claims"]:
        if c["category"] != "siting_constraint": continue
        print(f"  {c['parameter']}")
        if "value" in c:
            print(f"    -> {fmt_value_block(c['value'])}   [tier: {computed_tier(c['value'], sources)}]")
            for s in c["value"]["sources"]: print(f"       {cite(s, sources)}")
        elif "contested" in c:
            print("    !! CONTESTED — sources disagree; both kept, NOT averaged:")
            for cand in c["contested"]["candidates"]:
                srcs = "; ".join(cite(s, sources) for s in cand["sources"])
                print(f"       {cand['value']} {cand['unit']:<4}  <- {srcs}")
            r = c["contested"]["resolved"]
            print(f"       resolution ({c['contested']['resolution']}): use {r['value']} {r['unit']}")
        print(f"       note: {c.get('notes','')}\n")

def cmd_field(sources, data):
    print("DESIGN TARGET vs FIELD REALITY (formula != deployed outcome)\n")
    for c in data["claims"]:
        if "target_vs_field" not in c: continue
        tvf = c["target_vs_field"]
        dt, fld = tvf["design_target"], tvf["field"]
        print(f"  {c['parameter']}")
        print(f"    DESIGN TARGET : {fmt_value_block(dt)}")
        print(f"                    tier {computed_tier(dt, sources)} | {'; '.join(cite(s,sources) for s in dt['sources'])}")
        badge = {"corroborated":"✓ CORROBORATED","contradicted":"✗ CONTRADICTED"}.get(fld["status"], fld["status"])
        print(f"    FIELD REALITY : {badge}")
        print(f"                    {fld['finding']}")
        print(f"                    src: {'; '.join(cite(s,sources) for s in fld['sources'])}")
        print(f"                    caveat: {fld['caveat']}\n")

# ---- main ------------------------------------------------------------------
def main():
    sources, data = load()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate"); sub.add_parser("report")
    sub.add_parser("siting"); sub.add_parser("field")
    q = sub.add_parser("query")
    q.add_argument("--use", required=True); q.add_argument("--crop"); q.add_argument("--labour")
    a = ap.parse_args()
    if a.cmd == "validate": sys.exit(cmd_validate(sources, data))
    if a.cmd == "report": cmd_report(sources, data)
    if a.cmd == "siting": cmd_siting(sources, data)
    if a.cmd == "field": cmd_field(sources, data)
    if a.cmd == "query": cmd_query(sources, data, a.use, a.crop, a.labour)

if __name__ == "__main__":
    main()
