#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH cost lookup — sourced, context-specific cost anchors.

Cost is the one dimension that does NOT generalize across contexts, so this is a
provenance-tagged LOOKUP of sourced anchors, not a ranking dimension. Coverage is
deliberately partial (only what a source actually reports), and the caveat prints
every time. Compare figures only within the same source/context.

Usage:
  python engine/costs.py --tech S.3
  python engine/costs.py --systems
  python engine/costs.py --list
"""
import os, argparse, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load():
    costs = yaml.safe_load(open(os.path.join(ROOT, "data/costs.yaml")))
    sources = yaml.safe_load(open(os.path.join(ROOT, "data/sources.yaml")))["sources"]
    return costs, sources

def amt(v):
    a = f"{v['amount_range'][0]}–{v['amount_range'][1]}" if "amount_range" in v else str(v.get("amount"))
    return f"{a} {v.get('currency', v.get('unit',''))} ({v.get('year','')})".strip()

def cite(s, sources):
    org = sources.get(s["ref"], {}).get("org", s["ref"])
    return org + (f", {s['locator']}" if s.get("locator") else "")

def show_tech(costs, sources, tid):
    rows = [c for c in costs["technology_costs"] if c["tech"] == tid]
    print(f"COST ANCHORS — technology {tid}")
    if not rows:
        covered = sorted({c["tech"] for c in costs["technology_costs"]})
        print(f"  no sourced cost data for {tid}. Coverage is partial; techs with data: {', '.join(covered)}")
        return
    for c in rows:
        print(f"  {amt(c['value']):<26} {c.get('scope','')}  [{c.get('place','')}]")
        print(f"      src: {cite(c['source'], sources)}")

def show_systems(costs, sources):
    print("WHOLE-SYSTEM COST ANCHORS (per capita)")
    for s in costs["system_costs"]:
        print(f"  • {s['system']}")
        print(f"      capital {amt(s['capital'])}  ·  O&M {amt(s['om'])}   [{s.get('place','')}]")
        if s.get("finding"):
            print(f"      finding: {s['finding']}")
        print(f"      src: {cite(s['source'], sources)}")

def caveat(costs):
    print(f"\n  ⚠ {costs['meta']['caveat']}. Compare only WITHIN the same source/context.")

def main():
    costs, sources = load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--tech"); ap.add_argument("--systems", action="store_true"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.tech: show_tech(costs, sources, a.tech)
    elif a.systems: show_systems(costs, sources)
    elif a.list:
        covered = sorted({c["tech"] for c in costs["technology_costs"]})
        print(f"technologies with sourced cost anchors: {', '.join(covered)}\n")
        show_systems(costs, sources)
    else:
        ap.print_help(); return
    caveat(costs)

if __name__ == "__main__":
    main()
