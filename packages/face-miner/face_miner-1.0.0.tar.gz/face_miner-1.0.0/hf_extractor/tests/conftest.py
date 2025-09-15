# Ensure the repository root is on sys.path so `import hf_extractor` works
import os, sys, types

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Optional: if huggingface_hub isn't installed in your test env, stub it
try:
    import huggingface_hub  # noqa: F401
except ModuleNotFoundError:
    hub_pkg = types.ModuleType("huggingface_hub")
    hub_hf_api = types.ModuleType("huggingface_hub.hf_api")
    hub_utils = types.ModuleType("huggingface_hub.utils")

    class _DummyHfApi:  # will be monkeypatched by tests anyway
        def __init__(self, *a, **k): pass

    class _DummyErr(Exception):
        pass

    hub_hf_api.HfApi = _DummyHfApi
    hub_utils.HfHubHTTPError = _DummyErr

    sys.modules["huggingface_hub"] = hub_pkg
    sys.modules["huggingface_hub.hf_api"] = hub_hf_api
    sys.modules["huggingface_hub.utils"] = hub_utils
