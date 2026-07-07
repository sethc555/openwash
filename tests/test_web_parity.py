"""The browser guardrail (docs/guardrail.js) must return IDENTICAL verdicts to the Python
engine, and its embedded constants must equal the YAML — or it's an unattested second
source of truth. Skipped only where Node.js is absent."""
import os, shutil, importlib.util
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("ow_parity", os.path.join(_HERE, "parity.py"))
parity = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(parity)


@pytest.mark.skipif(shutil.which("node") is None and shutil.which("nodejs") is None,
                    reason="Node.js not installed — cannot check browser/Python parity")
def test_browser_guardrail_matches_python_engine():
    ok, report = parity.check()
    assert ok, report
