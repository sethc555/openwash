#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH capability query — technology selection under site constraints.

The original wedge: given a site (population/scale, water-table depth, land,
skilled labour, power, water), return the technologies that FIT and show the
DISQUALIFYING constraint for the ones that don't — not just the winner.

Reuse outputs are linked back to the safety layer (reuse_safety.yaml +
engine/dieoff.py) so selection and safety are one system.

Usage:
  python engine/select.py --preset flood_plain
  python engine/select.py --setting community --land 0.5 --skill high --power --piped-water
"""
import os, sys, argparse, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = {"low": 0, "medium": 1, "high": 2}
SCALE_RANK = {"household": 0, "small_community": 1, "community": 2}

def load():
    with open(os.path.join(ROOT, "data/technologies.yaml")) as f:
        return yaml.safe_load(f)

PRESETS = {
    "flood_plain":     dict(setting="household", water_table_depth_m=1.0, land_m2_per_capita=20,
                            soil_permeability="good", offsite_service=False, skilled_labour="low", power=False, piped_water=False,
                            desc="Coastal/flood-plain village: water table ~1 m, ample land, no grid, no piped water"),
    "dense_urban":     dict(setting="community", water_table_depth_m=8.0, land_m2_per_capita=0.5,
                            soil_permeability="good", offsite_service=True, skilled_labour="high", power=True, piped_water=True,
                            desc="Dense urban lowland: no spare land, but has grid, skilled operators, piped water + offsite FSM"),
    "rural_ample_land":dict(setting="community", water_table_depth_m=8.0, land_m2_per_capita=12,
                            soil_permeability="good", offsite_service=False, skilled_labour="low", power=False, piped_water=True,
                            desc="Rural community: lots of land, no grid, low skilled-labour, no offsite service"),
    "water_scarce":    dict(setting="household", water_table_depth_m=8.0, land_m2_per_capita=20,
                            soil_permeability="poor", offsite_service=False, skilled_labour="low", power=False, piped_water=False,
                            desc="Water-scarce village: no piped water, deep water table, low skill, impermeable (clay) soil"),
}

REUSE_HINT = {
    "sludge":       "faecal sludge → storage/composting safety screen (dieoff.py storage)",
    "dried_faeces": "dried faeces → WHO storage rule + Ascaris screen (dieoff.py storage)",
    "compost":      "compost → thermophilic ≥50 °C/≥1 wk (reuse_safety composting_thermophilic)",
    "pit_humus":    "pit humus → variable reduction; treat as unsanitized (Kumwenda caveat)",
    "biosolids":    "biosolids (treated sludge) → land application needs <1 viable helminth egg/g TS (reuse_safety verify_faeces_helminth)",
    "urine":        "urine → storage rule 20 °C/≥6 mo for all crops (reuse_safety urine_storage)",
    "effluent":     "effluent to irrigation → required log reduction 6–7 (reuse_safety logred_*)",
}

def disqualifiers(tech, site):
    """Return list of (constraint, reason) that disqualify this tech, else []."""
    out = []
    req = tech.get("requires", {})
    # scale: disqualify only if the tech's smallest scale is bigger than the site
    # (household toilets belong in a community system; a community plant does not fit a household)
    site_rank = SCALE_RANK.get(site["setting"], 0)
    tech_min = min((SCALE_RANK[s] for s in tech.get("scale", []) if s in SCALE_RANK), default=0)
    if tech_min > site_rank:
        smallest = min(tech.get("scale", []), key=lambda s: SCALE_RANK.get(s, 0))
        out.append(("scale", f"needs at least {smallest}; site is {site['setting']}"))
    # water / power
    if req.get("water") and not site["piped_water"]:
        out.append(("water", "needs a piped/reliable water supply; site has none"))
    if req.get("power") and not site["power"]:
        out.append(("power", "needs continuous electricity; site is off-grid"))
    # skilled labour
    need = SKILL.get(req.get("skilled_labour", "low"), 0)
    have = SKILL.get(site["skilled_labour"], 0)
    if need > have:
        out.append(("skilled_labour", f"needs {req['skilled_labour']} skill; site has {site['skilled_labour']}"))
    # water table vs pit depth — FAIL-CLOSED: a safety tool must not clear a deep pit at a site
    # whose water-table depth is unknown (silently passing an un-screenable pit is a false-fit).
    sit = tech.get("siting", {})
    if sit.get("pit_depth_m") is not None:
        wt = site.get("water_table_depth_m")
        clr = sit.get("clearance_above_water_table_m", 0)
        need_depth = sit["pit_depth_m"] + clr
        if wt is None:
            out.append(("water_table_unknown",
                        f"needs the water-table depth to screen a {sit['pit_depth_m']} m pit (+{clr} m "
                        f"clearance = {need_depth} m); site did not provide it"))
        elif wt < need_depth:
            out.append(("water_table",
                        f"pit is {sit['pit_depth_m']} m deep + {clr} m clearance = needs {need_depth} m; "
                        f"water table at {wt} m"))
    # land
    land = site.get("land_m2_per_capita")
    lpc = tech.get("land_m2_per_capita")
    if isinstance(lpc, dict):
        req_land = lpc["value"]["min"]
        if land is None:
            out.append(("land_unknown", f"needs {req_land}+ m²/person; site land not provided"))
        elif land < req_land:
            out.append(("land", f"needs {req_land}+ m²/person; site has {land}"))
    elif tech.get("land_demand") == "high":
        thr = 3   # engine heuristic (see technologies.yaml meta.heuristics)
        if land is None:
            out.append(("land_unknown", f"land-hungry (>~{thr} m²/person heuristic); site land not provided"))
        elif land < thr:
            out.append(("land", f"land-hungry (>~{thr} m²/person heuristic); site has {land}"))
    # reuse endpoints need agricultural land (heuristic ~1 m²/person) — fail-closed on unknown
    if req.get("reuse_land"):
        if land is None:
            out.append(("reuse_land_unknown", "on-site reuse needs land (>~1 m²/person); site land not provided"))
        elif land < 1:
            out.append(("reuse_land", f"on-site reuse needs land (>~1 m²/person); site has {land}"))
    # infiltration endpoints need permeable soil
    if req.get("permeable_soil") and site.get("soil_permeability", "good") != "good":
        out.append(("soil", f"needs permeable soil to infiltrate; site soil is {site.get('soil_permeability')}"))
    # conveyance-to-offsite needs a functioning offsite FSM/sewerage service
    if req.get("offsite_service") and not site.get("offsite_service", False):
        out.append(("offsite_service", "needs a functioning offsite FSM/sewerage service; site has none"))
    return out

def appropriateness(tech):
    """Lower resource requirement sorts first (appropriate-tech ordering)."""
    r = tech.get("requires", {})
    return (SKILL.get(r.get("skilled_labour","low"),0), int(bool(r.get("power"))), int(bool(r.get("water"))))

def run(data, site):
    print(f"CAPABILITY QUERY — {site.get('desc','(custom site)')}")
    print(f"  site: setting={site['setting']}, water_table={site.get('water_table_depth_m')} m, "
          f"land={site.get('land_m2_per_capita')} m²/cap, skill={site['skilled_labour']}, "
          f"power={site['power']}, piped_water={site['piped_water']}\n")
    fit, disq = [], []
    for t in data["technologies"]:
        d = disqualifiers(t, site)
        (disq if d else fit).append((t, d))
    fit.sort(key=lambda x: appropriateness(x[0]))
    print(f"  ✓ FITS ({len(fit)}):")
    for t, _ in fit:
        reuse = [p for p in t.get("reuse_products", [])]
        tag = f"   ⚑ {REUSE_HINT.get(reuse[0])}" if reuse and reuse[0] in REUSE_HINT else ""
        print(f"      {t['id']:<5} {t['name']}")
        if tag: print(f"           {tag.strip()}")
    print(f"\n  ✗ DISQUALIFIED ({len(disq)}):")
    for t, reasons in sorted(disq, key=lambda x: x[0]['id']):
        rs = "; ".join(f"[{c}] {why}" for c, why in reasons)
        print(f"      {t['id']:<5} {t['name']:<42} {rs}")

def main():
    data = load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS))
    ap.add_argument("--setting", choices=["household","small_community","community"])
    ap.add_argument("--water-table", type=float, dest="wt")
    ap.add_argument("--land", type=float)
    ap.add_argument("--soil", choices=["good","poor"], default="good")
    ap.add_argument("--skill", choices=["low","medium","high"])
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--piped-water", action="store_true", dest="piped")
    ap.add_argument("--offsite-service", action="store_true", dest="offsite")
    a = ap.parse_args()
    if a.preset:
        site = PRESETS[a.preset]
    else:
        if not a.setting: sys.exit("give --preset or at least --setting")
        site = dict(setting=a.setting, water_table_depth_m=a.wt, land_m2_per_capita=a.land,
                    soil_permeability=a.soil, offsite_service=a.offsite, skilled_labour=a.skill or "low",
                    power=a.power, piped_water=a.piped, desc="(custom site)")
    run(data, site)

if __name__ == "__main__":
    main()
