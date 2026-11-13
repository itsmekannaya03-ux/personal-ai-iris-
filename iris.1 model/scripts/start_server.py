import subprocess, os, sys

user_profile = os.environ.get("USERPROFILE", "C:\\Users\\User")
base = sys.executable
wd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
venv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".venv"))
log = os.path.join(os.environ.get("TEMP", os.path.join(user_profile, "AppData", "Local", "Temp")), "iris5743.log")

env = dict(os.environ)
env["VIRTUAL_ENV"] = venv
env["PYTHONPATH"] = os.path.join(venv, "Lib", "site-packages")

p = subprocess.Popen(
    [base, "-u", "run_server.py"],
    cwd=wd,
    env=env,
    stdin=subprocess.DEVNULL,
    stdout=open(log, "a", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
)
print(p.pid)