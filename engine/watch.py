#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH reuse-hazard watch layer — the non-pathogen hazards the safety table
does NOT cover (AMR/ARGs, micropollutants, heavy metals).

A flag layer, not a quantitative model: there is no accepted reduction target for
these the way there is for pathogens, so the output is a sourced WARNING per reuse
pathway — "passing the pathogen screen says nothing about this."

Usage:
  python engine/watch.py --product effluent
  python engine/watch.py --product urine
  python engine/watch.py --list
"""
import os, argparse, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load():
    watch = yaml.safe_load(open(os.path.join(ROOT, "data/watch.yaml")))
    sources = yaml.safe_load(open(os.path.join(ROOT, "data/sources.yaml")))["sources"]
    return watch, sources

def hazards_for(watch, product):
    return [h for h in watch["hazards"] if product in h.get("applies_to_products", [])]

def cite(s, sources):
    return sources.get(s["ref"], {}).get("org", s["ref"])

def show(h, sources):
    print(f"  ⚠ {h['name']}")
    print(f"      why the safety screen misses it: {h['why_the_safety_table_misses_it'].strip()}")
    for e in h.get("evidence", []):
        print(f"      • {e['finding']}  [{cite(e['source'], sources)}]")
    print(f"      disposition: {h['disposition'].strip()}")

def cmd_product(watch, sources, product):
    hs = hazards_for(watch, product)
    print(f"REUSE-HAZARD WATCH — product '{product}'  (beyond the pathogen safety screen)")
    if not hs:
        prods = sorted({p for h in watch["hazards"] for p in h["applies_to_products"]})
        print(f"  no watch-layer hazards flagged for '{product}'. Flagged products: {', '.join(prods)}")
        return
    for h in hs:
        show(h, sources)

def cmd_list(watch, sources):
    print("REUSE-HAZARD WATCH LAYER (non-pathogen hazards NOT in the safety table)\n")
    for h in watch["hazards"]:
        print(f"  {h['id']:<16} {h['name']}")
        print(f"      applies to reuse of: {', '.join(h['applies_to_products'])}")
    print(f"\n  note: {watch['meta']['note']}")

def main():
    watch, sources = load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--product"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.product: cmd_product(watch, sources, a.product)
    elif a.list: cmd_list(watch, sources)
    else: ap.print_help()

if __name__ == "__main__":
    main()
