"""The guardrail must say UNSAFE when it should and never launder an unsafe design as safe."""
import os, importlib.util

ENG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
spec = importlib.util.spec_from_file_location("safe_reuse", os.path.join(ENG, "safe_reuse.py"))
SR = importlib.util.module_from_spec(spec); spec.loader.exec_module(SR)

def status(material, treatment, params, route):
    return SR.assess(material, treatment, params, route)["status"]

def test_untreated_is_always_unsafe():
    assert status("sludge", "none", None, "soil_only") == "UNSAFE"
    assert status("faeces", "none", None, "food_processed") == "UNSAFE"

def test_malawi_case_short_passive_storage_is_unsafe():
    # 6-month passive storage at 25C — the deployed failure mode; rule needs ~365 d
    assert status("faeces", "storage", (25, 180), "food_raw") == "UNSAFE"

def test_long_enough_storage_passes_the_rule():
    assert status("faeces", "storage", (25, 400), "soil_only") == "SAFE_SCREEN"

def test_ammonia_needs_enough_time():
    # params: (temp, days, pH, measured total ammoniacal-N in mM)
    assert status("sludge", "ammonia", (30, 5, 9.1, 200), "soil_only") == "UNSAFE"     # too short
    assert status("sludge", "ammonia", (30, 60, 9.1, 200), "soil_only") == "SAFE_SCREEN"

def test_ammonia_low_ph_is_unknown_not_safe():
    assert status("sludge", "ammonia", (30, 60, 7.0, 200), "soil_only") == "UNKNOWN"

def test_ammonia_without_measured_dose_is_unknown_not_safe():
    # the false-safe fix: high pH alone (e.g. lime/ash, ~zero nitrogen) must NOT read SAFE.
    assert status("sludge", "ammonia", (30, 60, 11.0, None), "soil_only") == "UNKNOWN"

def test_storage_sides_with_the_conservative_model_at_the_rule_floor():
    # 365 d at 30°C clears the WHO rule band, but the die-off model still leaves >1 egg/g
    # (residual ~1.17): the conservative signal must govern → UNSAFE, not SAFE.
    assert status("faeces", "storage", (30, 365), "soil_only") == "UNSAFE"

def test_cold_urine_storage_is_unknown_not_safe():
    # WHO urine-storage times assume ~20°C; a 4°C store on a raw-crop route must not read SAFE.
    assert SR.assess("urine", "storage", (4, 6), "food_raw")["status"] == "UNKNOWN"

def test_unrecognised_route_fails_closed_not_safe():
    # round-5 fix: an unknown reuse route must not fall through to the most-permissive verdict.
    assert SR.assess("urine", "storage", (20, 0), "raw")["status"] == "UNKNOWN"          # misspelled food_raw
    assert SR.assess("sludge", "storage", (25, 400), "outer_space")["status"] == "UNKNOWN"

def test_thermal_time_temperature_law():
    assert status("sludge", "thermal", (52, 3), "non_food") == "UNSAFE"           # EPA needs ~6.9 d
    assert status("sludge", "thermal", (55, 10), "non_food") == "SAFE_SCREEN"

def test_mesophilic_is_unknown_not_a_guess():
    # 45C sits in the 40-50C gap with no robust curve — must NOT be certified either way
    assert status("sludge", "thermal", (45, 20), "non_food") == "UNKNOWN"

def test_urine_route_stringency():
    assert SR.assess("urine", "storage", (20, 0.5), "food_raw")["status"] == "UNSAFE"      # needs 6 mo
    assert SR.assess("urine", "storage", (20, 6), "food_raw")["status"] == "SAFE_SCREEN"
    assert SR.assess("urine", "storage", (20, 0), "non_food")["status"] == "SAFE_SCREEN"   # own/non-food ok

def test_verdict_carries_a_reason_and_screen_honesty():
    v = SR.assess("sludge", "none", None, "soil_only")
    assert v["reason"] and v["fix"]

def test_verification_plan_has_three_tiers_ending_in_the_hard_helminth_test():
    plan = SR.verification_plan("sludge", "ammonia", (30, 60, 9.1), "soil_only")
    assert len(plan) == 3                                   # process, E. coli, helminth
    text = " ".join(w for step in plan for w in step)
    assert "E. coli" in text and "1000" in text            # bacterial indicator + threshold
    assert "Ascaris" in text and "viable" in text.lower()  # the binding, hard endpoint
    # the honest limit must be stated: low E. coli does NOT clear helminths
    assert any("does NOT clear helminths" in step[3] for step in plan)

def test_urine_verification_plan_is_urine_specific():
    # round-3 fix: urine is dispatched as treatment="storage"; its process tier must still be
    # the urine-specific "no faecal contact" step, not the generic thermometer text.
    plan = SR.verification_plan("urine", "storage", (20, 6), "food_raw")
    assert "faecal contact" in " ".join(plan[0]).lower()

def test_process_tier_matches_the_treatment():
    assert "pH" in " ".join(SR.verification_plan("sludge", "ammonia", (30, 60, 9.1), "soil_only")[0])
    assert "centre" in " ".join(SR.verification_plan("sludge", "thermal", (55, 10), "non_food")[0]).lower()
