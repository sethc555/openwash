"""The system chainer — completeness, constraint propagation, ranking, regressions."""
import io, contextlib
import systems

DATA = systems.sel.load()
BYID = {t["id"]: t for t in DATA["technologies"]}
PRESETS = systems.sel.PRESETS
FAECES_BEARING = {"excreta", "faeces", "blackwater", "brownwater"}

def _is_reuse_endpoint(i):
    t = BYID[i]
    return (t["group"] == "D" and i not in systems.DISPOSAL
            and ("biomass" in t.get("outputs", []) or t.get("reuse_products")))

def test_every_reuse_endpoint_gets_a_pathogen_flag():
    # round-3 regression: NO reuse endpoint may reach a reuse output without the pathogen
    # safety flag — the biosolids (D.5) and in-situ biomass (arborloo D.1) gaps that the
    # chemical watch layer covered but the pathogen screen silently dropped.
    for name, site in PRESETS.items():
        fit = {t["id"] for t in DATA["technologies"] if not systems.sel.disqualifiers(t, site)}
        interfaces = [t["id"] for t in DATA["technologies"] if t["group"] == "U" and t["id"] in fit
                      and FAECES_BEARING & set(t.get("outputs", []))]
        for u in interfaces:
            for s in systems.enumerate_systems(DATA, site, u):
                reuse_nodes = [i for i in set(s) if _is_reuse_endpoint(i)]
                if not reuse_nodes:
                    continue
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    systems.render(DATA, site, s, 1, systems.score(s, BYID))
                lines = buf.getvalue().splitlines()
                for i in reuse_nodes:
                    assert any(i in ln and "⚑" in ln for ln in lines), \
                        f"{name}: reuse endpoint {i} in {sorted(set(s))} has NO pathogen flag"

def test_flood_plain_uddt_completes_without_any_deep_pit():
    syslist = systems.enumerate_systems(DATA, PRESETS["flood_plain"], "U.2")
    assert syslist, "UDDT should complete on a flood plain"
    for s in syslist:
        assert "S.2" not in s and "S.3" not in s  # water table disqualifies deep pits end-to-end

def test_arborloo_is_reuse_complete_score_one():
    # regression: in-situ biomass (a tree) counts as reuse, not disposal
    syslist = systems.enumerate_systems(DATA, PRESETS["rural_ample_land"], "U.1")
    arbor = [s for s in syslist if set(s) == {"U.1", "D.1"}]
    assert arbor, "U.1 → Arborloo should be a valid system"
    assert systems.score(arbor[0], BYID) == 1

def test_biomass_only_reuse_carries_a_chemical_watch_flag():
    # round-4 fix: a biomass-only reuse endpoint (arborloo D.1) must not escape the chemical watch
    # the way it once escaped the pathogen flag.
    s = ["U.1", "D.1"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        systems.render(DATA, PRESETS["rural_ample_land"], s, 1, systems.score(s, BYID))
    assert "non-pathogen watch" in buf.getvalue()

def test_reuse_scores_better_than_disposal():
    reuse = systems.score(["U.1", "S.5", "D.4"], BYID)     # → compost application
    disposal = systems.score(["U.1", "S.2", "D.12"], BYID)  # → landfill
    assert reuse < disposal

def test_offsite_service_unlocks_conveyance():
    with_svc = systems.enumerate_systems(DATA, PRESETS["dense_urban"], "U.4")
    assert any(any(t.startswith("C.") for t in s) for s in with_svc)
    no_svc = dict(PRESETS["dense_urban"]); no_svc["offsite_service"] = False
    without = systems.enumerate_systems(DATA, no_svc, "U.4")
    assert without, "must still complete via onsite disposal"
    assert all(not any(t.startswith("C.") for t in s) for s in without)

def test_every_enumerated_system_is_product_complete():
    # a returned system's non-terminal outputs must each be consumed within the system
    site = PRESETS["rural_ample_land"]
    syslist = systems.enumerate_systems(DATA, site, "U.1")[:50]
    for s in syslist:
        consumed = set()
        for tid in s:
            consumed |= set(BYID[tid].get("inputs", []))
        for tid in s:
            t = BYID[tid]
            if t["group"] == "D" or t.get("outputs") in ([], None):
                continue
            for prod in t.get("outputs", []):
                if prod == "biomass":
                    continue
                assert prod in consumed, f"system {s}: product {prod} from {tid} unresolved"

def test_faeces_root_rule_excludes_urinal():
    FAECES = {"excreta", "faeces", "blackwater", "brownwater"}
    assert not (FAECES & set(BYID["U.3"]["outputs"]))   # urinal is urine-only → not a system root
    assert FAECES & set(BYID["U.2"]["outputs"])          # UDDT manages faeces → valid root
