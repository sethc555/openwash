#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH system builder — chain technologies into complete sanitation systems,
enumerate all that fit a site, and RANK them by appropriateness.

A *system* is a product-linked chain (Compendium model: output of one technology
is the input of the next) from a User Interface (U) through storage/treatment
(S/T) to Use or Disposal (D). This enumerates every complete, site-fitting
system and ranks them so the output is a recommendation, not just "a" system.

Appropriateness score (LOWER is better): sum over technologies of
  1 + skill_rank + 2·(needs power) + 1·(needs water),
  + 2 per disposal endpoint, − 1 per reuse endpoint.
So the top system is the simplest, lowest-resource, most nutrient-cycling one
that actually fits — with the reuse-safety checkpoint at every reuse endpoint.

Usage:
  python engine/systems.py --preset flood_plain
  python engine/systems.py --preset dense_urban --top 5
"""
import os, sys, argparse, importlib.util, yaml

ENG = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("owselect", os.path.join(ENG, "select.py"))
sel = importlib.util.module_from_spec(spec); spec.loader.exec_module(sel)
WATCH = yaml.safe_load(open(os.path.join(os.path.dirname(ENG), "data/watch.yaml")))["hazards"]

GROUP_ORDER = {"U": 0, "S": 1, "C": 2, "T": 3, "D": 4}
DISPOSAL = {"D.7", "D.8", "D.11", "D.12"}

def enumerate_systems(data, site, start, cap=3000):
    fit = {t["id"]: t for t in data["technologies"] if not sel.disqualifiers(t, site)}
    if start not in fit:
        return []
    def consumers(p):
        cs = [t for t in fit.values()
              if p in t.get("inputs", []) and t["group"] != "U" and p not in t.get("outputs", [])]
        return sorted(cs, key=lambda t: (0 if t["group"] == "D" and t["id"] not in DISPOSAL else
                                         2 if t["id"] in DISPOSAL else 1))
    results, seen = [], set()
    def dfs(open_p, chosen, depth):
        if len(results) >= cap or depth > 22:
            return
        if not open_p:
            key = frozenset(chosen)
            if key not in seen:
                seen.add(key); results.append(list(chosen))
            return
        p, rest = open_p[0], open_p[1:]
        cs = consumers(p)
        if not cs:
            return                                   # dead end: product cannot be routed
        for c in cs:
            if c["id"] in chosen:
                dfs(rest, chosen, depth + 1)         # streams converge on an existing step
            else:
                add = [] if c["group"] == "D" else [o for o in c.get("outputs", []) if o != "biomass"]
                dfs(rest + add, chosen + [c["id"]], depth + 1)
    open0 = [o for o in fit[start].get("outputs", []) if o != "biomass"]
    dfs(open0, [start], 0)
    return results

def score(system, byid):
    s = reuse = disposal = 0
    for i in system:
        t = byid[i]; r = t.get("requires", {})
        s += 1 + sel.SKILL.get(r.get("skilled_labour", "low"), 0) + 2*int(bool(r.get("power"))) + int(bool(r.get("water")))
        if t["group"] == "D":
            if t["id"] in DISPOSAL: disposal += 1
            elif "biomass" in t.get("outputs", []) or t.get("reuse_products"): reuse += 1
    return s + 2*disposal - reuse

def render(data, site, system, rank, sc):
    byid = {t["id"]: t for t in data["technologies"]}
    techs = sorted(set(system), key=lambda i: (GROUP_ORDER[byid[i]["group"]], i))
    def is_reuse(i):  # a D-terminal that grows biomass (in-situ) OR yields a handled reuse product
        t = byid[i]
        return t["group"] == "D" and i not in DISPOSAL and ("biomass" in t.get("outputs", []) or t.get("reuse_products"))
    has_reuse = any(is_reuse(i) for i in techs)
    has_disposal = any(i in DISPOSAL for i in techs)
    has_offsite = any(byid[i]["group"] == "C" for i in techs)
    label = ("reuse-complete" if has_reuse and not has_disposal and not has_offsite else
             "offsite-managed" if has_offsite and not has_reuse else
             "mixed reuse/disposal" if has_reuse else
             "disposal-only")
    print(f"  #{rank}  score {sc}  ({len(techs)} techs, {label})")
    for i in techs:
        t = byid[i]
        io = f"[{'+'.join(t.get('inputs',[])) or '—'}] → [{'+'.join(t.get('outputs',[])) or 'end'}]"
        print(f"       {t['id']:<5} {t['name']:<40} {io}")
    # Pathogen safety flag. (a) any node carrying a hinted reuse product; (b) any reuse ENDPOINT
    # that grows biomass but produced no hinted flag above (e.g. an arborloo, or land-applied
    # material with an un-hinted product) — so NO reuse endpoint escapes the pathogen screen.
    checks = [(i, sel.REUSE_HINT[rp]) for i in techs
              for rp in byid[i].get("reuse_products", []) if rp in sel.REUSE_HINT]
    flagged = {i for i, _ in checks}
    for i in techs:
        if is_reuse(i) and i not in flagged:
            checks.append((i, "in-situ biomass / edible reuse → the applied excreta or humus must meet "
                              "<1 viable helminth egg/g TS before edible-crop use; untreated shallow-pit "
                              "reuse (e.g. an arborloo fruit tree) is a direct fecal–oral pathway "
                              "(reuse_safety verify_faeces_helminth)"))
    for i, hint in checks:
        print(f"       ⚑ {i} → {hint}")
    reuse_prods = {rp for i in techs for rp in byid[i].get("reuse_products", [])}
    watch = sorted({h["name"].split(" (")[0] for h in WATCH if reuse_prods & set(h["applies_to_products"])})
    if watch:
        print(f"       ⚠ non-pathogen watch (not in the safety screen — see watch.py): {', '.join(watch)}")

def run(data, site, top=3):
    print(f"SYSTEM BUILDER — {site.get('desc','(custom site)')}")
    print(f"  site: setting={site['setting']}, water_table={site.get('water_table_depth_m')} m, "
          f"land={site.get('land_m2_per_capita')} m²/cap, soil={site.get('soil_permeability','good')}, "
          f"skill={site['skilled_labour']}, power={site['power']}, piped_water={site['piped_water']}\n")
    byid = {t["id"]: t for t in data["technologies"]}
    fit = {t["id"] for t in data["technologies"] if not sel.disqualifiers(t, site)}
    # a sanitation system must manage FAECES — a urine-only interface (urinal) is a
    # supplement, not a system root.
    FAECES_BEARING = {"excreta", "faeces", "blackwater", "brownwater"}
    interfaces = [t["id"] for t in data["technologies"] if t["group"] == "U" and t["id"] in fit
                  and FAECES_BEARING & set(t.get("outputs", []))]
    allsys, seen = [], set()
    dead_interfaces = []
    for u in interfaces:
        got = enumerate_systems(data, site, u)
        if not got:
            dead_interfaces.append(u)
        for s in got:
            k = frozenset(s)
            if k not in seen:
                seen.add(k); allsys.append(s)
    if not allsys:
        print("  no complete system fits this site."
              + (f" (interfaces that fit but can't be completed: {', '.join(dead_interfaces)})" if dead_interfaces else ""))
        return
    ranked = sorted(allsys, key=lambda s: (score(s, byid), len(set(s))))
    print(f"  {len(allsys)} complete system(s) found; showing top {min(top,len(ranked))} "
          f"(lower score = simpler / lower-resource / more reuse):\n")
    for rank, s in enumerate(ranked[:top], 1):
        render(data, site, s, rank, score(s, byid))
        print()
    if dead_interfaces:
        print(f"  note: {', '.join(dead_interfaces)} fit the site but cannot be completed "
              f"(a product had no site-fitting downstream option — e.g. no reuse land / no permeable soil).")

def main():
    data = sel.load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(sel.PRESETS))
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--setting", choices=["household","small_community","community"])
    ap.add_argument("--water-table", type=float, dest="wt")
    ap.add_argument("--land", type=float); ap.add_argument("--soil", choices=["good","poor"], default="good")
    ap.add_argument("--skill", choices=["low","medium","high"])
    ap.add_argument("--power", action="store_true"); ap.add_argument("--piped-water", action="store_true", dest="piped")
    ap.add_argument("--offsite-service", action="store_true", dest="offsite")
    a = ap.parse_args()
    if a.preset:
        site = sel.PRESETS[a.preset]
    else:
        if not a.setting: sys.exit("give --preset or --setting")
        site = dict(setting=a.setting, water_table_depth_m=a.wt, land_m2_per_capita=a.land,
                    soil_permeability=a.soil, offsite_service=a.offsite, skilled_labour=a.skill or "low",
                    power=a.power, piped_water=a.piped, desc="(custom site)")
    run(data, site, a.top)

if __name__ == "__main__":
    main()
