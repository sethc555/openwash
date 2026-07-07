"""The PWA (offline/installable) + i18n scaffold must stay well-formed:
a valid manifest, the service worker + icons present, and every translation complete
(en/fr have exactly the same keys — a missing key would show English silently)."""
import json, os, re, shutil, subprocess
import pytest

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def test_pwa_assets_present_and_manifest_valid():
    for f in ("manifest.webmanifest", "sw.js", "i18n.js", "guardrail.js",
              "icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        assert os.path.exists(os.path.join(DOCS, f)), f"missing docs/{f}"
    m = json.load(open(os.path.join(DOCS, "manifest.webmanifest")))
    for k in ("name", "short_name", "start_url", "display", "icons", "theme_color"):
        assert m.get(k), f"manifest missing {k}"
    assert any(i["sizes"] == "512x512" for i in m["icons"])
    # the service worker must cache the app shell (so it works offline)
    sw = open(os.path.join(DOCS, "sw.js")).read()
    for asset in ("index.html", "guardrail.js", "i18n.js"):
        assert asset in sw, f"service worker does not cache {asset}"


def test_service_worker_registered_and_manifest_linked():
    html = open(os.path.join(DOCS, "index.html")).read()
    assert 'rel="manifest"' in html and "serviceWorker" in html and "sw.js" in html


@pytest.mark.skipif(shutil.which("node") is None and shutil.which("nodejs") is None,
                    reason="Node.js not installed")
def test_i18n_languages_have_identical_keys():
    node = shutil.which("node") or shutil.which("nodejs")
    out = subprocess.run(
        [node, "-e",
         "var I=require(process.argv[1]);"
         "process.stdout.write(JSON.stringify(Object.keys(I).map(function(l){return [l,Object.keys(I[l]).sort()];})));",
         os.path.join(DOCS, "i18n.js")],
        capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    langs = dict(json.loads(out.stdout))
    assert "en" in langs and "fr" in langs
    base = set(langs["en"])
    assert base, "no i18n keys found"
    for lang, keys in langs.items():
        assert set(keys) == base, f"i18n '{lang}' keys differ from en: " \
            f"missing={sorted(base - set(keys))} extra={sorted(set(keys) - base)}"


def test_every_data_i18n_key_exists_in_the_table():
    html = open(os.path.join(DOCS, "index.html")).read()
    used = set(re.findall(r'data-i18n="([^"]+)"', html))
    i18n = open(os.path.join(DOCS, "i18n.js")).read()
    for key in used:
        assert (key + ":") in i18n or ("'" + key + "'") in i18n or ('"' + key + '"') in i18n, \
            f"data-i18n='{key}' used in index.html but not defined in i18n.js"
