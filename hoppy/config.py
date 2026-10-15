"""Impostazioni e dati dell'utente, separati dal codice.

- DATA_DIR (%APPDATA%\\Hoppy): config.json, memoria, chiacchierate, comandi, pulizie.
- SETTINGS: cosa si può configurare, con default, etichetta e spiegazione.
- load()/save(): config.json; le chiavi sconosciute o i valori del tipo sbagliato si ignorano.
- apply(): copia i valori nelle costanti dei moduli (le leggono mentre girano).
- autostart: collegamenti nella cartella Esecuzione automatica di Windows.
"""
import ctypes
import json
import os
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

APP_NAME = "Hoppy"           # nome del progetto (e della cartella dei dati)
DATA_DIR = Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME
CONFIG_PATH = DATA_DIR / "config.json"
README_URL = "https://github.com/Bazox96/hoppy#readme"
STARTUP_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "Microsoft/Windows/Start Menu/Programs/Startup"
PROGRAMS = (("Hoppy", "hoppy.pet"), ("Hoppy Popup", "hoppy.popup"),   # (collegamento, modulo)
            ("Hoppy Inline", "hoppy.inline"))

MODELS = (("haiku", "Haiku (veloce, costa poco)"), ("sonnet", "Sonnet"), ("opus", "Opus (il più bravo)"))

# key, scheda, etichetta, tipo (bool|int|choice|text), default, dove va (modulo.COSTANTE),
# spiegazione, opzioni (per choice), serve il riavvio?
Setting = namedtuple("Setting", "key tab label kind default target help opts restart",
                     defaults=(None, False))
SETTINGS = (
    # --- mascotte
    Setting("character", "Mascotte", "Personaggio", "choice", "octopus", "pet.CHARACTER", "",
            (("octopus", "Hoppy, il polipetto"), ("crab", "Il granchietto"))),
    Setting("cape", "Mascotte", "Mantello da supereroe", "bool", True, "pet.CAPE", ""),
    Setting("power", "Mascotte", "Super potere per salire", "choice", "random", "pet.POWER", "",
            (("random", "Casuale"), ("web", "Ragnatela"), ("rockets", "Razzi"),
             ("telekinesis", "Telecinesi"))),
    Setting("portal", "Mascotte", "Stile del portale", "choice", "sparks", "pet.PORTAL_STYLE", "",
            (("sparks", "Anello di scintille"), ("ovals", "Ovali turchese e magenta"))),
    Setting("sleep_s", "Mascotte", "Si addormenta dopo (secondi senza mouse)", "int", 45,
            "pet.SLEEP_S", ""),
    Setting("hungry_min", "Mascotte", "Le viene fame dopo (minuti)", "int", 30,
            "pet.HUNGRY_MIN", ""),
    Setting("meeting", "Mascotte", "Durante le call si mette zitta nell'angolo", "bool", True,
            "pet.MEETING_MODE",
            "Riconosce la call dal microfono in uso o da un'app a schermo intero."),
    Setting("reactions", "Mascotte", "Saluti e reazioni (buongiorno, fine call, venerdì sera)",
            "bool", True, "pet.FEAT_REACTIONS", ""),
    Setting("lecture", "Mascotte", "Chi spiega le risposte", "choice", "random", "pet.LECTURE", "",
            (("random", "A caso"), ("professor", "Il professore alla lavagna"),
             ("presenter", "Il divulgatore nello studio"))),
    Setting("music", "Mascotte", "Musichetta nello studio del divulgatore", "bool", True,
            "pet.MUSIC", "Mai mentre il microfono è in uso."),
    # --- avvisi
    Setting("sessions", "Avvisi", "Avvisa quando una sessione di Claude Code finisce", "bool", True,
            "pet.FEAT_SESSIONS", "Anche quando sembra aspettare un tuo permesso."),
    Setting("wait_s", "Avvisi", "...e quando un comando è fermo da (secondi)", "int", 25,
            "watch.WAIT_S", ""),
    Setting("errors", "Avvisi", "Offre di spiegare gli errori che copi", "bool", True,
            "pet.FEAT_ERRORS", "L'errore va a Claude solo se rispondi di sì."),
    Setting("clip", "Avvisi", "Cronologia degli appunti (solo in RAM)", "bool", True,
            "pet.FEAT_CLIP", "Ultimi 20 testi copiati, senza password né token."),
    Setting("ram", "Avvisi", "Guardiano della RAM e delle ore di accensione", "bool", True,
            "pet.FEAT_RAM", ""),
    Setting("ram_uptime_h", "Avvisi", "...avvisa dopo (ore di accensione)", "int", 18,
            "pet.RAM_UPTIME_H", ""),
    Setting("ram_commit", "Avvisi", "...o con la memoria impegnata oltre il (%)", "int", 85,
            "pet.RAM_COMMIT_PCT", ""),
    Setting("standup", "Avvisi", "Standup del mattino sulla lavagna", "bool", False,
            "pet.FEAT_STANDUP",
            "Dalle tue sessioni di Claude Code e dai commit di ieri; una chiamata a Claude al giorno."),
    Setting("standup_hour", "Avvisi", "...dopo le ore", "int", 8, "pet.STANDUP_HOUR", ""),
    Setting("advice", "Avvisi", "Consigli spontanei (pause, ore piccole)", "bool", True,
            "pet.FEAT_ADVICE", ""),
    Setting("advice_day", "Avvisi", "...al massimo al giorno", "int", 6, "pet.MAX_ADVICE_PER_DAY", ""),
    Setting("updates", "Avvisi", "Avvisa quando esce una nuova versione di Hoppy", "bool", True,
            "pet.FEAT_UPDATES", "Una richiesta al giorno a GitHub; installa solo se rispondi di sì."),
    # --- pulizie
    Setting("desktop", "Pulizie", "Propone di riordinare il desktop in cartelle per mese", "bool",
            False, "pet.FEAT_DESKTOP", "Sposta, non cancella; si può annullare dal menu."),
    Setting("recent_days", "Pulizie", "...lasciando stare i file usati negli ultimi (giorni)", "int",
            7, "chores.RECENT_DAYS", ""),
    Setting("old", "Pulizie", "Propone di spostare i file vecchi in «Da rivedere»", "bool", False,
            "pet.FEAT_OLD", "Desktop e Download; si può annullare dal menu."),
    Setting("old_days", "Pulizie", "...vecchi = non usati da (giorni)", "int", 180,
            "chores.OLD_DAYS", ""),
    Setting("dev", "Pulizie", "Propone di ELIMINARE le build dei progetti fermi", "bool", False,
            "pet.FEAT_DEV", "node_modules, target, build... dei progetti di Claude Code. "
            "Non si può annullare (si rigenerano con npm install / mvn)."),
    Setting("dev_days", "Pulizie", "...progetti fermi da (giorni)", "int", 60,
            "chores.DEV_STALE_DAYS", ""),
    Setting("m2", "Pulizie", "Propone di ELIMINARE le versioni vecchie della cache Maven", "bool",
            False, "pet.FEAT_M2", "Maven le riscarica se servono."),
    Setting("m2_days", "Pulizie", "...non usate da (giorni)", "int", 180, "chores.M2_STALE_DAYS", ""),
    # --- Claude
    Setting("model", "Claude", "Modello della mascotte", "choice", "haiku", "pet.MODEL", "", MODELS),
    Setting("inline_model", "Claude", "Modello di ;;...;; e ;;...??", "choice", "haiku",
            "inline.MODEL", "Vale dal prossimo avvio dell'inline.", MODELS),
    Setting("popup_model", "Claude", "Modello del popup (Ctrl+Shift+Spazio)", "choice", "haiku",
            "popup.MODEL", "Vale dal prossimo avvio del popup.", MODELS),
    Setting("work", "Claude", "Ho un secondo profilo di Claude Code (es. per il lavoro)", "bool",
            False, "kn.WORK_ENABLED", "Una seconda cartella di configurazione (CLAUDE_CONFIG_DIR).",
            None, True),
    Setting("work_home", "Claude", "...cartella del profilo", "text", "~/.claude-work",
            "kn.WORK_HOME", "", None, True),
    Setting("work_label", "Claude", "...come lo chiamo", "text", "lavoro", "kn.WORK_LABEL", "",
            None, True),
    Setting("work_launcher", "Claude", "...comando che lo avvia (vuoto = claude)", "text", "",
            "kn.WORK_LAUNCHER", "", None, True),
    Setting("work_memories", "Claude", "...leggi anche le sue memorie", "bool", False,
            "kn.WORK_MEMORIES", "I pezzi pertinenti vanno a Claude dal tuo account personale.",
            None, True),
)
BY_KEY = {s.key: s for s in SETTINGS}
OLD_VALUES = {"spider": "web", "ironman": "rockets", "stranger": "telekinesis",   # versioni vecchie
              "strange": "sparks", "portal": "ovals", "einstein": "professor", "angela": "presenter"}
TABS = tuple(dict.fromkeys(s.tab for s in SETTINGS))


def defaults():
    return {s.key: s.default for s in SETTINGS}


def _valid(s, v):
    if s.kind == "bool":
        return isinstance(v, bool)
    if s.kind == "int":
        return isinstance(v, int) and not isinstance(v, bool) and v >= 0
    if s.kind == "choice":
        return v in [o[0] for o in s.opts]
    return isinstance(v, str)


def load():
    """Le impostazioni (default + config.json) e i flag del wizard."""
    cfg = defaults()
    cfg["wizard_done"] = False
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k in BY_KEY and BY_KEY[k].kind == "choice":
                v = OLD_VALUES.get(v, v)
            if k in BY_KEY and _valid(BY_KEY[k], v):
                cfg[k] = v
        cfg["wizard_done"] = raw.get("wizard_done") is True
    return cfg


def save(cfg):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {k: cfg[k] for k in BY_KEY if k in cfg}
    out["wizard_done"] = bool(cfg.get("wizard_done"))
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CONFIG_PATH)


def apply(cfg, modules):
    """Scrive i valori nelle costanti: modules = {"pet": modulo, "kn": ..., ...}."""
    for s in SETTINGS:
        name, _, const = s.target.partition(".")
        mod = modules.get(name)
        if mod is None:
            continue
        v = cfg.get(s.key, s.default)
        if s.key == "work_home":
            v = Path(os.path.expandvars(os.path.expanduser(v)))
        setattr(mod, const, v)


# ---- avvio automatico ---------------------------------------------------------------
def _pythonw():
    exe = Path(sys.executable)
    w = exe.with_name("pythonw.exe")
    return w if w.exists() else exe


def autostart_on():
    return all((STARTUP_DIR / f"{name}.lnk").exists() for name, _ in PROGRAMS)


def set_autostart(on):
    """Crea o toglie i collegamenti (crearli richiede PowerShell, una volta)."""
    if not on:
        for name, _ in PROGRAMS:
            try:
                (STARTUP_DIR / f"{name}.lnk").unlink()
            except OSError:
                pass
        return True

    def q(s):
        return "'" + str(s).replace("'", "''") + "'"
    lines = ["$sh = New-Object -ComObject WScript.Shell"]
    for name, module in PROGRAMS:
        lines += [f"$l = $sh.CreateShortcut({q(STARTUP_DIR / (name + '.lnk'))})",
                  f"$l.TargetPath = {q(_pythonw())}", f"$l.Arguments = {q('-m ' + module)}",
                  f"$l.WorkingDirectory = {q(Path.home())}", "$l.Save()"]
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "; ".join(lines)],
                           capture_output=True, timeout=30, creationflags=0x08000000)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


# ---- riavvio della mascotte -----------------------------------------------------------
def restart_pet(env):
    """Avvia una nuova mascotte che aspetta la fine di questa (poi chi chiama esce)."""
    subprocess.Popen([str(_pythonw()), "-m", "hoppy.pet", "--after", str(os.getpid())],
                     cwd=str(Path.home()), env=env, creationflags=0x08000000)


def wait_for_exit(pid, timeout_ms=15000):
    h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)   # SYNCHRONIZE
    if h:
        ctypes.windll.kernel32.WaitForSingleObject(h, timeout_ms)
        ctypes.windll.kernel32.CloseHandle(h)


# ---- chi è in esecuzione, e il segnale per uscire (aggiornamenti) ------------------------
_k32 = ctypes.windll.kernel32
_k32.CreateMutexW.restype = _k32.OpenMutexW.restype = _k32.CreateEventW.restype = ctypes.c_void_p
_held = []                                   # handle tenuti aperti finché il programma gira


def mark_running(module):
    """Un mutex col nome del programma: dice agli altri che gira."""
    _held.append(_k32.CreateMutexW(None, False, f"Local\\Hoppy-{module}"))


def is_running(module):
    h = _k32.OpenMutexW(0x00100000, False, f"Local\\Hoppy-{module}")   # SYNCHRONIZE
    if h:
        _k32.CloseHandle(ctypes.c_void_p(h))
    return bool(h)


def quit_event():
    """Evento condiviso: quando la mascotte lo accende (per aggiornarsi), popup e inline escono."""
    h = _k32.CreateEventW(None, True, False, "Local\\HoppyQuit")
    _held.append(h)
    return h


def quit_requested(h):
    return bool(h) and _k32.WaitForSingleObject(ctypes.c_void_p(h), 0) == 0


def request_quit():
    _k32.SetEvent(ctypes.c_void_p(quit_event()))
