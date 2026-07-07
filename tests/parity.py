#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Browser ↔ Python parity check for the OpenWASH guardrail.

Runs a large battery of reuse designs through BOTH the Python engine
(engine/safe_reuse.py) and the browser port (docs/guardrail.js, via Node) and
requires IDENTICAL verdicts — plus checks that the JS-embedded constants equal
data/dieoff_kinetics.yaml. If they diverge, the browser tool is an unattested
second source of truth; this script (and the `web_parity` claim) then fail.

Exit 0 iff every case matches and constants agree. Requires Node.js.
"""
import json, os, shutil, subprocess, importlib.util, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENG = os.path.join(ROOT, "engine")
GUARDRAIL_JS = os.path.join(ROOT, "docs", "guardrail.js")


def _load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def build_cases():
    """A broad grid touching every branch + boundary of every screen."""
    cases = []
    for mat in ("faeces", "sludge", "mixed", "compost"):
        for r in ("food_raw", "food_processed", "non_food", "soil_only", "raw", "bogus"):
            cases.append([mat, "none", None, r])
    for t in (2, 4, 10, 15, 20, 25, 30, 34, 35, 40, 50):
        for d in (0, 30, 90, 180, 365, 400, 548, 730, 1000):
            for r in ("food_raw", "soil_only"):
                cases.append(["faeces", "storage", [t, d], r])
    for t in (15, 20, 25, 30, 34, 40):
        for d in (0, 5, 15, 30, 60, 120, 400):
            for ph in (6, 7, 8.5, 9, 9.1, 10, 11):
                for dose in (None, 0, 10, 50, 130, 200, 250, 300, 440):
                    cases.append(["sludge", "ammonia", [t, d, ph, dose], "soil_only"])
    for t in (30, 40, 45, 49, 50, 52, 55, 57, 60, 70):
        for d in (0, 1, 2, 3, 7, 14, 30):
            cases.append(["sludge", "thermal", [t, d], "non_food"])
    for t in (4, 10, 15, 18, 20, 25, 30):
        for m in (0, 0.5, 1, 3, 6, 12):
            for r in ("food_raw", "food_processed", "non_food", "soil_only", "raw"):
                cases.append(["urine", "storage", [t, m], r])
    cases.append(["sludge", "xyz", [25, 100], "soil_only"])
    return cases


def _node():
    return shutil.which("node") or shutil.which("nodejs")


def _check_constants(jsdata):
    """The JS-embedded constants must equal the YAML (guards against silent drift)."""
    import yaml
    asc = yaml.safe_load(open(os.path.join(ROOT, "data/dieoff_kinetics.yaml")))["organisms"]["ascaris"]
    am, tm = asc["ammonia_model"], asc["thermal_model"]
    want = {
        "storage_meta_k": asc["meta_analysis"]["k_log10_per_day"],
        "ammonia.threshold_mM": am["threshold_mM"],
        "ammonia.nh3_saturation_mM": am["nh3_saturation_mM"],
        "ammonia.k_coeff": am["k_coeff_log10_per_day_per_mM"],
        "ammonia.Q10": am["Q10"],
        "thermal.min_temp_C": tm["min_temp_C"],
        "thermal.const_ge_7pct": tm["solids_ge_7pct_constant"],
        "dose.bulk_density": am["dosing"]["bulk_density_kg_per_L"]["value"],
        "dose.measured_1pct": am["dosing"]["measured_total_am_mM"][0]["total_am_mM"],
        "dose.measured_2pct": am["dosing"]["measured_total_am_mM"][1]["total_am_mM"],
    }
    got = {
        "storage_meta_k": jsdata["storage_meta_k"],
        "ammonia.threshold_mM": jsdata["ammonia"]["threshold_mM"],
        "ammonia.nh3_saturation_mM": jsdata["ammonia"]["nh3_saturation_mM"],
        "ammonia.k_coeff": jsdata["ammonia"]["k_coeff"],
        "ammonia.Q10": jsdata["ammonia"]["Q10"],
        "thermal.min_temp_C": jsdata["thermal"]["min_temp_C"],
        "thermal.const_ge_7pct": jsdata["thermal"]["const_ge_7pct"],
        "dose.bulk_density": jsdata["dose"]["bulk_density_kg_per_L"],
        "dose.measured_1pct": jsdata["dose"]["measured"][0]["total_mM"],
        "dose.measured_2pct": jsdata["dose"]["measured"][1]["total_mM"],
    }
    errs = []
    for k in want:
        if float(want[k]) != float(got[k]):
            errs.append(f"constant {k}: JS {got[k]} != YAML {want[k]}")
    # the storage-rule bands must match too
    rule_yaml = [[b["temp_C"], b["time_days"]] for b in asc["storage_rule"]]
    rule_js = [[b["temp"], b["need"]] for b in jsdata["storage_rule"]]
    if rule_yaml != rule_js:
        errs.append(f"storage_rule bands: JS {rule_js} != YAML {rule_yaml}")
    return errs


def check():
    """Return (ok: bool, report: str)."""
    node = _node()
    if not node:
        return False, "Node.js not found — cannot verify browser↔Python parity. Install Node to run this check."
    SR = _load("safe_reuse_parity", os.path.join(ENG, "safe_reuse.py"))
    cases = build_cases()
    py = [SR.assess(c[0], c[1], c[2], c[3])["status"] for c in cases]

    runner = os.path.join(HERE, "parity_runner.js")
    proc = subprocess.run([node, runner], input=json.dumps(cases),
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return False, f"node runner failed:\n{proc.stderr}"
    js = json.loads(proc.stdout)

    mism = [(cases[i], py[i], js[i]) for i in range(len(cases)) if py[i] != js[i]]

    dproc = subprocess.run(
        [node, "-e", "process.stdout.write(JSON.stringify(require(process.argv[1]).DATA))", GUARDRAIL_JS],
        capture_output=True, text=True, timeout=30)
    const_errs = _check_constants(json.loads(dproc.stdout)) if dproc.returncode == 0 else \
        [f"could not read JS constants: {dproc.stderr}"]

    # dose-planner parity — kill-time AND container→kg estimates must match (temps × container volumes)
    temps = list(range(4, 46, 2))
    vols = [None, 20, 30, 120, 200, 1000]
    py_dose = [[[o["cure_days"], o.get("urea_kg")] for o in SR.dose_plan(t, v)["options"]]
               for t in temps for v in vols]
    dscript = ("var G=require(process.argv[1]);var jobs=JSON.parse(process.argv[2]);"
               "process.stdout.write(JSON.stringify(jobs.map(function(j){"
               "return G.dose_plan(j[0], j[1]).options.map(function(o){"
               "return [o.cure_days, (o.urea_kg==null?null:o.urea_kg)];});})));")
    jobs = [[t, v] for t in temps for v in vols]
    dp = subprocess.run([node, "-e", dscript, GUARDRAIL_JS, json.dumps(jobs)],
                        capture_output=True, text=True, timeout=30)
    js_dose = json.loads(dp.stdout) if dp.returncode == 0 else None
    def _close(a, b):
        if a is None or b is None: return a == b
        return abs(a - b) <= 0.011
    dose_ok = js_dose is not None and len(js_dose) == len(py_dose) and all(
        _close(py_dose[i][k][0], js_dose[i][k][0]) and _close(py_dose[i][k][1], js_dose[i][k][1])
        for i in range(len(py_dose)) for k in range(len(py_dose[i])))

    ok = not mism and not const_errs and dose_ok
    lines = [f"parity: {len(cases) - len(mism)}/{len(cases)} verdicts identical (Python ↔ browser JS)"]
    for c, p, j in mism[:20]:
        lines.append(f"  MISMATCH {c}: python={p} js={j}")
    if len(mism) > 20:
        lines.append(f"  … and {len(mism) - 20} more")
    for e in const_errs:
        lines.append(f"  {e}")
    lines.append(f"dose planner: {len(temps)}×{len(vols)} temp×container dose cases identical"
                 if dose_ok else f"  DOSE MISMATCH: python={py_dose} js={js_dose}")
    if ok:
        lines.append("constants: JS matches data/dieoff_kinetics.yaml ✓")
    return ok, "\n".join(lines)


if __name__ == "__main__":
    ok, report = check()
    print(report)
    sys.exit(0 if ok else 1)
