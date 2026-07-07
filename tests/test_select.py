"""The capability query — site constraints disqualify the right technologies."""
import os, importlib.util
# `select` is a stdlib C built-in that shadows our module name — load ours by path.
_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "select.py")
_spec = importlib.util.spec_from_file_location("owselect_test", _p)
sel = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sel)

DATA = sel.load()
T = {t["id"]: t for t in DATA["technologies"]}

def dq(tid, **overrides):
    """Disqualifier categories for tech tid at a site that is permissive by default."""
    site = dict(setting="community", water_table_depth_m=None, land_m2_per_capita=None,
                soil_permeability="good", offsite_service=True, skilled_labour="high",
                power=True, piped_water=True)
    site.update(overrides)
    return [cat for cat, _why in sel.disqualifiers(T[tid], site)]

def test_high_water_table_kills_deep_pit_not_uddt():
    assert "water_table" in dq("S.2", setting="household", water_table_depth_m=1.0)
    assert "water_table" not in dq("U.2", setting="household", water_table_depth_m=1.0)

def test_no_piped_water_kills_pour_flush():
    assert "water" in dq("U.4", setting="household", piped_water=False)
    assert "water" not in dq("U.2", setting="household", piped_water=False)  # dry toilet fine

def test_no_power_kills_activated_sludge():
    assert "power" in dq("T.12", power=False)

def test_low_skill_kills_uasb():
    assert "skilled_labour" in dq("T.11", skilled_labour="low")

def test_scarce_land_kills_wetland():
    assert "land" in dq("T.8", land_m2_per_capita=0.5)
    assert "land" not in dq("T.8", land_m2_per_capita=12)

def test_poor_soil_kills_soak_pit():
    assert "soil" in dq("D.7", setting="household", soil_permeability="poor")

def test_no_offsite_service_kills_conveyance():
    assert "offsite_service" in dq("C.3", offsite_service=False)

def test_reuse_land_required_for_land_application():
    assert "reuse_land" in dq("D.2", land_m2_per_capita=0.5)
    assert "reuse_land" not in dq("D.2", land_m2_per_capita=12)

def test_scale_household_tech_fits_community_but_not_vice_versa():
    assert "scale" not in dq("U.2", setting="community")   # UDDT (household) OK in a community
    assert "scale" in dq("T.5", setting="household")       # WSP (community) too big for a household

def test_presets_all_produce_some_fit():
    for name, site in sel.PRESETS.items():
        fits = [t["id"] for t in DATA["technologies"] if not sel.disqualifiers(t, site)]
        assert fits, f"{name}: nothing fits"

def test_unknown_water_table_fails_closed_for_deep_pit():
    # round-3 fix: a safety tool must NOT clear a deep pit at a site whose water table is unknown
    assert "water_table_unknown" in dq("S.2")                          # default site: water table None
    assert "water_table_unknown" not in dq("S.2", water_table_depth_m=8.0)  # provided & deep enough

def test_unknown_land_fails_closed_for_reuse_endpoint():
    assert "reuse_land_unknown" in dq("D.2")                           # default site: land None
    assert "reuse_land_unknown" not in dq("D.2", land_m2_per_capita=12)
