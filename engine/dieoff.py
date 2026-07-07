#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OpenWASH constraint engine — pathogen die-off screening.

Answers: "given a storage/treatment regime (temperature, time, matrix), is the
predicted pathogen reduction sufficient?" — the safety-critical question that
separates a working ecosan design from a disease vector.

Model: first-order (log-linear) inactivation, LR(t) = k(T) * t, with k=1/T90.
This is an OPTIMISTIC approximation (real Ascaris die-off has tails and is
non-monotonic in the field). So the engine is a SCREEN, not a certifier:
  - it rules OUT clearly-insufficient designs (necessary condition), and
  - where the optimistic model disagrees with the conservative WHO categorical
    rule or field evidence, it sides with the conservative call and says so.

Usage:
  python engine/dieoff.py predict --organism ascaris --matrix faeces --days 180 --temp 25
  python engine/dieoff.py storage --temp 25 --days 180 --initial 10   # Ascaris storage screen
  python engine/dieoff.py table --temp 25 --days 180
"""
import os, sys, argparse, math, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load():
    with open(os.path.join(ROOT, "data/dieoff_kinetics.yaml")) as f:
        return yaml.safe_load(f)

# ---- kinetics --------------------------------------------------------------
SOLID = {"faeces", "soil", "sludge", "excreta", "compost", "dried_faeces"}
LIQUID = {"greywater", "greywater_sediment", "river_water", "river_water_sediment",
          "liquid_waste", "effluent", "urine", "wastewater", "blackwater", "brownwater"}
def mclass(m): return "solid" if m in SOLID else "liquid" if m in LIQUID else "other"

def k_at(org, temp, matrix):
    """Return (k in log10/day, basis string, confidence flag).

    Temperature-specific rates (WHO Table 3.8) are matrix-specific and mostly
    from LIQUID matrices; they are only applied when the query matrix is the
    same class. Otherwise we fall back to the matrix-correct T90 (Table 3.5) at
    reference temperature, with no temperature scaling — and say so."""
    model = org.get("temp_model", "none")
    rates = [r for r in (org.get("decay_rates") or []) if mclass(r.get("matrix","")) == mclass(matrix)]
    if model in ("interpolate", "single_point") and rates:
        pts = sorted([(r["temp_C"], r["k"]) for r in rates])
        if len(pts) == 1:
            return pts[0][1], f"single point @ {pts[0][0]}°C", "LOW (no temperature model — 1 datapoint)"
        def logk_line(p0, p1, T):
            (t0, k0), (t1, k1) = p0, p1
            f = (T - t0) / (t1 - t0)
            return math.log10(k0) + f * (math.log10(k1) - math.log10(k0))
        lo = [p for p in pts if p[0] <= temp]
        hi = [p for p in pts if p[0] >= temp]
        if lo and hi:
            p0, p1 = max(lo), min(hi)
            if p0 == p1:                                  # exact measured point
                return p0[1], f"measured @ {p0[0]}°C", "OK (measured point)"
            return 10**logk_line(p0, p1, temp), f"interpolated {p0[0]}–{p1[0]}°C", "OK (within measured range)"
        # temp outside measured range -> extrapolate from the nearest two points
        p0, p1 = (pts[0], pts[1]) if temp < pts[0][0] else (pts[-2], pts[-1])
        return max(10**logk_line(p0, p1, temp), 1e-6), \
               f"EXTRAPOLATED beyond {pts[0][0]}–{pts[-1][0]}°C", "LOW (extrapolation)"
    # no temp model -> prefer the current meta-analytic decay (conservative) for solids,
    # else fall back to the reference T90
    meta = org.get("meta_analysis")
    if meta and meta.get("k_log10_per_day") and mclass(matrix) == "solid":
        return meta["k_log10_per_day"], f"meta-analytic k (Musaazi 2023, N={meta.get('n_studies','?')})", \
               "OK (current meta-analysis; temperature-independent < 50 °C)"
    t90 = (org.get("t90_days", {}).get(matrix) or {}).get("mean")
    if t90:
        return 1.0 / t90, f"1/T90 @ ref {org.get('ref_temp_C')}°C (no temp scaling)", \
               "LOW (no temperature model — reference T90 only)"
    return None, "no data", "NONE"

def log_reduction(org, temp, days, matrix):
    k, basis, flag = k_at(org, temp, matrix)
    if k is None: return None, basis, flag
    return k * days, basis, flag

# ---- Ascaris categorical rule (the conservative cross-check) ---------------
def ascaris_rule(org, temp, days):
    for band in org.get("storage_rule", []):
        lo, hi = band["temp_C"]
        if lo <= temp <= hi:
            need_lo, need_hi = band["time_days"]
            ok = days >= need_lo
            return {"band": f"{lo}–{hi}°C", "need_days": band["time_days"],
                    "effect": band["effect"], "meets": ok}
    return None

def epa_thermal_days(data, temp, solids="high"):
    """US EPA 40 CFR 503 required hold (days) at `temp` for Class-A helminth reduction.
    The SINGLE engine home of the time–temperature constant — the guardrail
    (safe_reuse.screen_thermal) and the anchor test both call this, so the constant
    can't be silently changed without moving the tested value."""
    tm = data["organisms"]["ascaris"]["thermal_model"]
    const = tm["solids_lt_7pct_constant"] if solids == "low" else tm["solids_ge_7pct_constant"]
    return const / 10 ** (0.14 * temp)

# ---- commands --------------------------------------------------------------
def cmd_predict(data, organism, matrix, days, temp, initial):
    org = data["organisms"].get(organism)
    if not org: sys.exit(f"unknown organism '{organism}' (have: {', '.join(data['organisms'])})")
    lr, basis, flag = log_reduction(org, temp, days, matrix)
    print(f"DIE-OFF PREDICTION — {org['name']}")
    print(f"  regime: {matrix}, {days} days @ {temp}°C")
    if lr is None: print(f"  no kinetic data for {matrix}"); return
    print(f"  k basis: {basis}   [confidence: {flag}]")
    print(f"  predicted log10 reduction: {lr:.2f} log")
    if initial is not None:
        resid = initial * 10**(-lr)
        print(f"  {initial} egg|CFU/g  ->  {resid:.3g} egg|CFU/g residual")
    if org.get("field_caveat"): print(f"  ⚠ field caveat: {org['field_caveat']}")
    print(f"  ⚠ first-order model is OPTIMISTIC — a screen, not a safety certificate.")

def cmd_storage(data, temp, days, initial):
    """The killer demo: screen a passive Ascaris storage design."""
    org = data["organisms"]["ascaris"]
    target = 1.0   # <=1 viable egg/g total solids
    print(f"STORAGE SAFETY SCREEN (binding pathogen: Ascaris)")
    print(f"  design: passive storage of faeces, {days} days @ {temp}°C, initial {initial} eggs/g")
    print(f"  target: <= {target:.0f} viable helminth egg / g TS  (WHO 2006 Vol 4)\n")

    # (a) first-order model
    lr, basis, flag = log_reduction(org, temp, days, "faeces")
    resid = initial * 10**(-lr)
    model_pass = resid <= target
    print(f"  [1] first-order model  : {lr:.2f} log -> {resid:.3g} eggs/g  =>  "
          f"{'pass' if model_pass else 'FAIL'}   ({basis}; confidence {flag})")

    # (b) WHO categorical rule (conservative)
    rule = ascaris_rule(org, temp, days)
    if rule:
        rule_pass = rule["meets"]
        print(f"  [2] WHO categorical    : {temp}°C band {rule['band']} needs "
              f"{rule['need_days'][0]}–{rule['need_days'][1]} days; you have {days}  =>  "
              f"{'pass' if rule_pass else 'FAIL'}")
        print(f"                           (effect at rule time: {rule['effect']})")
    else:
        rule_pass = None
        print(f"  [2] WHO categorical    : no band covers {temp}°C")

    # (c) field evidence
    print(f"  [3] field evidence     : deployed passive storage under-performs the model — "
          f"Kumwenda 2019 found 12-month sludge still >1 egg/g in 12% of units, hookworm 5–10/g.")

    # verdict: side with the conservative signal
    print()
    if rule_pass is False:
        print(f"  VERDICT: ✗ UNSAFE (screened out). The WHO categorical rule requires "
              f">= {rule['need_days'][0]} days at {temp}°C; the optimistic first-order model "
              f"{'agrees' if not model_pass else 'DISAGREES (says pass) but is not trusted here'}.")
        need = rule['need_days'][0]
        print(f"           minimum by rule: ~{need} days ({need/30:.0f} months).")
    elif model_pass and rule_pass:
        print(f"  VERDICT: ⚠ NOT SCREENED OUT — model and rule both pass, but this is a "
              f"necessary-not-sufficient screen. Verify by measurement (<=1 egg/g); the field "
              f"caveat still applies. Do NOT treat as certified safe.")
    elif rule_pass is None and model_pass:
        # no WHO categorical band covers this temperature, but the model passes — advisory only
        print(f"  VERDICT: ⚠ NOT SCREENED OUT by the model ({resid:.3g} ≤ {target} eggs/g), but NO WHO "
              f"categorical rule covers {temp}°C, so this is ADVISORY — verify by measurement.")
    else:
        # model residual exceeds the target (with or without a covering rule) → conservative UNSAFE
        print(f"  VERDICT: ✗ UNSAFE (screened out) — first-order model residual {resid:.3g} > {target} eggs/g.")

# ---- ammonia-enhanced Ascaris inactivation (Nordin 2009 / Pecson 2007) -----
def nh3_fraction(pH, temp_C):
    """Uncharged-NH3 fraction of total ammoniacal-N (Emerson/Nordin pKa)."""
    T = temp_C + 273.15
    pKa = 2729.92 / T + 0.09018
    return 1.0 / (1.0 + 10 ** (pKa - pH)), pKa

def k_ammonia(am, temp_C, nh3_mM):
    """Ascaris inactivation rate (log10/day) from uncharged NH3; 0 below threshold.
    The linear-in-NH3 rate is CLAMPED at the calibration ceiling (Nordin/Fidjeland saturate) so it
    cannot over-predict inactivation at high doses — the single guard for every caller (CLI + guardrail)."""
    if nh3_mM < am["threshold_mM"]:
        return 0.0
    nh3 = min(nh3_mM, am.get("nh3_saturation_mM", 250.0))
    return am["k_coeff_log10_per_day_per_mM"] * nh3 * am["Q10"] ** ((temp_C - 24) / 10.0)

def cmd_ammonia(data, temp, days, initial, nh3, ph, total_am, validate):
    am = data["organisms"]["ascaris"]["ammonia_model"]
    if validate:
        print("AMMONIA MODEL VALIDATION — calibrated model vs sourced anchor points (t99 = 2-log):\n")
        print(f"  {'lab':>10} {'temp°C':>6} {'NH3 mM':>7} {'model t99':>11} {'sourced':>10}")
        print("  " + "-"*54)
        for a in am["anchors_t99_days"]:
            k = k_ammonia(am, a["temp_C"], a["nh3_mM"])
            mt = 2.0 / k if k > 0 else float("inf")
            print(f"  {a.get('lab','?'):>10} {a['temp_C']:>6} {a['nh3_mM']:>7} {mt:>10.0f}d {str(a['t99_days'])+'d':>10}   {a.get('note','')}")
        print("\n  Coeff/Q10 are FIT to the Nordin 2009 points (an interpolation of sourced data,"
              "\n  not an independent claim). Fidjeland 2015 rows are an INDEPENDENT cross-check —"
              "\n  its own t99 values fall on the model. A smooth-shoulder curve was tested & rejected"
              "\n  by Fidjeland (over-conservative); t99 is used as the robustness threshold instead.")
        return
    print(f"AMMONIA / ALKALINE STORAGE SCREEN (binding pathogen: Ascaris)")
    print(f"  design: {temp}°C, {days} days, initial {initial} eggs/g")
    if nh3 is not None:
        nh3_aq, basis = nh3, f"NH3(aq) = {nh3} mM (given)"
    elif ph is not None and total_am is not None:
        f, pKa = nh3_fraction(ph, temp)
        nh3_aq = f * total_am
        basis = f"pH {ph}, total NH-N {total_am} mM → pKa {pKa:.2f}, NH3 fraction {f:.3f} → NH3(aq) {nh3_aq:.0f} mM"
    else:
        print("  give --nh3, OR --ph and --total-ammonia"); return
    print(f"  {basis}")
    k = k_ammonia(am, temp, nh3_aq)
    if k == 0:
        print(f"  NH3(aq) {nh3_aq:.0f} mM < {am['threshold_mM']} mM threshold → ammonia effect negligible;")
        print(f"  fall back to plain-storage screen:  dieoff.py storage --temp {temp} --days {int(days)}")
        return
    lr = k * days; resid = initial * 10 ** (-lr); t99 = 2.0 / k
    print(f"  k = {k:.3f} log10/day  (t99 ≈ {t99:.0f} d)   [Nordin 2009 calibrated ammonia model]")
    print(f"  → {lr:.2f} log reduction over {days:.0f} d → {resid:.3g} eggs/g residual")
    ok = resid <= 1.0
    if ok:
        print(f"  VERDICT: ⚠ NOT SCREENED OUT — residual {resid:.3g} ≤ 1 egg/g. Lab-calibrated model; "
              f"verify by measurement. Ammonia route is FAR faster than plain storage.")
        if days < t99:
            print(f"  ⚠ LAG CAUTION: {days:.0f} d < t99 ({t99:.0f} d). Inactivation has a lag phase "
                  f"(Fidjeland 2015); sub-t99 exposures rely on the optimistic early phase. "
                  f"For a robust pass, run ≥ {t99:.0f} d.")
    else:
        need = initial  # eggs/g to clear to 1
        import math as _m
        need_days = _m.log10(initial) / k if initial > 1 else 0
        print(f"  VERDICT: ✗ UNSAFE (screened out) — residual {resid:.3g} > 1 egg/g; "
              f"need ~{need_days:.0f} d at this NH3/temperature.")

def cmd_thermal(data, temp, days, solids):
    tm = data["organisms"]["ascaris"]["thermal_model"]
    const = tm["solids_lt_7pct_constant"] if solids == "low" else tm["solids_ge_7pct_constant"]
    print(f"THERMAL TREATMENT SCREEN (Ascaris / Class-A pathogen reduction)")
    print(f"  design: sustain {temp}°C for {days} days (solids {'<7%' if solids=='low' else '>=7%'})")
    adv = tm.get("mesophilic_advisory", {})
    lo, hi = adv.get("temp_range_C", [40, 50])
    if temp < lo:
        print(f"  {temp}°C < {lo}°C — below any thermal regime; this is not a thermal treatment.")
        print(f"  use instead:  dieoff.py storage  (ambient)   or   dieoff.py ammonia  (alkaline/urea)")
        return
    if temp < tm["min_temp_C"]:
        # mesophilic advisory band (evidence too thin for a pass/fail screen)
        print(f"  MESOPHILIC ADVISORY ({lo}–{hi}°C) — not a pass/fail screen:")
        print(f"  Ascaris inactivation IS achievable here given EXTENDED time (Harroff 2019; Naidoo 2020,"
              f" 40–55°C in water/sludge) — the ≥{tm['min_temp_C']}°C floor is a conservative screen boundary,"
              f" not a biological limit.")
        print(f"  But no robust time-temperature curve exists at these temps (Espinosa 2020: few helminth"
              f" studies; temperature weakly predictive of decay < ~50°C), so no number is invented.")
        print(f"  → verify by measurement, or use the ammonia route (dieoff.py ammonia) which IS quantified here.")
        return
    D = epa_thermal_days(data, temp, solids)
    print(f"  EPA 40 CFR 503 required hold: D = {const:.3g} / 10^(0.14·{temp}) = {D:.2f} days ({D*24:.1f} h)")
    if days >= D:
        print(f"  VERDICT: ✓ MEETS the time–temperature requirement ({days:.2f} d ≥ {D:.2f} d).")
    else:
        print(f"  VERDICT: ✗ UNSAFE (screened out) — {days:.2f} d < required {D:.2f} d at {temp}°C.")
    xc = ", ".join(f"{p['temp_C']}°C→{p['epa_days']} d ({p['who']})" for p in tm.get("cross_check", []))
    print(f"  cross-check (in kinetics data): {xc}.")
    print(f"  regulatory whole-mass requirement incl. viable helminth ova; assumes UNIFORM temperature "
          f"(field piles have cold spots — Manga 2020).")
    if tm.get("contested"):
        print(f"  ⚠ CONTESTED ({tm['contested']}): the >=50°C floor is deliberately conservative; "
              f"Harroff 2019 shows mesophilic (<45°C) treatment inactivates Ascaris given time, so "
              f"this screen rejects some valid low-temperature designs. See data/limitations.yaml.")

def cmd_table(data, temp, days):
    print(f"LOG-REDUCTION TABLE — {days} days @ {temp}°C (matrix=faeces)\n")
    print(f"  {'organism':<18}{'log red':>9}   basis / confidence")
    print("  " + "-"*70)
    for oid, org in data["organisms"].items():
        lr, basis, flag = log_reduction(org, temp, days, "faeces")
        if lr is None:
            print(f"  {oid:<18}{'n/a':>9}   {basis}")
        else:
            mark = " (BINDING)" if org.get("binding") else ""
            print(f"  {oid:<18}{lr:>8.2f}   {basis} [{flag.split('(')[0].strip()}]{mark}")

def main():
    data = load()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--organism", required=True); p.add_argument("--matrix", default="faeces")
    p.add_argument("--days", type=float, required=True); p.add_argument("--temp", type=float, required=True)
    p.add_argument("--initial", type=float)
    s = sub.add_parser("storage")
    s.add_argument("--temp", type=float, required=True); s.add_argument("--days", type=float, required=True)
    s.add_argument("--initial", type=float, default=10.0)
    t = sub.add_parser("table")
    t.add_argument("--temp", type=float, required=True); t.add_argument("--days", type=float, required=True)
    m = sub.add_parser("ammonia")
    m.add_argument("--temp", type=float, default=25); m.add_argument("--days", type=float, default=90)
    m.add_argument("--initial", type=float, default=10.0)
    m.add_argument("--nh3", type=float, help="uncharged NH3(aq) in mM (direct)")
    m.add_argument("--ph", type=float); m.add_argument("--total-ammonia", type=float, dest="total_am",
                   help="total ammoniacal-N in mM (with --ph)")
    m.add_argument("--validate", action="store_true")
    h = sub.add_parser("thermal")
    h.add_argument("--temp", type=float, required=True); h.add_argument("--days", type=float, required=True)
    h.add_argument("--solids", choices=["high","low"], default="high")
    a = ap.parse_args()
    if a.cmd == "predict": cmd_predict(data, a.organism, a.matrix, a.days, a.temp, a.initial)
    if a.cmd == "storage": cmd_storage(data, a.temp, a.days, a.initial)
    if a.cmd == "table": cmd_table(data, a.temp, a.days)
    if a.cmd == "ammonia": cmd_ammonia(data, a.temp, a.days, a.initial, a.nh3, a.ph, a.total_am, a.validate)
    if a.cmd == "thermal": cmd_thermal(data, a.temp, a.days, a.solids)

if __name__ == "__main__":
    main()
