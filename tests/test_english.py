"""In inglese: i moduli partono, menu, Impostazioni, novità e prompt sono tradotti
(in un processo a parte con HOPPY_LANG=en: qui i test girano in italiano)."""
import os, pathlib, subprocess, sys
import _setup  # noqa: F401

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

CODE = r'''
import os, sys, pathlib, tempfile
sys.path.insert(0, sys.argv[1])
from hoppy import config, i18n
T = pathlib.Path(tempfile.mkdtemp())
config.DATA_DIR, config.CONFIG_PATH, config.STARTUP_DIR = T, T / "config.json", T / "startup"
from hoppy import pet, settings, inline, popup, changelog, work
print("LANG", i18n.LANG)
print("LABEL", config.BY_KEY["character"].label)
print("NEWS", changelog.text(changelog.CHANGES[:1]).splitlines()[0])
print("PERSONA", "English" in pet.PERSONA or "english" in pet.PERSONA)
print("POWER", pet.POWER_NAMES["web"])
'''
env = {**os.environ, "HOPPY_LANG": "en", "PYTHONIOENCODING": "utf-8"}
r = subprocess.run([sys.executable, "-c", CODE, str(pathlib.Path(__file__).resolve().parents[1])],
                   capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
out = dict(line.split(" ", 1) for line in r.stdout.splitlines() if " " in line)
check("i moduli partono in inglese" + (": " + r.stderr[-300:] if r.returncode else ""),
      r.returncode == 0 and out.get("LANG") == "en")
check("Impostazioni in inglese", out.get("LABEL") == "Character")
check("novità in inglese", out.get("NEWS", "").startswith("**Version "))
check("Claude risponde in inglese", out.get("PERSONA") == "True")
check("nomi dei poteri tradotti", out.get("POWER") not in (None, "Ragnatela"))
print("TUTTO OK" if all(ok) else "FALLITO")
