#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH — the reuse-safety GUARDRAIL, made usable.

The point of the whole project, at the point of decision: a field operator, health
worker, or small-NGO engineer describes what they have and what they want to do with
it, and gets an honest answer — SAFE-BY-SCREEN / UNSAFE / NOT ENOUGH EVIDENCE — with
the binding pathogen, the specific fix, and two limits it never hides:
  • it is a SCREEN, not a certificate — verify by measurement before reuse;
  • it says NOTHING about chemical hazards (AMR, heavy metals, micropollutants — the
    watch layer). Passing the pathogen screen does not clear those.

It says UNSAFE when it should, and "not enough evidence" when the evidence is thin —
the opposite of a confident hallucination. All logic and numbers come from the sourced
substrate (engine/dieoff.py + data/*.yaml); nothing here is invented.

Run:
  python engine/safe_reuse.py            # answer a few plain questions
  python engine/safe_reuse.py --demo     # worked examples (a safe and an unsafe case)
"""
import os, sys, math, importlib.util

ENG = os.path.dirname(os.path.abspath(__file__))
def _load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
D = _load("owdieoff", os.path.join(ENG, "dieoff.py"))
DATA = D.load()
ASC = DATA["organisms"]["ascaris"]
AM  = ASC["ammonia_model"]

TARGET_EGG = 1.0                                   # <=1 viable helminth egg / g TS (WHO 2006 Vol 4)
REP_TOTAL_AMMONIACAL_MM = 200.0                    # representative hydrolysed-urine/urea dose (mM total N)
ECOLI_LIMIT = 1000                                 # <1000 CFU/g TS (WHO 2006 Vol 4)  — verify_faeces_ecoli
EGG_LIMIT_CHILD = 0.1                              # tighten to <=0.1 egg/L where children <15 exposed

# ---- verdict helpers -------------------------------------------------------
def _v(status, reason, fix=None, detail=None):
    return {"status": status, "reason": reason, "fix": fix, "detail": detail}

def screen_storage(temp, days, material_label, initial_eggs=40):
    """Passive storage of solids — conservative Ascaris screen (rule + model + field)."""
    rule = D.ascaris_rule(ASC, temp, days)
    lr, basis, flag = D.log_reduction(ASC, temp, days, "faeces")
    resid = initial_eggs * 10 ** (-lr) if lr is not None else None
    if rule is None:
        return _v("UNKNOWN", f"No sourced storage rule covers {temp}°C for {material_label}.",
                  "Bring the material into a covered regime with a known rule (raise temperature, "
                  "or add urine/urea/ash to sanitise by ammonia), then re-check.")
    if not rule["meets"]:
        need = rule["need_days"][0]
        return _v("UNSAFE",
                  f"Passive storage at {temp}°C needs ≥ {need} days (~{need/30:.0f} months) to reach "
                  f"≤1 viable egg/g; you have {days}.",
                  f"Store ≥ {need} days at this temperature — OR add urine/urea/ash (pH ≥9) to sanitise "
                  f"far faster, OR heat-compost ≥50°C. Deployed passive storage has under-performed in "
                  f"the field (Kumwenda 2019, Malawi), so treat this bound as a floor.",
                  f"model: {lr:.1f} log → {resid:.2g} eggs/g ({flag}); rule band {rule['band']}.")
    # Rule says it meets — but SIDE WITH THE CONSERVATIVE SIGNAL: if the first-order
    # die-off model still leaves > the target at this exact point (typical at the rule-band
    # floor), do not bless it. The two signals must AGREE for a SAFE screen.
    if resid is not None and resid > TARGET_EGG:
        return _v("UNSAFE",
                  f"Storage {days} d at {temp}°C meets the WHO categorical rule band, but the first-order "
                  f"die-off model still leaves ~{resid:.2g} viable eggs/g (target ≤{TARGET_EGG:.0f}); the "
                  f"conservative signal governs.",
                  f"Hold longer — the model clears ≤1 egg/g only past the rule-band floor — or add "
                  f"urine/urea/ash (pH ≥9) to sanitise by ammonia, or heat-compost ≥50°C; then re-check.",
                  f"model: {lr:.1f} log → {resid:.2g} eggs/g ({flag}); rule band {rule['band']}.")
    return _v("SAFE_SCREEN",
              f"Storage {days} d at {temp}°C meets both the WHO categorical rule (needs "
              f"{rule['need_days'][0]}–{rule['need_days'][1]} d) and the first-order model for ≤1 viable egg/g.",
              None,
              f"model: {lr:.1f} log → {resid:.2g} eggs/g ({flag}); rule band {rule['band']}.")

def screen_ammonia(temp, days, pH, total_mM, material_label, initial_eggs=40):
    """Urine/urea/ash amendment — ammonia (uncharged NH3) inactivation.

    Requires a MEASURED total ammoniacal-N dose (mM). pH alone cannot stand in for it:
    lime or ash can push pH ≥9 while adding little or no nitrogen, so a pH-only screen
    would falsely clear a batch with essentially no ammonia. Without a dose → UNKNOWN.
    """
    if total_mM is None:
        return _v("UNKNOWN",
                  "Ammonia inactivation is driven by the actual ammonia DOSE, which pH alone cannot "
                  "confirm — ash/lime can raise pH while adding little or no nitrogen.",
                  "Measure total ammoniacal-N (NH3+NH4⁺) with an ammonia test strip/kit (mg/L ÷ 14 ≈ mM) "
                  "and re-check with that value. Guide: hydrolysed urine / urea dosing reaches ~150–300 mM; "
                  "lime-only reads near zero.")
    if pH < 8.5:
        return _v("UNKNOWN", f"pH {pH} is too low for meaningful ammonia sanitisation.",
                  "Add more urine/urea (adds nitrogen AND raises pH) to reach pH ≥9 (hydrolysed urine "
                  "self-rises to ~9), then re-check.")
    f, _ = D.nh3_fraction(pH, min(temp, 34.0))
    nh3 = min(f * total_mM, 250.0)                 # calibration-bounded (Nordin/Fidjeland saturate)
    k = D.k_ammonia(AM, min(temp, 34.0), nh3)
    if k <= 0:
        return _v("UNKNOWN", f"At your measured {total_mM:.0f} mM total ammoniacal-N and pH {pH}, uncharged "
                  f"NH3 (~{nh3:.0f} mM) is below the ~{AM['threshold_mM']} mM threshold where ammonia "
                  "inactivation works.",
                  "Increase the urine/urea dose or pH; warmer material also raises the active fraction.")
    need_log = math.log10(initial_eggs / TARGET_EGG)
    cure = max(need_log / k, 2.0 / k)              # lag/robustness guard
    if days >= cure:
        return _v("SAFE_SCREEN",
                  f"At your measured {total_mM:.0f} mM dose, pH {pH}, {temp}°C, ammonia clears Ascaris in "
                  f"~{cure:.0f} d; you held {days}.",
                  None,
                  f"NH3(aq) ≈ {nh3:.0f} mM, k ≈ {k:.3f} log/d (from your {total_mM:.0f} mM total ammoniacal-N).")
    return _v("UNSAFE",
              f"At your measured {total_mM:.0f} mM dose, pH {pH}, {temp}°C, ammonia needs ~{cure:.0f} d to "
              f"clear Ascaris; you held {days}.",
              f"Hold the batch ≥ {cure:.0f} days (sealed, to retain ammonia), or add more urine/urea to "
              f"raise the dose, or warm it.",
              f"NH3(aq) ≈ {nh3:.0f} mM, k ≈ {k:.3f} log/d (from your {total_mM:.0f} mM total ammoniacal-N).")

def screen_thermal(temp, days):
    """Thermophilic composting / heat — US EPA 40 CFR 503 time–temperature law (≥50°C)."""
    if temp < 50:
        return _v("UNKNOWN", f"{temp}°C is below the ≥50°C thermal regime; there is no robust "
                  "mesophilic (40–50°C) helminth time–temperature curve in the evidence.",
                  "Either reach and hold ≥50°C uniformly (turned pile), or treat it as ambient storage "
                  "(store for the full categorical time) / ammonia amendment instead.")
    req = D.epa_thermal_days(DATA, temp)           # EPA required days at T (shared engine fn)
    if days >= req:
        return _v("SAFE_SCREEN",
                  f"Holding ≥{temp}°C for {days} d meets the EPA time–temperature requirement (~{req:.1f} d).",
                  None, "Requires the WHOLE mass to reach temperature — turn the pile; edges lag.")
    return _v("UNSAFE",
              f"At {temp}°C the EPA law requires ~{req:.1f} d of hold; you have {days}.",
              f"Hold ≥{req:.1f} days at {temp}°C (or hotter for less time), turning to heat the whole mass.")

# ---- routing ---------------------------------------------------------------
ROUTE_NOTE = {
    "food_raw": "Strictest route: crops eaten raw. Full sanitisation AND withholding/washing barriers.",
    "food_processed": "Cooked/processed crops: sanitisation required; cooking is a strong extra barrier.",
    "non_food": "Non-food (fodder, trees, fibre): sanitisation still required — handler contact risk.",
    "soil_only": "Soil amendment, no crop: still sanitise — pathogens persist and people touch soil.",
}

def assess(material, treatment, params, route):
    """Return a verdict dict for solids/faecal reuse. Urine handled separately."""
    if material == "urine":
        return assess_urine(treatment, params, route)
    ml = {"faeces": "faeces", "sludge": "faecal sludge", "mixed": "settled blackwater solids",
          "compost": "compost"}.get(material, material)
    if treatment == "none":
        return _v("UNSAFE", f"Untreated {ml} reused directly is a disease vector — raw excreta carries "
                  "the full pathogen load (Ascaris eggs survive months).",
                  "Sanitise before ANY reuse: ammonia (urine/urea/ash, pH ≥9), heat ≥50°C, or long storage.")
    if treatment == "storage": return screen_storage(*params, ml)
    if treatment == "ammonia": return screen_ammonia(*params, ml)
    if treatment == "thermal": return screen_thermal(*params)
    return _v("UNKNOWN", f"Unrecognised treatment '{treatment}'.", None)

def assess_urine(treatment, params, route):
    """Urine reuse — WHO storage rule (pathogen risk is low; storage clears the little there is)."""
    temp, months = params
    need = 6 if route == "food_raw" else (1 if route == "food_processed" else 0)
    label = {6: "≥6 months (all crops)", 1: "≥1 month (processed crops only)",
             0: "own-household / non-food use (no storage needed)"}[need]
    # WHO urine-storage times are anchored to ~20°C; colder storage is materially slower and
    # these times are not validated there. Don't credit a cold store as if it were 20°C.
    if need > 0 and temp < 20:
        return _v("UNKNOWN",
                  f"WHO urine-storage times ({label}) assume ~20°C; at {temp}°C inactivation is slower and "
                  f"these times are not validated.",
                  "Store at ~20°C or warmer for the required months, or extend the time and verify by "
                  "measurement, or restrict to processed / non-food / own-household use.")
    if months >= need:
        return _v("SAFE_SCREEN", f"Urine stored {months} mo at ~{temp}°C meets WHO guidance for this route "
                  f"({label}).", None, "Urine's pathogen risk is low; storage clears it. Keep it OUT of "
                  "contact with faeces (that would reintroduce the full load).")
    return _v("UNSAFE", f"This route needs {label}; you stored {months} mo.",
              f"Store urine ≥{need} months at ~20°C before using on this crop class, or use it only on "
              "processed/non-food crops, or restrict to the producing household.")

# ---- the verification plan (what the paired TEST KIT must measure) ----------
# The screen checks the DESIGN; a kit checks the DEPLOYED BATCH. Mirrors WHO multi-barrier /
# HACCP: verify the critical control points cheaply & routinely, confirm the hard endpoint
# (viable helminth eggs) periodically — because no cheap fast field helminth-viability test exists.
def verification_plan(material, treatment, params, route):
    child = route == "food_raw"
    steps = []
    # Tier 1 — PROCESS / critical-control-point check (cheapest; EVERY batch)
    if treatment == "storage":
        temp, days = params[0], params[1]
        steps.append(("① PROCESS  (every batch, ~$)",
            f"the batch actually sat ≥ the required time at ≥{temp}°C",
            "log start/end dates + a min–max thermometer (or $10 datalogger)",
            "a wall calendar + a cheap thermometer — near-free"))
    elif treatment == "ammonia":
        pH = params[2]
        steps.append(("① PROCESS  (every batch, ~$)",
            f"pH stayed ≥{pH} and it was held sealed for the required days at temperature",
            "pH strips + ammonia (NH3/NH4) test strips + thermometer + a batch log",
            "pH & ammonia strips ~$0.10 each, thermometer once"))
    elif treatment == "thermal":
        temp = params[0]
        steps.append(("① PROCESS  (every batch, ~$)",
            f"the WHOLE mass reached ≥{temp}°C for the required days (centre lags — probe it)",
            "a probe/datalogger left in the pile CENTRE, plus turning records",
            "one $10–30 logger, reused"))
    elif material == "urine":
        steps.append(("① PROCESS  (every batch, ~$)",
            "urine was stored the required months with NO faecal contact",
            "a dated storage log + separation check",
            "near-free"))
    # Tier 2 — BACTERIAL INDICATOR (cheap, direct; every batch or spot-check)
    steps.append(("② E. COLI  (per batch / spot, ~$3–5)",
        f"E. coli < {ECOLI_LIMIT} CFU/g  — catches gross treatment failure",
        "field MPN test (Aquagenx Compartment Bag Test) or 3M Petrifilm; incubate ~24–48 h",
        "~$3–5/test, NO lab needed — but LOW E. coli does NOT clear helminths (they're hardier)"))
    # Tier 3 — HELMINTH CONFIRMATION (the hard, binding one; PERIODIC audit)
    lim = f"viable Ascaris eggs < {TARGET_EGG:.0f} /g TS" + (f" (tighten toward {EGG_LIMIT_CHILD}/L if children are exposed)" if child else "")
    steps.append(("③ HELMINTH  (periodic audit — the hard, BINDING test)",
        lim,
        "sieve → sediment/flotation → count under a microscope (a $50 USB/Foldscope works), "
        "THEN incubate 3–4 weeks to see if eggs are VIABLE (dead eggs don't count)",
        "the real gap: slow (weeks) + skilled. Do it per-N-batches or via a partner lab, "
        "not every batch — Tier ① + ② are your routine, Tier ③ is the backstop audit"))
    return steps

# ---- presentation ----------------------------------------------------------
BADGE = {"SAFE_SCREEN": "✅ SAFE (by screen)", "UNSAFE": "✗ UNSAFE", "UNKNOWN": "❓ NOT ENOUGH EVIDENCE"}

def report(material, route, verdict, plan=None):
    print("\n" + "═"*66)
    print(f"  {BADGE[verdict['status']]}")
    print("═"*66)
    print(f"  reuse: {material} → {route.replace('_',' ')}  ({ROUTE_NOTE.get(route,'')})")
    print(f"\n  WHY: {verdict['reason']}")
    if verdict.get("fix"):    print(f"\n  DO THIS: {verdict['fix']}")
    if verdict.get("detail"): print(f"\n  (detail: {verdict['detail']})")
    if verdict["status"] == "SAFE_SCREEN" and plan:
        print("\n  ── NOW CONFIRM IT (pair with a test kit — the screen checks the DESIGN, the kit")
        print("     checks THIS batch). Three tiers, cheap-and-routine to hard-and-periodic: ──")
        for tier, what, how, note in plan:
            print(f"  {tier}")
            print(f"      measure: {what}")
            print(f"      how:     {how}")
            print(f"      note:    {note}")
    print("\n  ── always true ──")
    print("  • This is a SCREEN, not a safety certificate — the kit above is how you certify a batch.")
    print("  • It says NOTHING about chemical hazards — antimicrobial resistance, heavy metals,")
    print("    micropollutants (data/watch.yaml). Passing the pathogen screen does not clear those.")
    if verdict["status"] == "SAFE_SCREEN" and route == "food_raw":
        print("  • Raw-eaten crops are the strictest case — keep withholding periods + wash produce.")
    print()

# ---- input -----------------------------------------------------------------
def ask(prompt, options):
    keys = list(options)
    while True:
        print(prompt)
        for i, k in enumerate(keys, 1): print(f"    {i}) {options[k]}")
        r = input("  > ").strip()
        if r.isdigit() and 1 <= int(r) <= len(keys): return keys[int(r)-1]
        if r in options: return r
        print("  (pick a number)\n")

def num(prompt, cast=float):
    while True:
        try: return cast(input(f"  {prompt} ").strip())
        except ValueError: print("  (enter a number)")

def interactive():
    print("\nOpenWASH — is my reuse safe?  (a screen; verify by testing before reuse)\n")
    material = ask("What are you reusing?", {
        "faeces": "faeces / dried faeces", "sludge": "faecal sludge (pit/tank/CBS)",
        "mixed": "mixed blackwater solids (settled)", "urine": "urine (source-separated)",
        "compost": "compost / material you believe is already treated"})
    route = ask("\nWhere is it going?", {
        "food_raw": "crops eaten raw (salad, veg)", "food_processed": "crops that are cooked/processed",
        "non_food": "non-food crops (fodder, trees, fibre)", "soil_only": "soil amendment, no crop"})
    if material == "urine":
        treatment = "storage"
        params = (num("Storage temperature (°C)?"), num("Stored how many MONTHS?"))
        v = assess("urine", "storage", params, route)
    else:
        treatment = ask("\nHow is it being treated?", {
            "storage": "stored / aged (time + temperature)",
            "ammonia": "urine / urea / ash added (raises pH — ammonia)",
            "thermal": "heat / thermophilic composting (≥50°C)",
            "none": "not treated"})
        if treatment == "storage":
            params = (num("Temperature (°C)?"), num("Stored how many DAYS?", int))
        elif treatment == "ammonia":
            temp = num("Temperature (°C)?"); days = num("Held how many DAYS?", int); pH = num("Approx pH?")
            if ask("\nHave you MEASURED the ammonia dose (total ammoniacal-N)?", {
                    "yes": "yes — I have a strip/lab reading",
                    "no":  "no — only pH, or it's just lime/ash"}) == "yes":
                dose = num("Total ammoniacal-N in mM? (mg/L ÷ 14 ≈ mM)")
            else:
                dose = None                         # pH alone can't confirm a dose → UNKNOWN
            params = (temp, days, pH, dose)
        elif treatment == "thermal":
            params = (num("Temperature held (°C)?"), num("For how many DAYS?", int))
        else:
            params = None
        v = assess(material, treatment, params, route)
    plan = verification_plan(material, treatment, params, route) if v["status"] == "SAFE_SCREEN" else None
    report(material, route, v, plan)

def demo():
    cases = [
        ("A safe case (ammonia, MEASURED dose, held long enough)", "sludge", "ammonia", (30, 60, 9.1, 200), "soil_only"),
        ("Lime raised pH but ammonia dose not measured", "sludge", "ammonia", (30, 60, 11.0, None), "soil_only"),
        ("The Malawi failure (6-mo passive storage)", "faeces", "storage", (25, 180), "food_raw"),
        ("Untreated — never", "sludge", "none", None, "food_processed"),
        ("Hot compost, too short", "sludge", "thermal", (52, 3), "non_food"),
    ]
    for title, mat, tr, pr, route in cases:
        print(f"\n\n### {title}: {mat} + {tr} → {route}")
        v = assess(mat, tr, pr, route)
        plan = verification_plan(mat, tr, pr, route) if v["status"] == "SAFE_SCREEN" else None
        report(mat, route, v, plan)

if __name__ == "__main__":
    if "--demo" in sys.argv: demo()
    else:
        try: interactive()
        except (EOFError, KeyboardInterrupt): print("\n(cancelled)")
