"""Cost anchors — sourced, context-complete, and tech ids that actually exist."""
import os, yaml, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COSTS = yaml.safe_load(open(os.path.join(ROOT, "data/costs.yaml")))
SOURCES = yaml.safe_load(open(os.path.join(ROOT, "data/sources.yaml")))["sources"]
TECH_IDS = {t["id"] for t in yaml.safe_load(open(os.path.join(ROOT, "data/technologies.yaml")))["technologies"]}

def test_cost_sources_resolve():
    for c in COSTS["technology_costs"] + COSTS["system_costs"]:
        assert c["source"]["ref"] in SOURCES

def test_cost_tech_ids_exist():
    for c in COSTS["technology_costs"]:
        assert c["tech"] in TECH_IDS, c["tech"]
    for s in COSTS["system_costs"]:
        for t in s.get("techs_like", []):
            assert t in TECH_IDS, t

def test_no_context_free_costs():
    # every cost figure must carry place + year + currency/unit (never a naked cost)
    for c in COSTS["technology_costs"]:
        assert c.get("place") and c["value"].get("year") and c["value"].get("currency")
    for s in COSTS["system_costs"]:
        assert s.get("place") and s["capital"].get("year") and s["capital"].get("unit")

def test_costs_engine_formats():
    spec = importlib.util.spec_from_file_location("owcosts", os.path.join(ROOT, "engine", "costs.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert m.amt({"amount": 348, "currency": "EUR", "year": 2007}) == "348 EUR (2007)"
    assert "106–211" in m.amt({"amount_range": [106, 211], "currency": "EUR", "year": 2006})
