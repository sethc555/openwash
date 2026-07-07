"""The corroboration engine — tier is computed from lineage, catching over-claims."""
import openwash

SOURCES, DATA = openwash.load()
BYID = {c["id"]: c for c in DATA["claims"]}

def test_overclaim_downgraded_to_single_lineage():
    # WHO Vol4+Vol2+SSP all cite the 6/7-log target, but share one lineage
    c = BYID["logred_unrestricted_leaf"]
    assert openwash.computed_tier(c["value"], SOURCES) == "single_lineage"

def test_genuine_multi_lineage_kept():
    # Sphere + EAWAG are independent → genuinely multi-corroborated
    c = BYID["siting_setback_from_water"]
    assert openwash.computed_tier(c["value"], SOURCES) == "multi_corroborated"

def test_single_sourced_stays_single():
    c = BYID["design_infection_risk_rotavirus"]
    assert openwash.computed_tier(c["value"], SOURCES) == "single_sourced"

def test_restates_does_not_add_independence():
    # a source marked restates:X folds onto X's lineage
    c = BYID["logred_unrestricted_leaf"]
    lineages = openwash.independent_lineages(c["value"], SOURCES)
    assert lineages == {"who_2006_reuse"}

def test_pure_echoes_do_not_manufacture_multi_corroboration():
    # round-3 fix: two restatements of DIFFERENT lineages, with NO primary source, must not
    # read as multi_corroborated (the latent restates-fold inflation path).
    vb = {"sources": [{"ref": "a", "restates": "A"}, {"ref": "b", "restates": "B"}]}
    assert openwash.computed_tier(vb, SOURCES) != "multi_corroborated"
    assert openwash.independent_lineages(vb, SOURCES) == set()

def test_validate_reports_no_errors():
    errs, _warns = openwash.validate(SOURCES, DATA)
    assert errs == []

def test_validate_flags_the_overclaims():
    _errs, warns = openwash.validate(SOURCES, DATA)
    assert any("OVER-CLAIM" in w for w in warns)
