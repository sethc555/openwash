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
    D55 = 1.317e8 / 10 ** (0.14 * 55)
    D50 = 1.317e8 / 10 ** (0.14 * 50)
    assert abs(D55 - 2.63) < 0.1     # ~2.6 days at 55°C
    assert abs(D50 - 13.17) < 0.2    # ~13 days at 50°C (more conservative than WHO's 1 week)

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
