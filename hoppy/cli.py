"""Come Hoppy lancia `claude -p`: quale eseguibile, con quale profilo, e dove annota gli errori.

- command(): l'eseguibile. Se nel PATH c'è solo il claude.cmd di npm, salta cmd.exe (che
  rovina gli argomenti con a capo e virgolette) e lancia direttamente quello che il .cmd lancerebbe.
- env(): l'ambiente di un terminale nuovo, col profilo scelto in Impostazioni > Claude.
  Con --setting-sources "" Claude non legge settings.json: del profilo si passa solo il blocco
  "env" (es. le credenziali Bedrock di un account aziendale), niente hook né plugin.
- log() / friendly(): l'errore vero in %APPDATA%\\Hoppy\\errors.log, e una frase per il fumetto.
"""
import json
import os
import re
import shutil
import winreg
from datetime import datetime
from pathlib import Path

from . import config
from .i18n import T
from .knowledge import clean_env

LOG_MAX = 200_000            # oltre questa dimensione il registro riparte da metà


def command():
    """Il comando che avvia Claude Code, come lista (None se non c'è)."""
    native = Path.home() / ".local" / "bin" / "claude.exe"
    found = shutil.which("claude")
    if not found:
        return [str(native)] if native.exists() else None
    if Path(found).suffix.lower() not in (".cmd", ".bat"):
        return [found]
    if native.exists():
        return [str(native)]
    return _npm_target(Path(found)) or [found]


def _npm_target(cmd):
    """Dal claude.cmd di npm: il programma che lancia (claude.exe, o node + cli.js)."""
    try:
        text = cmd.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r'"%dp0%\\([^"%]+\.(?:js|exe))"', text, re.I)
    if not m:
        return None
    target = cmd.parent / m.group(1)
    if not target.exists():
        return None
    if target.suffix.lower() == ".exe":
        return [str(target)]
    node = cmd.parent / "node.exe"
    node = str(node) if node.exists() else shutil.which("node")
    return [node, str(target)] if node else None


def _user_env(names=None, prefix=None):
    """Variabili d'ambiente di Windows (utente, poi sistema) come le vede un terminale nuovo:
    la mascotte può essere stata avviata da un altro programma che le ha tolte o cambiate."""
    out = {}
    for hive, path in ((winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                       (winreg.HKEY_CURRENT_USER, "Environment")):
        try:
            with winreg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        k, v, _ = winreg.EnumValue(key, i)
                    except OSError:
                        break
                    i += 1
                    if isinstance(v, str) and ((names and k.upper() in names)
                                               or (prefix and k.upper().startswith(prefix))):
                        out[k.upper()] = os.path.expandvars(v)
        except OSError:
            pass
    return out


def profile_dir(cfg=None):
    """La cartella di configurazione che usano le risposte di Hoppy."""
    cfg = cfg or config.load()
    if cfg.get("ask_profile") == "work":
        return Path(os.path.expandvars(os.path.expanduser(cfg.get("work_home") or "~/.claude-work")))
    own = _user_env(names=("CLAUDE_CONFIG_DIR",)).get("CLAUDE_CONFIG_DIR")
    return Path(own) if own else Path.home() / ".claude"


def _settings_env(home):
    """Il blocco "env" di <home>/settings.json (solo i valori di testo)."""
    try:
        data = json.loads((Path(home) / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    env = data.get("env") if isinstance(data, dict) else None
    if not isinstance(env, dict):
        return {}
    return {str(k): str(v) for k, v in env.items() if isinstance(v, (str, int, float))
            and not isinstance(v, bool)}


def env(cfg=None):
    """L'ambiente per `claude -p`: senza i segni di un'altra sessione di Claude Code, con le
    tue CLAUDE_CODE_USE_* (es. Bedrock) e la cartella del profilo scelto."""
    home = profile_dir(cfg)
    e = clean_env()
    e.update(_user_env(prefix="CLAUDE_CODE_USE_"))
    if home != Path.home() / ".claude":
        e["CLAUDE_CONFIG_DIR"] = str(home)
    e.update(_settings_env(home))
    return e


def log(where, err):
    """Annota un errore di Claude in errors.log (nella cartella dei dati di Hoppy)."""
    path = config.DATA_DIR / "errors.log"
    try:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > LOG_MAX:
            path.write_text(path.read_text(encoding="utf-8", errors="replace")[-LOG_MAX // 2:],
                            encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} [{where}] "
                    f"{' '.join(str(err).split())}\n")
    except OSError:
        pass


def friendly(err):
    """Il motivo di un errore di Claude, detto in modo comprensibile."""
    low = str(err or "").lower()
    if "not found" in low or "non trovat" in low:
        return T("Non trovo Claude Code. Installalo (claude.ai/install) e riprova.")
    if any(w in low for w in ("not logged in", "/login", "log in", "login", "authenticat",
                              "invalid api key", "401", "403", "oauth")):
        return T("Claude non ha il login su questo profilo. Apri un terminale, scrivi claude e "
                 "fai /login, oppure scegli l'altro profilo in Impostazioni > Claude.")
    if any(w in low for w in ("credit", "usage limit", "limit reached", "quota", "429",
                              "rate limit", "billing")):
        return T("Ho finito il credito di Claude o ho raggiunto un limite. Riprova più tardi.")
    if any(w in low for w in ("timed out", "timeout", "nessuna risposta", "no answer",
                              "no response")):
        return T("Claude non ha risposto in tempo: forse la rete è lenta o c'è un proxy.")
    return T("Scusa, mi si è annodata la lingua. Riprova! (Il motivo è in errors.log, "
             "nella cartella di Hoppy.)")
