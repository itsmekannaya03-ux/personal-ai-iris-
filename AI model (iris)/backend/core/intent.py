"""
Intent shim — re-exports the canonical IntentDetector from the brain core.

The single source of truth lives in `AI model (iris)/core/intent.py`;
this module bridges the backend's import path so both can share it.
Loaded under a unique module name to avoid circular import collisions.
"""

import os
import importlib.util
import sys

_BRAIN_INTENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core", "intent.py"))
_UNIQUE_NAME = "iris_brain_core_intent"

if _UNIQUE_NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_UNIQUE_NAME, _BRAIN_INTENT)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_UNIQUE_NAME] = _module
    _spec.loader.exec_module(_module)
else:
    _module = sys.modules[_UNIQUE_NAME]

IntentDetector = _module.IntentDetector

__all__ = ["IntentDetector"]
