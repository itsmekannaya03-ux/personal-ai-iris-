"""
IRIS AI - Workspace Root Launcher
Forwards execution to the IRIS engine in 'AI model (iris)/run_iris.py'.
"""

import os
import sys

_SUBDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI model (iris)")

if os.path.isdir(_SUBDIR):
    os.chdir(_SUBDIR)
    sys.path.insert(0, _SUBDIR)
    run_file = os.path.join(_SUBDIR, "run_iris.py")
    with open(run_file, "r", encoding="utf-8") as f:
        code = compile(f.read(), run_file, "exec")
        exec(code, {"__name__": "__main__", "__file__": run_file})
else:
    print(f"[ERROR] Could not find IRIS directory at {_SUBDIR}")
    sys.exit(1)

