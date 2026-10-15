"""Aggiornamenti: chiede a GitHub l'ultima release e, se rispondi di sì, installa la nuova versione.

L'installazione la fa un processo a parte (python -m hoppy.update TAG PID MODULI...), dopo che
mascotte, popup e inline sono usciti: su Windows i loro .exe restano bloccati finché girano.
Usa il pip dell'installazione corrente (anche quella di pipx) e lo zip della release su GitHub,
quindi non serve git. Poi riavvia i programmi che giravano e lascia l'esito in update.json."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from . import __version__
from . import config as pet_config

REPO = "Bazox96/hoppy"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ZIP_URL = "https://github.com/" + REPO + "/archive/refs/tags/{tag}.zip"
RESULT_PATH = pet_config.DATA_DIR / "update.json"
LOG_PATH = pet_config.DATA_DIR / "update.log"
NO_WINDOW = 0x08000000


def version_tuple(v):
    return tuple(int(n) for n in re.findall(r"\d+", v)[:3])


def is_newer(tag):
    return version_tuple(tag) > version_tuple(__version__)


def latest():
    """Il tag dell'ultima release, o None (niente rete, repo privato, limite di GitHub...)."""
    req = urllib.request.Request(LATEST_URL, headers={"Accept": "application/vnd.github+json",
                                                      "User-Agent": "hoppy/" + __version__})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            tag = json.loads(r.read(200_000)).get("tag_name")
    except (OSError, ValueError, AttributeError):
        return None
    return tag if isinstance(tag, str) and re.fullmatch(r"v?\d+(\.\d+){0,2}", tag) else None


def installed():
    """Installata come pacchetto (pipx o pip)? Dai sorgenti non si aggiorna da sola."""
    return "site-packages" in (p.lower() for p in Path(__file__).resolve().parts)


def start(tag, modules, env):
    """Avvia l'aggiornamento: parte quando questo processo (la mascotte) è uscito."""
    subprocess.Popen([str(pet_config._pythonw()), "-m", "hoppy.update", tag, str(os.getpid()),
                      *modules], cwd=str(Path.home()), env=env, creationflags=NO_WINDOW)


def take_result():
    """L'esito dell'ultimo aggiornamento ({"tag", "ok"}), una volta sola; None se non c'è."""
    try:
        res = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        RESULT_PATH.unlink()
    except (OSError, ValueError):
        return None
    return res if isinstance(res, dict) else None


def run(tag, pid, modules):
    pet_config.wait_for_exit(pid)
    deadline = time.time() + 30                       # popup e inline escono da soli
    while any(pet_config.is_running(m) for m in modules) and time.time() < deadline:
        time.sleep(0.5)
    python = Path(sys.executable).with_name("python.exe")
    cmd = [str(python), "-m", "pip", "install", "--upgrade", "--disable-pip-version-check",
           "--no-input", ZIP_URL.format(tag=tag)]
    ok, log = False, ""
    for attempt in range(3):                          # un .exe ancora bloccato: riprova
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=600, creationflags=NO_WINDOW)
            ok, log = r.returncode == 0, r.stdout + r.stderr
        except (OSError, subprocess.TimeoutExpired) as e:
            log = str(e)
        if ok:
            break
        time.sleep(5)
    pet_config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(" ".join(cmd) + "\n\n" + log, encoding="utf-8")
    RESULT_PATH.write_text(json.dumps({"tag": tag, "ok": ok}), encoding="utf-8")
    for m in modules:                                 # riparte chi girava (anche se è fallito:
        subprocess.Popen([str(pet_config._pythonw()), "-m", m],   # c'è ancora la versione vecchia)
                         cwd=str(Path.home()), creationflags=NO_WINDOW)


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]), sys.argv[3:])
