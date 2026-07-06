"""Data-integrity invariants — the rules the whole substrate depends on."""
import os, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(f): return yaml.safe_load(open(os.path.join(ROOT, "data", f)))

SOURCES = load("sources.yaml")["sources"]
SAFETY = load("reuse_safety.yaml")
KIN = load("dieoff_kinetics.yaml")
TECH = load("technologies.yaml")

def _refs(obj, out):
    if isinstance(obj, dict):
        if isinstance(obj.get("ref"), str): out.append(obj["ref"])
        for v in obj.values(): _refs(v, out)
    elif isinstance(obj, list):
        for v in obj: _refs(v, out)

def test_yaml_parses():
    assert SOURCES and SAFETY["claims"] and KIN["organisms"] and TECH["technologies"]

def test_every_source_ref_resolves():
    for doc in (SAFETY, KIN, TECH):
        out = []; _refs(doc, out)
        for r in out:
            assert r in SOURCES, f"unknown source ref: {r}"

def test_each_claim_has_exactly_one_shape():
    for c in SAFETY["claims"]:
        shapes = [k for k in ("value", "contested", "target_vs_field") if k in c]
        assert len(shapes) == 1, f"{c['id']}: {shapes}"

def test_no_naked_numbers():
    for c in SAFETY["claims"]:
        blocks = []
        if "value" in c: blocks.append(c["value"])
        if "contested" in c: blocks += c["contested"]["candidates"]
        if "target_vs_field" in c:
            blocks += [c["target_vs_field"]["design_target"], c["target_vs_field"]["field"]]
        for b in blocks:
            srcs = b.get("sources", [])
            assert srcs, f"{c['id']}: value block has no source"
            for s in srcs:
                assert s.get("page") or s.get("locator"), f"{c['id']}: source {s['ref']} lacks page/locator"

def test_contested_candidates_actually_differ():
    for c in SAFETY["claims"]:
        if "contested" in c:
            vals = [str(x["value"]) for x in c["contested"]["candidates"]]
            assert len(set(vals)) >= 2, f"{c['id']}: contested candidates identical"

def test_target_vs_field_has_both_halves():
    for c in SAFETY["claims"]:
        if "target_vs_field" in c:
            assert "design_target" in c["target_vs_field"] and "field" in c["target_vs_field"]

def test_technologies_wellformed():
    ids = set()
    for t in TECH["technologies"]:
        assert t["id"] not in ids, f"duplicate tech id {t['id']}"; ids.add(t["id"])
        assert t["group"] in ("U", "S", "C", "T", "D"), t["id"]
        for k in ("inputs", "outputs", "requires", "source"):
            assert k in t, f"{t['id']} missing {k}"

def test_full_compendium_catalog():
    assert len(TECH["technologies"]) >= 54  # the full distinct Compendium set

def test_ammonia_anchors_present_and_sourced():
    am = KIN["organisms"]["ascaris"]["ammonia_model"]
    assert len(am["anchors_t99_days"]) >= 4
    labs = {a["lab"] for a in am["anchors_t99_days"]}
    assert {"nordin", "fidjeland"} <= labs  # both the fit set and the cross-check set
