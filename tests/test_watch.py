"""Reuse-hazard watch layer — sourced, product-keyed, and it actually flags the gaps."""
import os, yaml, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = yaml.safe_load(open(os.path.join(ROOT, "data/watch.yaml")))
SOURCES = yaml.safe_load(open(os.path.join(ROOT, "data/sources.yaml")))["sources"]
HAZARDS = WATCH["hazards"]

def test_every_hazard_is_sourced_with_evidence():
    for h in HAZARDS:
        assert h.get("evidence"), f"{h['id']}: no evidence"
        for e in h["evidence"]:
            assert e["source"]["ref"] in SOURCES, f"{h['id']}: unknown source {e['source']['ref']}"

def test_hazard_fields_present():
    ids = set()
    for h in HAZARDS:
        assert h["id"] not in ids; ids.add(h["id"])
        for k in ("name", "applies_to_products", "why_the_safety_table_misses_it", "disposition"):
            assert h.get(k), f"{h['id']} missing {k}"

def test_the_three_adversarial_gaps_are_covered():
    ids = {h["id"] for h in HAZARDS}
    assert {"amr_args", "micropollutants", "heavy_metals"} <= ids

def test_products_are_real_reuse_products():
    real = {"sludge", "biosolids", "compost", "pit_humus", "effluent", "urine", "stored_urine", "dried_faeces"}
    for h in HAZARDS:
        for p in h["applies_to_products"]:
            assert p in real, f"{h['id']}: '{p}' is not a known reuse product"

def test_watch_engine_maps_products():
    spec = importlib.util.spec_from_file_location("owwatch", os.path.join(ROOT, "engine", "watch.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    watch, sources = m.load()
    # effluent reuse must surface AMR, micropollutants, and heavy metals
    names = {h["id"] for h in m.hazards_for(watch, "effluent")}
    assert {"amr_args", "micropollutants", "heavy_metals"} <= names
    # a product with no flagged hazard returns empty
    assert m.hazards_for(watch, "biogas") == []
