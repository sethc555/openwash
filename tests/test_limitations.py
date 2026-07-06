"""Limitations register — the substrate carries its own known weaknesses, sourced."""
import os, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMS = yaml.safe_load(open(os.path.join(ROOT, "data/limitations.yaml")))["limitations"]
SOURCES = yaml.safe_load(open(os.path.join(ROOT, "data/sources.yaml")))["sources"]

VALID_TYPES = {"contested", "scope_gap", "verifiability", "currency"}

def test_every_limitation_is_sourced():
    for lim in LIMS:
        assert lim.get("sources"), f"{lim['id']}: no source"
        for s in lim["sources"]:
            assert s["ref"] in SOURCES, f"{lim['id']}: unknown source {s['ref']}"

def test_limitation_fields_present():
    ids = set()
    for lim in LIMS:
        assert lim["id"] not in ids; ids.add(lim["id"])
        assert lim["type"] in VALID_TYPES, lim["id"]
        for k in ("affects", "finding", "disposition"):
            assert lim.get(k), f"{lim['id']} missing {k}"

def test_key_gaps_recorded():
    ids = {l["id"] for l in LIMS}
    # the adversarial pass must have logged these
    assert {"thermal_conservative_mesophilic", "amr_out_of_scope", "helminth_assay_verifiability"} <= ids

def test_thermal_model_points_at_its_limitation():
    kin = yaml.safe_load(open(os.path.join(ROOT, "data/dieoff_kinetics.yaml")))
    tm = kin["organisms"]["ascaris"]["thermal_model"]
    assert "thermal_conservative_mesophilic" in tm.get("contested", "")
