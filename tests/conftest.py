import sys, os
# put engine/ first so `import select` resolves to our engine/select.py, not stdlib
ENGINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
sys.path.insert(0, ENGINE)
