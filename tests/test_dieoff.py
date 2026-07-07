"""The die-off constraint engine — three sourced temperature/chemistry regimes."""
import dieoff

DATA = dieoff.load()
ASCARIS = DATA["organisms"]["ascaris"]
AM = ASCARIS["ammonia_model"]

def test_nh3_fraction_is_half_at_pka():
    # at pH == pKa the uncharged fraction is exactly 0.5
    pKa = 2729.92 / (25 + 273.15) + 0.09018
    f, pKa_reported = dieoff.nh3_fraction(pKa, 25)
    assert abs(f - 0.5) < 0.001
    assert abs(pKa_reported - pKa) < 1e-9

def test_ammonia_model_reproduces_nordin_anchors():
    for a in AM["anchors_t99_days"]:
        if a["lab"] != "nordin":
            continue
        k = dieoff.k_ammonia(AM, a["temp_C"], a["nh3_mM"])
        t99 = 2.0 / k
        assert abs(t99 - a["t99_days"]) / a["t99_days"] < 0.30, f"anchor {a} off: model {t99:.0f}d"

def test_ammonia_below_threshold_is_zero():
    assert dieoff.k_ammonia(AM, 25, 10) == 0.0  # 10 mM < 20 mM threshold

def test_ammonia_temperature_speeds_up():
    # 34°C should be markedly faster than 24°C at equal NH3
    assert dieoff.k_ammonia(AM, 34, 200) > 4 * dieoff.k_ammonia(AM, 24, 200)

def test_thermal_epa_matches_known_points():
    # Call the ENGINE (dieoff.epa_thermal_days), not a re-typed formula — so changing the
    # engine's constant would move this test. Check against the INDEPENDENT cross-check
    # points recorded (with sources) in the kinetics data (WHO/Haug), then the EPA-503 anchors.
    xc = {p["temp_C"]: p for p in ASCARIS["thermal_model"]["cross_check"]}
    for temp in (50, 57):
        got, published = dieoff.epa_thermal_days(DATA, temp), xc[temp]["epa_days"]
        assert abs(got - published) / published < 0.02, f"{temp}°C: engine {got:.2f} vs data {published}"
    assert abs(dieoff.epa_thermal_days(DATA, 55) - 2.63) < 0.05   # EPA-503 anchor ~2.6 d at 55°C
    # genuinely INDEPENDENT consistency checks (not the EPA formula restated):
    assert dieoff.epa_thermal_days(DATA, 50) > 7.0               # more conservative than WHO ">1 week" (7 d)
    assert 1.0 <= dieoff.epa_thermal_days(DATA, 57) <= 2.0       # within Haug 1993's 55–60°C → 1–2 d band

def test_kinetics_constants_are_sourced():
    # no naked numbers in the kinetics data either: every load-bearing constant/anchor carries a source.
    asc = ASCARIS
    assert asc["t90_days"]["faeces"]["source"]["ref"]
    am = asc["ammonia_model"]
    assert am["source"]["ref"] and all(a["source"]["ref"] for a in am["anchors_t99_days"])
    tm = asc["thermal_model"]
    assert tm["source"]["ref"] and all(p["source"]["ref"] for p in tm["cross_check"])

def test_faeces_query_uses_matrix_correct_t90_not_liquid_rate():
    # Salmonella's Table-3.8 rates are for greywater; a faeces query must fall back to T90
    k, basis, flag = dieoff.k_at(DATA["organisms"]["salmonella"], 25, "faeces")
    assert "T90" in basis

def test_liquid_query_uses_measured_rate():
    k, basis, flag = dieoff.k_at(DATA["organisms"]["salmonella"], 20, "greywater")
    assert "measured" in basis or "interpolated" in basis

def test_ascaris_storage_rule_screens_short_and_passes_long():
    assert dieoff.ascaris_rule(ASCARIS, 25, 180)["meets"] is False   # 6 mo < needed 12 mo
    assert dieoff.ascaris_rule(ASCARIS, 25, 400)["meets"] is True

def test_ascaris_uses_current_meta_analytic_decay():
    # refreshed: ambient Ascaris should use the meta-analytic k (Musaazi 2023), which is
    # MORE conservative (slower) than the old WHO T90=125d value
    k, basis, flag = dieoff.k_at(ASCARIS, 25, "faeces")
    assert "meta-analytic" in basis
    assert k < 1.0 / 125  # slower decay than WHO T90 → more persistent → conservative
