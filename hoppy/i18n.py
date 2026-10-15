"""Lingua dell'interfaccia e delle risposte di Claude: italiano (il testo nel codice) o inglese
(le traduzioni in en.py). T("testo") dà il testo nella lingua scelta.

La lingua si legge una volta, all'avvio: HOPPY_LANG (per i test), poi «lang» in config.json,
altrimenti quella di Windows (italiano se Windows è in italiano, sennò inglese)."""
import ctypes
import json
import os
from pathlib import Path

from .en import EN


def _windows_lang():
    try:
        return "it" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x10 else "en"
    except (AttributeError, OSError):
        return "it"


def _pick():
    env = os.environ.get("HOPPY_LANG")
    if env in ("it", "en"):
        return env
    path = Path(os.environ.get("APPDATA") or Path.home()) / "Hoppy" / "config.json"
    try:
        pref = json.loads(path.read_text(encoding="utf-8")).get("lang")
    except (OSError, ValueError, AttributeError):
        pref = None
    return pref if pref in ("it", "en") else _windows_lang()


LANG = _pick()


def T(text):
    """Il testo nella lingua scelta (se manca la traduzione resta in italiano)."""
    return EN.get(text, text) if LANG == "en" else text
