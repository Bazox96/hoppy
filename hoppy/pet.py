"""Hoppy, la mascotte da desktop: un polipetto (o, a scelta, un granchietto) che vive su
tutti i tuoi schermi e ti porta Claude Code a portata di clic.

- Cammina sulla taskbar e sul bordo superiore delle finestre visibili.
- Segue il mouse: se il cursore è più in alto ci arriva coi super poteri
  (ragnatela, razzi o telecinesi); se il cursore è fermo in alto le fluttua accanto.
  Se è più in basso salta giù.
- Se il cursore (o il cibo) è su un altro schermo, o troppo lontano, apre un
  portale e ci passa attraverso: anello di scintille oppure ovali turchese e
  magenta, si sceglie dal menu.
- Se la finestra su cui sta si sposta ci resta sopra; se si chiude o viene coperta, cade.
- Quando non muovi il mouse gironzola, e dopo un po' si addormenta.
- Carezze: strofina il cursore avanti e indietro sopra di lei (senza cliccare).
- Cibo: tasto destro > "Dai da mangiare"; il cibo resta attaccato al cursore e cade
  quando fermi il mouse. Lei lo raggiunge (anche arrampicandosi) e lo mangia.
  Dopo HUNGRY_MIN minuti senza cibo le viene fame e lo fa capire.
- Trascinala col tasto sinistro (anche da uno schermo all'altro) e lasciala cadere.
  Tasto destro: menu.
- Con hoppy-inline: per le domande (;;...??) raggiunge lo schermo dove sei, si mette
  la parrucca da professore e spiega la risposta scrivendola col gesso su una lavagna
  (o, a caso, la spiega da divulgatore in uno studio con le statue);
  per le trasformazioni (;;...;;) dice "Ci lavoro..." e poi "Fatto!".
- Pulizie (chores.py): quando non segue il cursore propone di riordinare il desktop
  in cartelle per mese, di spostare i file vecchi in "Da rivedere" e di eliminare le build
  dei progetti fermi; solo dopo il tuo sì.
- Osserva (watch.py): RAM e ore di accensione, riunioni, sessioni di Claude Code che
  finiscono o aspettano un permesso, appunti (errori da spiegare, cronologia in RAM).
- Lavoro (work.py): standup del mattino, git in sospeso, comandi rapidi, promemoria e
  timer dalla chat, spesa delle sue chiamate a Claude. Giochi: palla e nascondino.
- Impostazioni e presentazione: config.py e settings.py; i dati stanno in %APPDATA%\\Hoppy.

Le chiamate a Claude passano dalla CLI `claude`. L'unica altra rete è una porta locale
(127.0.0.1:PET_PORT) su cui hoppy-inline le passa domande e risposte.
"""
import array
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
import queue
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import wave
import winsound
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path

from . import chores as pet_chores
from . import config as pet_config
from . import knowledge as pet_knowledge
from . import settings as pet_settings
from . import update as pet_update
from . import watch as pet_watch
from . import work as pet_work
from .chores import ChoreLog, known_folder, size_label
from .knowledge import Knowledge, Sessions, clean_env, launch_claude, norm, project_roots

# ---- configurazione ---------------------------------------------------------
P = 6               # lato di un "pixel" della pixel art (dimensione della mascotte)
WALK, RUN = 4.0, 9.0    # velocità in px per fotogramma
CLIMB = 10.0        # velocità di salita col super potere (px per fotogramma)
GRAVITY = 0.9
POWER = "random"    # "random", "web" (ragnatela), "rockets" (razzi), "telekinesis" (telecinesi)
CAPE = True        # mantello da supereroe (si può togliere dal menu)
CHUTE_DROP = 230    # caduta oltre questa altezza: apre il paracadute
CHUTE_VY = 3.2      # velocità di discesa col paracadute aperto
ACTIVITY_MIN = 7.0  # ogni quanti secondi, a riposo, può mettersi a fare qualcosa
FOLLOW_S = 30.0     # resta col mouse (anche fermo) per N secondi dall'ultimo movimento
SLEEP_S = 45.0      # si addormenta dopo N secondi senza movimenti del mouse
HUNGRY_MIN = 30     # le viene fame dopo N minuti senza cibo
RUB_PX = 150        # quanti px di "strofinata" sopra di lei per farle le carezze
PORTAL_DIST = 1000  # sullo stesso schermo, oltre questa distanza usa il portale
PORTAL_COOLDOWN = 2.0
PORTAL_STYLE = "sparks"   # "sparks" (anello di scintille) oppure "ovals" (ovali turchese e magenta)
PET_PORT = 48761    # porta locale su cui claude_inline la chiama (stessa costante là)
CHALK_FONT = "Segoe Print"
MODEL = "haiku"             # modello usato per parlare, consigliare, proporre migliorie
MAX_ADVICE_PER_DAY = 6      # consigli spontanei al giorno (le chiamate costano credito)
BREAK_GAP_S = 150           # una pausa del mouse più lunga azzera la sessione di lavoro
LONG_WORK_MIN = 50          # oltre questi minuti filati può suggerire una pausa
MEM_PATH = pet_config.DATA_DIR / "pet_memory.json"   # memoria locale, leggibile
PROPOSALS_PATH = pet_config.DATA_DIR / "pet_proposals.md"
SESSIONS_PATH = pet_config.DATA_DIR / "pet_sessions"  # le vostre chiacchierate
CHORES_PATH = pet_config.DATA_DIR / "pet_chores.json"  # spostamenti fatti (per annullarli)
CHORE_FIRST_S = 3 * 60      # prima occhiata a desktop e Download dopo l'avvio
CHORE_EVERY_S = 30 * 60     # poi ogni tanto, quando non sta seguendo il cursore
CHORE_SNOOZE_S = 3 * 86400  # se dici di no, non lo ripropone per 3 giorni
CHAT_TURNS = 12             # battute della conversazione che ricorda (solo in RAM)
CHAT_FORGET_S = 15 * 60     # dopo tanto silenzio la conversazione ricomincia da capo
DIARY_SHOWN = 8             # quanti riassunti delle chiacchierate passate ricorda sempre
DIARY_KEEP = 60             # quanti riassunti tiene nel diario
MOOD_DEFAULT = 0.6         # umore iniziale (unico valore, usato anche dopo "Dimentica tutto")
MAX_LINE = 65536            # tetto alla lunghezza di una riga ricevuta sul socket locale
FRAME_MS = 33

CHARACTER = "octopus"       # "octopus" (Hoppy, il polipetto) o "crab" (il granchietto)
WHO = {"octopus": "Hoppy, un polipetto viola", "crab": "un granchietto arancione"}
PERSONA = (
    "Sei {who}, la mascotte che vive sul desktop di {user} e gli porta Claude a portata di clic. "
    "Parli in prima persona, in italiano, con tono caldo, curioso e un po' giocoso. "
    "Sei breve: una o due frasi, mai elenchi. Non inventare fatti personali sull'utente: "
    "usa solo quello che trovi in COSA RICORDO, PROGETTI, DIARIO, MEMORIE e CONVERSAZIONI "
    "PASSATE. Non dare consigli medici o finanziari seri."
)
LAUNCH_HINT = (
    "Se l'utente ti chiede di aprire o avviare Claude (Claude Code) su uno dei suoi progetti, "
    "rispondi in breve e aggiungi come ultimissima riga '#AVVIA: <nome del progetto, scritto "
    "esattamente come in uno degli elenchi dei suoi progetti, personali o di lavoro>'. "
    "Altrimenti non aggiungerla mai. Se ti chiede di usare una delle sue SKILL (anche "
    "scrivendo /nome), aggiungi come ultimissima riga '#SKILL: <nome della skill> <argomenti, "
    "es. il codice del ticket>' (con #AVVIA solo se nomina anche un progetto)."
)
LAUNCH_WORDS = ("avvia", "avviami", "apri", "aprimi", "lancia", "lanciami", "fai partire",
                "start", "open")
REMEMBER_HINT = (
    "Se l'utente ti dice qualcosa che vale la pena ricordare (il suo nome, una preferenza, "
    "un progetto, un gusto), aggiungi come ultimissima riga '#RICORDA: <fatto in poche parole>'. "
    "Se ti dice come si chiama, usa '#NOME: <nome>'. Altrimenti non aggiungere nulla."
)
REMIND_HINT = (
    "Adesso è {now}. Se l'utente ti chiede di ricordargli qualcosa a un'ora o in un giorno "
    "precisi, aggiungi come ultima riga '#PROMEMORIA: AAAA-MM-GG HH:MM | <cosa ricordare>'. "
    "Se chiede un timer o un pomodoro (pomodoro = 25 minuti), aggiungi '#TIMER: <minuti> | "
    "<etichetta>'. Se chiede di lanciare uno dei suoi COMANDI RAPIDI, aggiungi "
    "'#COMANDO: <nome esatto del comando>' (glielo farai confermare). Altrimenti niente."
)
CHAT_TAGS = ("#AVVIA:", "#SKILL:", "#PROMEMORIA:", "#TIMER:", "#COMANDO:")
# guardiano della RAM (es. driver che perdono memoria): avvisa oltre una di queste soglie
RAM_UPTIME_H = 18           # ore di accensione
RAM_COMMIT_PCT = 85         # memoria impegnata sul massimo
RAM_NONPAGED_GB = 6.0       # memoria del kernel (cresce coi processi fantasma)
RAM_REPEAT_S = 2 * 3600     # non ripete l'avviso più spesso di così
STANDUP_HOUR = 8            # standup alla prima attività dei giorni feriali dopo quest'ora
DEV_SCAN_S = 24 * 3600      # build vecchie da buttare: controlla una volta al giorno
COMMANDS_PATH = pet_config.DATA_DIR / "pet_commands.json"
BALL_IDLE_S = 90            # la palla sparisce dopo tanto che nessuno ci gioca
HIDE_S = 60                 # nascondino: dopo tanto esce da sola
MEETING_MODE = True         # in call: zitta e nell'angolo
LECTURE = "random"          # chi spiega: "random", "professor" o "presenter"
MUSIC = True                # musichetta nello studio del divulgatore
# funzioni accese o spente (dalle Impostazioni: pet_config.SETTINGS)
FEAT_REACTIONS = FEAT_SESSIONS = FEAT_ERRORS = FEAT_CLIP = FEAT_RAM = FEAT_ADVICE = True
FEAT_STANDUP = FEAT_DESKTOP = FEAT_OLD = FEAT_DEV = FEAT_M2 = FEAT_UPDATES = True
START_COMPANIONS = True     # all'avvio fa partire anche popup e inline
UPDATE_EVERY_S = 24 * 3600   # ogni quanto chiede a GitHub se c'è una versione nuova
# -----------------------------------------------------------------------------

KEY = "#010203"     # colore reso trasparente (e click-through)
ORANGE, EYE = "#D97757", "#1F1E1D"
OCTO, OCTO_DARK = "#A77BD6", "#7E57B0"   # Hoppy: corpo e macchioline/ventose
LEAF, WOOD_DARK = "#7CB342", "#7A5232"
WEB = "#F4F4F4"
GOGGLE_STRAP, GOGGLE_LENS = "#6D4C41", "#BDE7F2"   # occhialoni da aviatore (razzi)
FLAME = ("#FFF3B0", "#FFC233", "#FF7A1A")
TELE, TELE_SOFT = "#9B4DCA", "#D7B4F0"
POWERS = ("web", "rockets", "telekinesis")
POWER_NAMES = {"random": "Casuale", "web": "Ragnatela", "rockets": "Razzi",
               "telekinesis": "Telecinesi"}
MENU_BG, MENU_FG, MENU_BORDER, MENU_RED = "#FAF9F5", "#1F1E1D", "#D97757", "#B3261E"
HEART, BLUSH = "#E8577A", "#F4A6A0"
COOKIE, COOKIE_EDGE, CHIP = "#C68B59", "#8B5A2B", "#4E342E"
APPLE, APPLE_EDGE, STEM = "#E0403A", "#A8231F", "#6D4C41"
SPARKS = ("#FFB300", "#FF8F00", "#FFD54F", "#FF6F00", "#FFE082")
OVALS = {True: ("#2EC4B6", "#A8F0E8", "#0B3B37"),       # entrata: turchese
         False: ("#D94FC4", "#F2B8E9", "#3F1238")}      # uscita: magenta
CAPE_COL, CAPE_DARK = "#C0392B", "#922B21"
CHUTE_COL, CHUTE_ALT, CHUTE_STR = "#E74C3C", "#F5F5F0", "#4A4A4A"
STAR = "#FFE082"
DUMBBELL = "#5F6368"
CHALK, CHALK_DIM, CHALK_ERR = "#F2F2E9", "#BFCBB8", "#FF9E9E"
BOARD, BOARD_FRAME, BOARD_LEDGE = "#2F4F3A", "#8B5A2B", "#A9875F"
WIG, WIG_SHADE, MUSTACHE = "#F5F5F0", "#C9C9C2", "#E3E3DA"
# studio del divulgatore: fondale blu notte, cornice dorata, statue di marmo
STUDIO, STUDIO_FRAME, STUDIO_GOLD = "#14233F", "#2E3D5C", "#D8B45A"
STUDIO_TEXT, STUDIO_DIM, STUDIO_ERR = "#F3EBD8", "#A9B4C8", "#FF9E9E"
MARBLE, MARBLE_SHADE = "#ECE8DF", "#BDB6A8"
HAIR, JACKET, SHIRT, TIE = "#4A3426", "#2B2F3A", "#DCE8F2", "#7A1F2B"
STUDIO_FONT = "Georgia"
LECTURE_STYLES = ("professor", "presenter")   # chi spiega: scelto a caso a ogni spiegazione
HEART_PIX = (".X.X.", "XXXXX", "XXXXX", ".XXX.", "..X..")
WIG_PARTS = (       # parrucca da professore: (col0, riga0, col1, riga1, colore) in pixel
    (0, -0.6, 7, 0.4, WIG),
    (0.4, -1.3, 1.3, -0.5, WIG), (1.9, -1.7, 2.8, -0.5, WIG_SHADE),
    (3.4, -1.4, 4.3, -0.5, WIG), (5.0, -1.8, 5.9, -0.5, WIG),
    (-1.4, -0.2, 0.3, 1.2, WIG), (-1.9, 0.6, -0.5, 1.7, WIG_SHADE), (-1.2, 1.5, 0.1, 2.2, WIG),
    (6.7, -0.2, 8.4, 1.2, WIG), (7.5, 0.6, 8.9, 1.7, WIG_SHADE), (6.9, 1.5, 8.2, 2.2, WIG))
PET_W, PET_H = 7 * P, 7 * P     # corpo 7x5 + zampe 2 (le braccia sporgono di P per lato)
MARGIN = PET_W // 2 + P         # distanza minima dalle estremità di un bordo
PORTAL_RX, PORTAL_RY = 20, 36   # semiassi del portale
PORTAL_OFF = PET_W / 2 + 20     # distanza del portale dalla mascotte
HIDDEN = PET_W / 2 + P + 2      # oltre il centro del portale di tanto: tutta dentro

Rect = namedtuple("Rect", "left top right bottom")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32")
dwmapi = ctypes.WinDLL("dwmapi")
user32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_long]
dwmapi.DwmGetWindowAttribute.argtypes = [wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD]

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x20, 0x80, 0x08000000
DWMWA_EXTENDED_FRAME_BOUNDS, DWMWA_CLOAKED = 9, 14
SKIP_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
                "Windows.UI.Core.CoreWindow"}
ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.POINTER(wt.RECT), wt.LPARAM)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT),
                ("dwFlags", wt.DWORD)]


user32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFO)]
user32.EnumDisplayMonitors.argtypes = [ctypes.c_void_p, ctypes.c_void_p, MONITORENUMPROC,
                                       wt.LPARAM]
user32.GetForegroundWindow.restype = wt.HWND
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.CloseHandle.argtypes = [wt.HANDLE]
kernel32.CloseHandle.restype = wt.BOOL
kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                                ctypes.POINTER(wt.DWORD)]


def round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def active_app(own_pid):
    """Nome del programma in primo piano (es. 'idea64', 'chrome'), o '' se è la mascotte."""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(pid))
    if pid.value in (0, own_pid):
        return ""
    h = kernel32.OpenProcess(0x1000, False, pid.value)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(512)
        size = wt.DWORD(512)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.splitext(os.path.basename(buf.value))[0]
        return ""
    finally:
        kernel32.CloseHandle(h)


def ask_claude(prompt, system, timeout=90):
    """Una domanda a Claude via CLI (piano abbonamento). Ritorna (testo, None) o (None, errore)."""
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    if not Path(exe).exists():
        return None, "CLI 'claude' non trovata"
    cmd = [exe, "-p", "--model", MODEL, "--output-format", "json",
           "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config",
           "--tools", "", "--system-prompt", system]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                           timeout=timeout, cwd=tempfile.gettempdir(), env=clean_env(),
                           creationflags=0x08000000)   # CREATE_NO_WINDOW
    except (subprocess.TimeoutExpired, OSError) as e:
        return None, str(e)
    try:
        out = json.loads(r.stdout)
    except ValueError:
        out = {}
    COSTS.put(out.get("total_cost_usd") or 0.0)   # la spesa la conta la mascotte (pet_work)
    if r.returncode != 0 or out.get("is_error") or "result" not in out:
        return None, (r.stderr or out.get("result") or r.stdout or "errore").strip()[:200]
    return out["result"].strip(), None


COSTS = queue.Queue()       # costo di ogni chiamata a Claude (in dollari), dai thread


class Brain:
    """Memoria e umore della mascotte, salvati in un file JSON locale leggibile e cancellabile."""

    def __init__(self):
        self.data = self._blank()
        try:
            if MEM_PATH.exists():
                self.data.update(json.loads(MEM_PATH.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
        self.mood = float(self.data.get("mood", MOOD_DEFAULT))

    @staticmethod
    def _blank():
        return {"name": "", "facts": [], "advice_up": {}, "advice_down": {},
                "mood": MOOD_DEFAULT, "created": datetime.now().isoformat(timespec="seconds"),
                "last_proposal_day": "", "diary": []}

    def save(self):
        self.data["mood"] = round(self.mood, 3)
        try:
            MEM_PATH.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        except OSError:
            pass

    @property
    def name(self):
        return self.data.get("name", "")

    def set_name(self, name):
        name = name.strip()[:40]
        if name and name != self.data.get("name"):
            self.data["name"] = name
            self.save()

    def remember(self, fact):
        fact = fact.strip()[:120]
        facts = self.data.setdefault("facts", [])
        if fact and fact.lower() not in (f.lower() for f in facts):
            facts.append(fact)
            del facts[:-20]                  # tiene solo gli ultimi 20
            self.save()

    def add_diary(self, sid, summary):
        """Riassunto di una chiacchierata; se la stessa conversazione è continuata, lo aggiorna."""
        summary = " ".join(summary.split())[:400]
        diary = [e for e in self.data.setdefault("diary", []) if e.get("id") != sid]
        diary.append({"id": sid, "summary": summary})
        self.data["diary"] = diary[-DIARY_KEEP:]
        self.save()

    def diary_context(self, n=DIARY_SHOWN):
        return "\n".join(f"({e['id'][8:10]}/{e['id'][5:7]}) {e['summary']}"
                         for e in self.data.get("diary", [])[-n:])

    def forget_all(self):
        self.data = self._blank()
        self.mood = MOOD_DEFAULT
        try:
            MEM_PATH.unlink(missing_ok=True)
        except OSError:
            pass

    def feedback(self, category, good):
        key = "advice_up" if good else "advice_down"
        d = self.data.setdefault(key, {})
        d[category] = d.get(category, 0) + 1
        self.bump_mood(0.05 if good else -0.03)
        self.save()

    def liked(self, category):              # bilancio pollici su/giù per una categoria
        up = self.data.get("advice_up", {}).get(category, 0)
        down = self.data.get("advice_down", {}).get(category, 0)
        return up - down

    def bump_mood(self, delta):
        self.mood = max(0.0, min(1.0, self.mood + delta))

    def mood_label(self):
        return ("giù di morale" if self.mood < 0.3 else
                "tranquilla" if self.mood < 0.55 else
                "di buon umore" if self.mood < 0.8 else "euforica")

    def context(self):
        parts = []
        if self.name:
            parts.append(f"L'utente si chiama {self.name}.")
        if self.data.get("facts"):
            parts.append("So queste cose: " + " ; ".join(self.data["facts"][-8:]))
        liked = sorted(self.data.get("advice_up", {}).items(), key=lambda kv: -kv[1])
        if liked:
            parts.append("Consigli graditi in passato: "
                         + ", ".join(k for k, _ in liked[:3]) + ".")
        return " ".join(parts) or "Non so ancora nulla di lei."

    @staticmethod
    def parse_tags(text):
        """Estrae le righe #NOME: e #RICORDA: dalla risposta, ritorna (testo pulito, nome, fatti)."""
        name, facts, keep = "", [], []
        for line in text.splitlines():
            s = line.strip()
            if s.upper().startswith("#NOME:"):
                name = s.split(":", 1)[1].strip()
            elif s.upper().startswith("#RICORDA:"):
                facts.append(s.split(":", 1)[1].strip())
            else:
                keep.append(line)
        return "\n".join(keep).strip(), name, facts


def monitor_rects():
    """Schermi come (rettangolo intero, area di lavoro), il principale per primo."""
    out = []

    def cb(hmon, _hdc, _rc, _lp):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            m, w = mi.rcMonitor, mi.rcWork
            out.append(((m.left, m.top, m.right, m.bottom),
                        (w.left, w.top, w.right, w.bottom), bool(mi.dwFlags & 1)))
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    out.sort(key=lambda m: not m[2])
    return [(full, work) for full, work, _ in out]


def cursor_pos():
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def window_rects(own_pid):
    """Finestre normali visibili in ordine z (dalla più in alto): (hwnd, l, t, r, b)."""
    out = []

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == own_pid:
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & (WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
                                                      | WS_EX_NOACTIVATE):
            return True
        if user32.GetWindowTextLengthW(hwnd) == 0:
            return True
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if cls.value in SKIP_CLASSES:
            return True
        cloaked = ctypes.c_int(0)           # finestre "nascoste" da DWM (altri desktop, UWP)
        dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked),
                                     ctypes.sizeof(cloaked))
        if cloaked.value:
            return True
        r = wt.RECT()                       # bordi visibili, senza l'ombra invisibile
        if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r),
                                        ctypes.sizeof(r)) != 0:
            user32.GetWindowRect(hwnd, ctypes.byref(r))
        if r.right - r.left >= 120 and r.bottom - r.top >= 60:
            out.append((hwnd, r.left, r.top, r.right, r.bottom))
        return True

    user32.EnumWindows(ENUMPROC(cb), 0)
    return out


def platforms(wins, wa):
    """Superfici calpestabili di uno schermo: la taskbar e i tratti visibili del bordo
    superiore delle finestre (tolti quelli coperti da finestre più in alto)."""
    plats = [(None, wa.bottom, wa.left, wa.right)]
    above = []
    for hwnd, l, t, r, b in wins:
        if wa.top + PET_H + 6 <= t < wa.bottom - 20:
            segs = [(max(l, wa.left), min(r, wa.right))]
            for al, at, ar, ab in above:
                if at < t < ab:             # quella finestra copre la riga del bordo
                    segs = [s for a, e in segs
                            for s in ((a, min(e, al)), (max(a, ar), e)) if s[1] > s[0]]
            plats += [(hwnd, t, a, e) for a, e in segs if e - a >= 2 * MARGIN]
        above.append((l, t, r, b))
    return plats


class Monitor:
    """Uno schermo: area di lavoro, finestra trasparente sovrapposta e superfici."""

    def __init__(self, root, full, work):
        self.full, self.wa = Rect(*full), Rect(*work)
        self.ox, self.oy = self.wa.left, self.wa.top
        w, h = self.wa.right - self.wa.left, self.wa.bottom - self.wa.top
        self.win = win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.configure(bg=KEY)
        win.geometry(f"{w}x{h}+{self.wa.left}+{self.wa.top}")
        win.attributes("-topmost", True, "-transparentcolor", KEY)
        self.c = tk.Canvas(win, width=w, height=h, bg=KEY, highlightthickness=0, bd=0)
        self.c.pack()
        win.update_idletasks()
        hwnd = int(win.frame(), 16)         # mai il focus, niente icona in taskbar
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                              | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        self.plats = [(None, self.wa.bottom, self.wa.left, self.wa.right)]

    def contains(self, x, y):
        f = self.full
        return f.left <= x < f.right and f.top <= y < f.bottom


def serve_inline(inbox):
    """Riceve da claude_inline (solo connessioni locali) righe JSON. Ogni connessione è
    una richiesta: i messaggi finiscono in coda come (id connessione, messaggio)."""
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", PET_PORT))
        srv.listen(4)
    except OSError:
        return                               # porta occupata: c'è già un'altra mascotte

    def handle(conn, cid):
        with conn, conn.makefile("r", encoding="utf-8") as lines:
            while True:
                line = lines.readline(MAX_LINE)     # tetto: una riga non può gonfiare la RAM
                if not line:
                    break
                if not line.endswith("\n"):          # troppo lunga o troncata: la scarto
                    continue
                try:
                    inbox.put((cid, json.loads(line)))
                except ValueError:
                    pass

    cid = 0
    while True:
        conn, _ = srv.accept()
        cid += 1
        threading.Thread(target=handle, args=(conn, cid), daemon=True).start()


def ctrl_v():
    user32.keybd_event(0x11, 0, 0, 0)
    user32.keybd_event(0x56, 0, 0, 0)
    user32.keybd_event(0x56, 0, 2, 0)
    user32.keybd_event(0x11, 0, 2, 0)


AIR_EIGHTH = 0.42          # secondi per ottavo
# Bach, Aria sulla quarta corda (pubblico dominio): (nota MIDI, durata in ottavi)
AIR_MELODY = ((78, 8), (78, 2), (83, .5), (79, .5), (76, .5), (74, .5), (73, .5), (74, .5),
              (73, 3), (74, 4))
AIR_BASS = (50, 62, 49, 61, 47, 59, 45, 57, 43, 55, 42, 54, 40, 52, 38, 50, 45, 57, 38, 50)


def air_wav(path, sr=22050):
    """Sintetizza la musichetta (melodia legata con vibrato + basso a ottave) in un WAV."""
    n8 = AIR_EIGHTH
    total = int(sr * n8 * (sum(d for _, d in AIR_MELODY) + 4))
    buf = [0.0] * total

    def add(midi, t0, dur, amp, decay, vib):
        f = 440 * 2 ** ((midi - 69) / 12)
        i0 = int(t0 * sr)
        for i in range(min(int(dur * sr), total - i0)):
            t = i / sr
            env = min(1.0, t / 0.04, (dur - t) / 0.08) * math.exp(-t * decay)
            ph = 2 * math.pi * f * t + vib * math.sin(2 * math.pi * 5.5 * t)
            buf[i0 + i] += amp * env * (math.sin(ph) + 0.35 * math.sin(2 * ph)
                                        + 0.15 * math.sin(3 * ph))

    t = 0.0
    for k, (midi, d) in enumerate(AIR_MELODY):
        add(midi, t, d * n8 + (1.5 if k == len(AIR_MELODY) - 1 else 0.05), 0.3, 0.15, 0.6)
        t += d * n8
    for k, midi in enumerate(AIR_BASS):
        add(midi, k * n8, n8 * (4 if k == len(AIR_BASS) - 1 else 1.1), 0.22, 1.5, 0.0)
    peak = max(abs(v) for v in buf) or 1.0
    pcm = array.array("h", (int(v / peak * 26000) for v in buf))
    tmp = path.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    os.replace(tmp, path)


def play_air(board):
    """Musichetta in sottofondo (generata la prima volta in un thread, poi riusata)."""
    def run():
        path = Path(tempfile.gettempdir()) / "hoppy_aria.wav"
        try:
            if not path.exists():
                air_wav(path)
            if board.alive and board.phase != "sink":
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC
                                   | winsound.SND_NODEFAULT)
        except (OSError, RuntimeError):
            pass
    threading.Thread(target=run, daemon=True).start()


def draw_statue(c, x, floor, tags, bust=True):
    """Statua di marmo in pixel art: busto su colonnina, oppure colonna dorica."""
    def r(x0, y0, x1, y1, col=MARBLE):
        c.create_rectangle(x + x0, floor - y1, x + x1, floor - y0, fill=col, width=0, tags=tags)
    if bust:
        r(-22, 0, 22, 8)                                    # base
        r(-14, 8, 14, 96, MARBLE_SHADE)                     # colonnina
        r(-10, 8, 10, 96)
        r(-20, 96, 20, 104)                                 # capitello
        r(-24, 104, 24, 124)                                # spalle
        r(-7, 124, 7, 132, MARBLE_SHADE)                    # collo
        r(-13, 132, 13, 160)                                # testa
        r(-15, 152, 15, 166, MARBLE_SHADE)                  # riccioli
        r(-4, 140, -1, 146, MARBLE_SHADE)                   # occhi vuoti
        r(3, 140, 6, 146, MARBLE_SHADE)
    else:
        r(-30, 0, 30, 10)
        for k in (-18, -6, 6, 18):                          # scanalature
            r(k - 5, 10, k + 5, 190, MARBLE if k % 12 else MARBLE_SHADE)
        r(-34, 190, 34, 200, MARBLE_SHADE)                  # capitello
        r(-30, 200, 30, 212)


class Blackboard:
    """Lavagna che sale dal pavimento: la mascotte ci scrive la risposta. Due stili a caso:
    il professore (parrucca, lavagna e gesso) o il divulgatore (studio con statue e musichetta)."""

    def __init__(self, pet, mon, cid, question, ctx_len, hwnd, style="professor"):
        self.pet, self.mon, self.cid, self.hwnd = pet, mon, cid, hwnd
        self.style = style
        ang = style == "presenter"
        bg, frame = (STUDIO, STUDIO_FRAME) if ang else (BOARD, BOARD_FRAME)
        fg, dim, err = (STUDIO_TEXT, STUDIO_DIM, STUDIO_ERR) if ang else (CHALK, CHALK_DIM, CHALK_ERR)
        font = STUDIO_FONT if ang else CHALK_FONT
        self.c = c = mon.c
        wa = mon.wa
        w = min(700, wa.right - wa.left - 220)
        h = min(430, wa.bottom - wa.top - 160)
        legs = 34
        self.left = (wa.left + wa.right) / 2 - w / 2 + 50   # coordinate globali
        self.spot_x = self.left - 40                          # dove si mette la mascotte
        L, T = self.left - mon.ox, wa.bottom - legs - h - mon.oy
        R, B = L + w, T + h
        tg = ("board",)
        if ang:                                              # statue ai lati dello studio
            floor = wa.bottom - mon.oy
            draw_statue(c, L - 130, floor, tg, bust=False)
            if R + 62 <= wa.right - mon.ox:
                draw_statue(c, R + 34, floor, tg)
        for lx in (L + 40, R - 40):                          # gambe
            c.create_rectangle(lx - 5, B, lx + 5, B + legs, fill=frame, width=0, tags=tg)
        c.create_rectangle(L, T, R, B, fill=frame, width=0, tags=tg)                # cornice
        if ang:
            c.create_rectangle(L + 6, T + 6, R - 6, B - 6, outline=STUDIO_GOLD, width=2, tags=tg)
        c.create_rectangle(L + 10, T + 10, R - 10, B - 10, fill=bg, width=0, tags=tg)
        if not ang:
            c.create_rectangle(L + 24, B - 4, R - 24, B + 5, fill=BOARD_LEDGE, width=0, tags=tg)
            c.create_rectangle(R - 80, B - 9, R - 58, B - 4, fill=CHALK, width=0, tags=tg)  # gesso
        q = question if len(question) <= 70 else question[:67] + "…"
        head = f"Domanda: «{q}»"
        if ctx_len is not None:
            head += f"   ·   ho letto {ctx_len} caratteri"
        c.create_text(L + 26, T + 20, anchor="nw", text=head, fill=dim,
                      font=(font, 9, "italic") if ang else (font, 9), width=w - 150, tags=tg)
        c.create_text(R - 24, T + 16, anchor="ne", text="⚛" if ang else "E = mc²",
                      fill=STUDIO_GOLD if ang else dim,
                      font=("Segoe UI Symbol", 16) if ang else (font, 12), tags=tg)
        c.create_line(L + 26, T + 54, R - 26, T + 54, fill=STUDIO_GOLD if ang else dim,
                      dash=() if ang else (4, 4), tags=tg)

        t = self.txt = tk.Text(c, wrap="word", bg=bg, fg=fg, relief="flat", bd=0,
                               highlightthickness=0, font=(font, 11), cursor="arrow",
                               padx=0, pady=0, spacing1=2, state="disabled")
        t.tag_configure("b", font=(font, 11, "bold"))
        t.tag_configure("err", foreground=err)
        t.tag_configure("dim", foreground=dim)
        t.bind("<Button-1>", lambda e: self.skip())
        self.win_id = c.create_window(L + 26, T + 62, anchor="nw", window=t, width=w - 52,
                                      height=h - 62 - 58, tags=tg)
        self.bar = bar = tk.Frame(c, bg=bg)
        self.btns = []
        for label, cmd, bbg in (("Incolla al cursore", self.paste, frame),
                                ("Copia", self.copy, "#3B4A6B" if ang else "#6D4C41"),
                                ("Chiudi", self.close, "#5A4A2A" if ang else "#3E5B47")):
            b = tk.Button(bar, text=label, command=cmd, bg=bbg, fg=fg, relief="flat", bd=0,
                          font=("Segoe UI", 9), padx=12, pady=4, cursor="hand2",
                          activebackground=bbg, activeforeground=fg)
            b.pack(side="left", padx=(0, 8))
            self.btns.append(b)
        self.status = tk.Label(bar, text="", bg=bg, fg=dim, font=("Segoe UI", 9))
        self.status.pack(side="left")
        c.create_window(L + 26, B - 46, anchor="nw", window=bar, tags=("board", "board_btns"))
        c.itemconfigure("board_btns", state="hidden")
        c.tag_bind("board", "<Button-1>", lambda e: self.skip())

        self.hidden = h + legs + 12          # parte sotto il pavimento e sale
        self.off = self.hidden
        c.move("board", 0, self.off)
        self.phase = "rise"                  # rise | think | talk | idle | sink
        self.pending = None
        self.chars, self.pos, self.plain, self.error = [], 0, "", False
        self.dots = -1
        self.alive = True

    def set_text(self, segments):
        t = self.txt
        t.config(state="normal")
        t.delete("1.0", "end")
        for s, tag in segments:
            t.insert("end", s, tag)
        t.config(state="disabled")

    def update(self, now):
        c = self.c
        if self.phase == "rise":
            step = min(self.off, max(4, int(self.off * 0.2)))
            c.move("board", 0, -step)
            self.off -= step
            if self.off <= 0:
                self.phase = "think"
        elif self.phase == "sink":
            step = min(self.hidden - self.off, max(4, int((self.off + 8) * 0.25)))
            c.move("board", 0, step)
            self.off += step
            if self.off >= self.hidden:
                self.destroy()
        elif self.phase == "think":
            if self.pending and self.pet.state == "lecture":
                self.start_talk(*self.pending)
            else:
                d = int(now / 0.4) % 4
                if d != self.dots:
                    self.dots = d
                    self.set_text([("Mmm, fammi pensare" + "." * d, "dim")])
        elif self.phase == "talk" and self.pet.state == "lecture":
            self.write(max(3, len(self.chars) // 150))

    def answer(self, text, error):
        self.pending = (text, error)         # parte appena lei è alla lavagna

    def start_talk(self, text, error):
        self.pending = None
        self.plain, self.error = text.replace("**", ""), error
        self.chars = []
        for i, part in enumerate(text.split("**")):     # **grassetto** -> gesso calcato
            tag = "err" if error else ("b" if i % 2 else "")
            self.chars.extend((ch, tag) for ch in part)
        self.pos = 0
        self.set_text([])
        self.phase = "talk"

    def write(self, n):
        end = min(len(self.chars), self.pos + n)
        t = self.txt
        if self.pos < end:
            t.config(state="normal")
            i = self.pos
            while i < end:
                tag, j = self.chars[i][1], i
                while j < end and self.chars[j][1] == tag:
                    j += 1
                t.insert("end", "".join(ch for ch, _ in self.chars[i:j]), tag)
                i = j
            t.config(state="disabled")
            t.see("end")
            self.pos = end
            box = t.bbox("end-2c")           # polvere di gesso dopo l'ultima lettera scritta
            if box and self.style == "professor":
                wx, wy = self.c.coords(self.win_id)
                self.pet.particles.append({
                    "kind": "dust", "mon": self.mon, "x": wx + box[0] + box[2] + self.mon.ox,
                    "y": wy + box[1] + box[3] + self.mon.oy, "vx": random.uniform(-0.3, 0.3),
                    "vy": 0.4, "life": 12, "color": CHALK})
        if self.pos >= len(self.chars):
            self.phase = "idle"
            if self.error:
                for b in self.btns[:2]:
                    b.pack_forget()
            self.c.itemconfigure("board_btns", state="normal")

    def skip(self):
        if self.phase == "talk":
            self.write(len(self.chars))

    def copy(self):
        root = self.pet.root
        root.clipboard_clear()
        root.clipboard_append(self.plain)
        root.update()
        self.status.config(text="Copiato")

    def paste(self):
        self.copy()
        self.close()
        if self.hwnd:
            user32.SetForegroundWindow(self.hwnd)
        self.pet.root.after(150, ctrl_v)

    def close(self):
        if self.phase == "sink":
            return
        self.c.itemconfigure("board_btns", state="hidden")
        self.phase = "sink"
        if self.style == "presenter":
            winsound.PlaySound(None, 0)      # ferma la musichetta
        self.pet.end_lecture(self)

    def destroy(self):
        self.alive = False
        self.c.delete("board")
        self.txt.destroy()
        self.bar.destroy()
        if self.pet.lecture is self:
            self.pet.lecture = None


class Pet:
    def __init__(self, root):
        self.root = root
        self.mons = [Monitor(root, full, work) for full, work in monitor_rects()]
        self.mon = self.mons[0]              # parte dallo schermo principale
        self.pid = kernel32.GetCurrentProcessId()

        now = time.time()
        wa = self.wa
        self.x, self.y, self.vy = (wa.left + wa.right) / 2, wa.top + PET_H + 10.0, 0.0
        self.state, self.since = "fall", now
        self.stand, self.stand_rect = None, None   # (hwnd, y) e posizione della finestra
        self.ignore = None                         # bordo da attraversare saltando giù
        self.tx, self.climb, self.hop_after = self.x, None, False
        self.fall_y0, self.chute = self.y, False   # paracadute
        self.act_dir = 1                           # verso dell'attività in corso
        self.cape_on = CAPE
        self.next_activity = now + ACTIVITY_MIN
        self.power_pref = POWER                    # potere scelto dal menu ("random" = a caso)
        self.power = "web"                      # potere della salita in corso
        self.rise_goal = 0.0                       # quota da raggiungere salendo
        self.anchor_pt = (0.0, 0.0)                # dove è attaccata la ragnatela
        self.float_side = 1                        # da che lato del cursore fluttua
        self.rects = {}
        self.last_refresh = 0.0
        self.mouse = cursor_pos()
        self.last_move = now
        self.anchor, self.anchor_t = self.mouse, now   # dove il cursore si è "fermato"
        self.next_think = now
        self.next_blink, self.blink_until = now + 2, 0.0
        self.anim = 0.0
        self.follow = True
        self.dragging = False
        self.drag_dx = self.drag_dy = 0.0
        self.menu_until = 0.0
        self.food = None                # cibo: dict con kind, mon, x, y, vy, state, bites
        self.particles = []             # cuoricini, briciole, scintille
        self.happy_until = 0.0
        self.rub, self.last_rub, self.last_heart = 0.0, 0.0, 0.0
        self.fed_at = now
        self.portal = None              # viaggio in corso: src, dst, dir, T, exit_x
        self.portal_ready = 0.0
        self.portal_style = PORTAL_STYLE
        self.lecture = None             # lavagna della spiegazione in corso
        self.boards = []                # lavagne ancora visibili (anche mentre sprofondano)
        self.wig_t = 0.0
        self.last_q = 0.0
        self.say_text, self.say_until = None, 0.0   # fumetto (None = finché non cambia)
        self.work_id = None             # richiesta "trasforma" in corso
        self.inbox = queue.Queue()
        threading.Thread(target=serve_inline, args=(self.inbox,), daemon=True).start()

        # --- carattere, memoria, consigli ---
        self.brain = Brain()
        self.think_q = queue.Queue()    # risultati delle chiamate a Claude (chat/consiglio/idee)
        self.thinking = None            # tipo di pensiero in corso, o None
        self.bubble = None              # fumetto corrente (chat / consiglio / bisogno)
        self.last_fb_cat = None
        self.talk_win = self.talk_ent = None
        self.chat_hist, self.chat_at = [], 0.0  # battute recenti: ("Utente"|"Tu", testo)
        self.know = Knowledge()                 # progetti e memorie di Claude Code (lettura)
        self.sessions = Sessions(SESSIONS_PATH)  # le vostre chiacchierate
        self.session_id = None                  # chiacchierata in corso
        self.diary_due = set()                  # chiacchierate da riassumere nel diario
        self.diary_sid = None                   # quella che sta riassumendo adesso
        self.diary_done = {}                    # battute già riassunte, per chiacchierata
        self.work_since = now          # inizio della sessione di lavoro corrente
        self.app = ""
        self.last_mood_save = now
        self.advice_today, self.advice_day = 0, date.today().isoformat()
        self.next_spontaneous = now + random.uniform(60, 150)
        self.last_need = 0.0
        self.chores = ChoreLog(CHORES_PATH)
        self.next_chore = now + CHORE_FIRST_S
        self.dev_found, self.dev_busy = None, False   # build vecchie (cercate in un thread)
        self.next_dev_scan = now + CHORE_FIRST_S
        self.next_update = now + 120     # controllo degli aggiornamenti (su GitHub)
        self.work_q = queue.Queue()     # risultati dei lavori lunghi (thread) -> (tipo, dati)
        # --- cose che osserva: PC, riunioni, sessioni di Claude Code, appunti ---
        self.next_sys, self.next_meet, self.next_watch = now + 20, now, now + 5
        self.last_ram_warn = 0.0
        self.meeting, self.meeting_since, self.meeting_call = False, now, False
        self.sys_status = None
        self.after_meeting = []         # avvisi rimandati a fine riunione
        self.claude_watch = pet_watch.ClaudeWatch(project_roots())
        self.clip = pet_watch.Clipboard()
        self.last_err_text = ""
        self.clip_win = None
        self.settings_win = None
        self.summon_until = 0.0         # corre da te anche se non muovi il mouse
        # --- promemoria, standup, comandi ---
        self.commands = pet_work.Commands(COMMANDS_PATH)
        self.standup_busy = False
        self.day_seen = date.today().isoformat()
        # --- giochi ---
        self.ball = None                # palla: mon, x, y, vx, vy, state, t_touch
        self.hide = None                # nascondino: dict con mon, T, x, t0
        self.mouse_hist = []            # ultime posizioni del cursore (per lanciare la palla)

        for m in self.mons:
            c = m.c
            c.tag_bind("pet", "<ButtonPress-1>", self.on_press)
            c.tag_bind("pet", "<Double-Button-1>", self.open_talk)
            c.tag_bind("food", "<ButtonPress-1>", self.on_food_press)
            c.bind("<ButtonRelease-1>", self.on_release)
            c.tag_bind("pet", "<ButtonPress-3>", self.on_menu)
            c.tag_bind("bubble", "<ButtonPress-1>", lambda e: self.bubble_skip_or_close())
            c.tag_bind("thumb_up", "<ButtonPress-1>", lambda e: self.on_thumb(True))
            c.tag_bind("thumb_down", "<ButtonPress-1>", lambda e: self.on_thumb(False))
            c.tag_bind("menu_talk", "<ButtonPress-1>", self.open_talk)
            c.tag_bind("menu_advice", "<ButtonPress-1>",
                       lambda e: (setattr(self, "menu_until", 0.0),
                                  self.give_advice(time.time(), spontaneous=False)))
            c.tag_bind("menu_propose", "<ButtonPress-1>",
                       lambda e: (setattr(self, "menu_until", 0.0),
                                  self.propose_improvements(time.time(), auto=False)))
            c.tag_bind("menu_forget", "<ButtonPress-1>", self.on_forget)
            c.tag_bind("menu_chores", "<ButtonPress-1>",
                       lambda e: (setattr(self, "menu_until", 0.0),
                                  self.check_chores(time.time(), manual=True)))
            c.tag_bind("menu_undo", "<ButtonPress-1>", self.undo_chores)
            c.tag_bind("menu_ball", "<ButtonPress-1>", self.toggle_ball)
            c.tag_bind("menu_hide", "<ButtonPress-1>", self.start_hide)
            c.tag_bind("menu_clip", "<ButtonPress-1>", self.open_clipboard)
            c.tag_bind("menu_standup", "<ButtonPress-1>",
                       lambda e: (setattr(self, "menu_until", 0.0), self.start_standup()))
            c.tag_bind("menu_pc", "<ButtonPress-1>", self.on_pc_info)
            c.tag_bind("ball", "<ButtonPress-1>", self.on_ball_press)
            c.tag_bind("menu_feed", "<ButtonPress-1>", self.give_food)
            c.tag_bind("menu_follow", "<ButtonPress-1>", self.toggle_follow)
            c.tag_bind("menu_portal", "<ButtonPress-1>", self.toggle_portal)
            c.tag_bind("menu_cape", "<ButtonPress-1>", self.toggle_cape)
            c.tag_bind("menu_power", "<ButtonPress-1>", self.cycle_power)
            c.tag_bind("menu_meeting", "<ButtonPress-1>", self.toggle_meeting_mode)
            c.tag_bind("menu_settings", "<ButtonPress-1>", self.open_settings)
            c.tag_bind("menu_update", "<ButtonPress-1>", self.check_update_now)
            c.tag_bind("menu_quit", "<ButtonPress-1>", lambda e: root.destroy())
        self.tick()

    # lo schermo su cui si trova la mascotte
    @property
    def wa(self):
        return self.mon.wa

    @property
    def c(self):
        return self.mon.c

    @property
    def ox(self):
        return self.mon.ox

    @property
    def oy(self):
        return self.mon.oy

    @property
    def plats(self):
        return self.mon.plats

    def monitor_at(self, x, y):
        for m in self.mons:
            if m.contains(x, y):
                return m
        return min(self.mons, key=lambda m: abs((m.full.left + m.full.right) / 2 - x)
                   + abs((m.full.top + m.full.bottom) / 2 - y))

    # ---- ciclo principale ------------------------------------------------------
    def tick(self):
        now = time.time()
        if now - self.last_refresh >= 0.1:
            self.refresh(now)
        m = cursor_pos()
        moved = abs(m[0] - self.mouse[0]) + abs(m[1] - self.mouse[1])
        if moved > 3:
            if now - self.last_move > BREAK_GAP_S:   # tornata l'attività dopo una pausa
                self.work_since = now
            self.last_move = now
        if math.hypot(m[0] - self.anchor[0], m[1] - self.anchor[1]) > 120:
            self.anchor, self.anchor_t = m, now
        self.mouse = m
        self.mouse_hist = (self.mouse_hist + [(now, m)])[-6:]
        while not self.inbox.empty():
            self.on_message(now, *self.inbox.get_nowait())
        while not self.think_q.empty():
            self.on_thought(now, *self.think_q.get_nowait())
        self.update_life(now)
        self.check_petting(now, moved)
        if not (now < self.menu_until and self.state in ("idle", "walk", "float")):
            getattr(self, "st_" + self.state)(now)   # col menu aperto resta ferma: le voci
        for b in self.boards:                        # restano sotto il cursore
            b.update(now)
        self.boards = [b for b in self.boards if b.alive]
        if not self.state.startswith("portal"):
            self.x = min(max(self.x, self.wa.left + MARGIN), self.wa.right - MARGIN)
        self.update_food(now)
        self.update_ball(now)
        self.update_portal(now)
        self.update_particles()
        self.draw(now)
        self.root.after(FRAME_MS, self.tick)

    def set_state(self, state, now):
        self.state, self.since = state, now

    def refresh(self, now):
        self.last_refresh = now
        wins = window_rects(self.pid)
        self.rects = {w[0]: w[1:] for w in wins}
        for m in self.mons:
            m.plats = platforms(wins, m.wa)
        h = self.stand[0] if self.stand else None
        if h and self.state in ("idle", "walk", "sleep", "hide"):
            r = self.rects.get(h)
            if r and self.stand_rect and (r[0], r[1]) != self.stand_rect:
                dx, dy = r[0] - self.stand_rect[0], r[1] - self.stand_rect[1]
                self.x += dx                # la finestra si è mossa: ci resta sopra
                self.y += dy
                self.tx += dx
                self.stand, self.stand_rect = (h, r[1]), (r[0], r[1])

    # ---- appoggio e cadute -----------------------------------------------------
    def plat_at(self, x, y, tol=2, mon=None):
        for p in (mon or self.mon).plats:
            if abs(p[1] - y) <= tol and p[2] <= x <= p[3]:
                return p
        return None

    def set_stand(self, p):
        self.stand = (p[0], p[1])
        r = self.rects.get(p[0])
        self.stand_rect = (r[0], r[1]) if r else None
        self.y = p[1]

    def supported(self, now):
        p = self.plat_at(self.x, self.y)
        if p:
            if (p[0], p[1]) != self.stand:
                self.set_stand(p)
            return True
        self.start_fall(now)
        return False

    def start_fall(self, now, hop=False):
        self.ignore = self.stand if hop else None
        self.vy = -6.0 if hop else 0.0
        self.stand, self.climb, self.hop_after = None, None, False
        self.fall_y0 = self.y
        self.chute = False
        self.set_state("fall", now)

    def st_fall(self, now):
        if not self.chute and self.vy > 0 and self.y - self.fall_y0 > CHUTE_DROP:
            self.chute = True                   # caduta lunga: si apre il paracadute
        if self.chute:
            self.vy = min(self.vy + GRAVITY * 0.3, CHUTE_VY)
            self.x += 1.1 * math.sin(now * 2.2)  # dondola scendendo
        else:
            self.vy = min(self.vy + GRAVITY, 24.0)
        ny = self.y + self.vy
        if self.vy > 0:
            land = None
            for p in self.plats:
                if ((p[0], p[1]) != self.ignore and p[2] <= self.x <= p[3]
                        and self.y <= p[1] <= ny and (land is None or p[1] < land[1])):
                    land = p
            if land is None and ny >= self.wa.bottom:
                land = self.plats[0]            # la taskbar c'è sempre
            if land:
                self.set_stand(land)
                if self.chute:                   # il paracadute si ripiega in uno sbuffo
                    for _ in range(8):
                        self.particles.append({"kind": "dust", "mon": self.mon,
                                               "x": self.x + random.uniform(-16, 16),
                                               "y": self.y - PET_H, "vx": random.uniform(-1, 1),
                                               "vy": random.uniform(-2, -0.3), "life": 14,
                                               "color": CHUTE_COL})
                self.ignore, self.vy, self.chute = None, 0.0, False
                self.set_state("idle", now)
                self.next_think = now + 0.35
                return
        self.y = ny

    # ---- decisioni -------------------------------------------------------------
    def following(self, now):
        if self.meeting or self.hide or self.ball:   # riunione o gioco: il cursore aspetta
            return False
        return now < self.summon_until or (self.follow and now - self.last_move < FOLLOW_S)

    def summon(self, now, secs=8.0):
        """Corre dove sei tu (sullo schermo del cursore), anche se il mouse è fermo."""
        self.summon_until = now + secs
        if self.state in ("sleep", "heropose", "flex", "pushup"):
            self.set_state("idle", now)
        self.next_think = now

    def think(self, now):
        self.next_think = now + 0.4
        L = self.lecture
        if L:                                # c'è da spiegare: va alla lavagna
            ground = L.mon.wa.bottom
            if self.mon is L.mon and abs(self.y - ground) <= 2 and abs(self.x - L.spot_x) <= 6:
                self.x = L.spot_x
                self.wig_t = now             # arriva la parrucca
                return self.set_state("lecture", now)
            if (self.mon is not L.mon or abs(self.y - ground) > 2
                    or abs(self.x - L.spot_x) > 250):
                return self.start_portal(now, L.mon, L.mon.plats[0], L.spot_x)
            return self.go(now, L.spot_x)
        if self.talk_win is not None:        # state parlando: resta lì ad ascoltarti
            return
        H = self.hide
        if H:                                # nascondino: va al nascondiglio e si acquatta
            m, T = self.hide_spot(H)         # la finestra può essersi spostata
            if not m:
                self.hide = None
                return
            if T is not H["T"]:
                H["x"] = min(max(H["x"] + T[2] - H["T"][2], T[2] + MARGIN), T[3] - MARGIN)
                H["mon"], H["T"] = m, T
            if self.mon is H["mon"] and abs(self.y - T[1]) <= 2:
                if abs(self.x - H["x"]) <= 6:
                    self.bubble = None       # il fumetto la tradirebbe
                    return self.set_state("hide", now)
                return self.go(now, H["x"])  # già sul bordo giusto: a piedi (il portale la
                                             # fa uscire lontano dagli angoli, mai sul punto)
            if H.setdefault("portals", 0) >= 3:  # non riesce ad arrivarci: lascia perdere
                self.hide = None
                return self.set_bubble("chat", "Non trovo un buon nascondiglio... giochiamo dopo?")
            if now >= self.portal_ready:
                H["portals"] += 1
                return self.start_portal(now, H["mon"], H["T"], H["x"])
            return
        if self.meeting:                     # in riunione: si mette zitta nell'angolo
            T = self.mon.plats[0]
            return self.plan_to(now, T[3] - MARGIN, T[1], self.mon)
        f = self.food
        if f and f["state"] == "rest":       # il cibo per terra ha la precedenza
            if (f["mon"] is self.mon and abs(f["y"] - self.y) <= 3
                    and abs(f["x"] - self.x) <= PET_W / 2 + 14):
                return self.start_eat(now)
            side = 1 if f["x"] >= self.x else -1
            return self.plan_to(now, f["x"], f["y"] - 1, f["mon"],
                                want_x=f["x"] - side * (PET_W / 2 + 6))
        if f and f["state"] == "carry":      # lo stai portando tu: lo insegue
            return self.plan_to_mouse(now)
        b = self.ball
        if b and b["state"] == "rest":       # palla ferma: la raggiunge e la calcia
            if (b["mon"] is self.mon and abs(b["y"] - self.y) <= 3
                    and abs(b["x"] - self.x) <= PET_W / 2 + 12):
                return self.kick_ball(now)
            side = 1 if b["x"] >= self.x else -1
            return self.plan_to(now, b["x"], b["y"] - 1, b["mon"],
                                want_x=b["x"] - side * (PET_W / 2 + 4))
        if self.following(now):
            self.plan_to_mouse(now)
        else:
            self.wander(now)

    def go(self, now, tx, climb=None, hop=False):
        self.tx, self.climb, self.hop_after = tx, climb, hop
        self.set_state("walk", now)          # se è già lì, st_walk conclude subito

    def cursor_on_pet(self):
        mx, my = self.mouse
        return (abs(mx - self.x) <= PET_W / 2 + P and self.y - PET_H - 4 <= my <= self.y + 2)

    def plan_to_mouse(self, now):
        if self.cursor_on_pet():             # ce l'hai già addosso: resta ferma
            if self.state == "walk":
                self.set_state("idle", now)
            return
        self.plan_to(now, *self.mouse, self.monitor_at(*self.mouse), hang_ok=True)

    def plan_to(self, now, mx, my, tm, want_x=None, hang_ok=False):
        """Raggiunge la superficie sotto al punto (mx, my) dello schermo tm:
        cammina, sale, salta giù, o apre un portale se è su un altro schermo o lontano."""
        cur = self.plat_at(self.x, self.y)
        if cur is None:
            return
        wa = tm.wa
        mx = min(max(mx, wa.left), wa.right)
        my = min(max(my, wa.top), wa.bottom)
        # la superficie "sotto" al punto (40 px di tolleranza per la barra del titolo)
        cands = [p for p in tm.plats if p[2] <= mx <= p[3] and p[1] >= my - 40]
        if not cands:
            return
        T = min(cands, key=lambda p: p[1])
        tx = min(max(mx if want_x is None else want_x, T[2] + MARGIN), T[3] - MARGIN)
        other = tm is not self.mon
        if other or math.hypot(tx - self.x, T[1] - self.y) > PORTAL_DIST:
            if now >= self.portal_ready:
                return self.start_portal(now, tm, T, tx)
            if other:                        # il portale si sta ricaricando: aspetta
                if self.state == "walk":
                    self.set_state("idle", now)
                return
        if (hang_ok and abs(T[1] - self.y) <= 2 and T[1] - my > 200 and abs(self.x - mx) < 40
                and now - self.anchor_t > 1.2):
            self.start_hang(now)             # cursore fermo in alto: vola da lui
        elif abs(T[1] - self.y) <= 2:
            self.go(now, tx)
        elif T[1] > self.y:                  # più in basso: salta giù sotto al cursore
            self.go(now, min(max(tx, cur[2] + P), cur[3] - P), hop=True)
        else:                                # più in alto: super potere
            lo, hi = max(T[2], cur[2]) + MARGIN, min(T[3], cur[3]) - MARGIN
            if lo <= hi:
                self.go(now, min(max(tx, lo), hi), climb=T)
            else:                            # irraggiungibile da qui: scende e riprova
                self.go(now, self.x, hop=True)

    def wander(self, now):
        cur = self.plat_at(self.x, self.y)
        if cur is None:
            return
        if now >= self.next_activity and random.random() < 0.6:
            self.next_activity = now + random.uniform(ACTIVITY_MIN, ACTIVITY_MIN * 3)
            return self.start_activity(now, cur)
        r = random.random()
        others = [m for m in self.mons if m is not self.mon]
        if r >= 0.975 and others and now >= self.portal_ready:   # gita su un altro schermo
            m = random.choice(others)
            T = m.plats[0]
            return self.start_portal(now, m, T, random.uniform(T[2] + MARGIN, T[3] - MARGIN))
        if 0.35 <= r < 0.72:
            self.go(now, random.uniform(cur[2] + MARGIN, cur[3] - MARGIN))
            return
        if 0.72 <= r < 0.92:
            ups = [p for p in self.plats if self.y - 650 < p[1] < self.y - PET_H
                   and min(p[3], cur[3]) - max(p[2], cur[2]) > 2 * MARGIN]
            if ups:
                T = random.choice(ups)
                lo, hi = max(T[2], cur[2]) + MARGIN, min(T[3], cur[3]) - MARGIN
                self.go(now, random.uniform(lo, hi), climb=T)
                return
        if r >= 0.92 and cur[0] is not None:
            self.go(now, self.x, hop=True)
            return
        self.set_state("idle", now)
        self.next_think = now + random.uniform(1.5, 4.0)

    # ---- stati a terra ---------------------------------------------------------
    def st_idle(self, now):
        if not self.supported(now):
            return
        if (now - self.last_move > SLEEP_S and now - self.since > 2 and not self.food
                and not self.ball and not self.hide):  # mentre gioca resta sveglia
            self.set_state("sleep", now)
        elif now >= self.next_think:
            self.think(now)

    def st_sleep(self, now):
        if self.supported(now) and now - self.last_move < 1.0:
            self.set_state("idle", now)      # svegliata dal mouse
            self.next_think = now + 0.6

    def st_walk(self, now):
        if not self.supported(now):
            return
        if self.following(now) and now >= self.next_think:
            self.think(now)                  # ripianifica mentre il mouse si muove
            if self.state != "walk":
                return
        d = self.tx - self.x
        speed = RUN if abs(d) > 280 else WALK
        if abs(d) > speed:
            self.x += speed if d > 0 else -speed
            self.anim += speed
        elif self.climb:
            self.x = self.tx
            self.start_climb(now)
        elif self.hop_after:
            self.x = self.tx
            self.start_fall(now, hop=True)
        else:
            self.x = self.tx
            self.set_state("idle", now)
            busy = self.following(now) or self.food is not None or self.lecture is not None
            self.next_think = now + (0.3 if busy else random.uniform(1.0, 3.5))

    # ---- richieste da claude_inline --------------------------------------------
    def on_message(self, now, cid, msg):
        if msg.get("t") == "start":
            if msg.get("mode") == "ask":
                self.begin_lecture(now, cid, msg)
            else:
                self.work_id = cid
                self.say("Ci lavoro…", None)
        elif msg.get("t") == "answer":
            L = self.lecture
            if L and L.cid == cid:
                L.answer(msg.get("text") or "", bool(msg.get("error")))
            elif cid == self.work_id:
                self.work_id = None
                if msg.get("error"):
                    self.say("Ops, non ci sono riuscito", now + 2.5)
                else:
                    self.say("Fatto!", now + 1.6)
                    for _ in range(3):
                        self.add_heart()

    def say(self, text, until):
        self.say_text, self.say_until = text, until

    def begin_lecture(self, now, cid, msg):
        if self.lecture:
            self.lecture.close()
        mon = self.monitor_at(*self.mouse)   # la lavagna compare dove sei tu
        self.lecture = Blackboard(self, mon, cid, msg.get("q") or "", msg.get("ctx"),
                                  msg.get("hwnd"), random.choice(LECTURE_STYLES)
                                  if LECTURE == "random" else LECTURE)
        self.boards.append(self.lecture)
        if (MUSIC and self.lecture.style == "presenter"
                and not pet_watch.mic_users()):   # in call: niente musica
            play_air(self.lecture)
        self.hide = None                     # anche dal nascondiglio
        if self.state in ("rise", "float"):
            self.start_fall(now)             # molla tutto e scende
        elif self.state in ("sleep", "happy", "eat", "lecture", "walk", "hide"):
            self.set_state("idle", now)
        self.next_think = now
        return self.lecture

    def end_lecture(self, board):
        now = time.time()
        if self.lecture is board:
            self.lecture = None
        if self.state == "lecture":
            for _ in range(10 if board.style == "professor" else 0):   # la parrucca vola via
                self.particles.append({"kind": "dust", "mon": self.mon,
                                       "x": self.x + random.uniform(-25, 25),
                                       "y": self.y - PET_H - random.uniform(0, 10),
                                       "vx": random.uniform(-1.2, 1.2),
                                       "vy": random.uniform(-2.5, -0.5), "life": 16,
                                       "color": WIG})
            self.set_state("idle", now)
            self.next_think = now + 1.0

    def st_lecture(self, now):
        L = self.lecture
        if not L:
            self.set_state("idle", now)
        elif L.phase in ("rise", "think") and now - self.last_q > 0.9:
            self.last_q = now                # punti interrogativi mentre ci pensa
            self.particles.append({"kind": "qmark", "mon": self.mon,
                                   "x": self.x + random.uniform(-18, 6), "y": self.y - PET_H - 22,
                                   "vx": random.uniform(-0.3, 0.3), "vy": -0.9, "life": 28})

    # ---- portali ---------------------------------------------------------------
    def start_portal(self, now, tm, T, tx):
        """Apre un portale accanto a sé e uno a destinazione, sulla superficie T di tm."""
        cur = self.plat_at(self.x, self.y)
        if tm is self.mon:
            d = 1 if tx >= self.x else -1
        else:
            d = 1 if tm.wa.left + tm.wa.right >= self.wa.left + self.wa.right else -1
        if cur and not cur[2] + 20 <= self.x + d * PORTAL_OFF <= cur[3] - 20:
            d = -d                           # niente spazio da quella parte: l'altro lato
        lo, hi = T[2] + MARGIN + PORTAL_OFF, T[3] - MARGIN - PORTAL_OFF
        exit_x = min(max(tx, lo), hi) if lo <= hi else (T[2] + T[3]) / 2
        self.portal = {
            "dir": d, "exit_x": exit_x,
            "src": {"mon": self.mon, "x": self.x + d * PORTAL_OFF, "y": self.y,
                    "t_open": now, "t_close": None, "entry": True},
            "dst": {"mon": tm, "x": exit_x - d * PORTAL_OFF, "y": T[1],
                    "t_open": now, "t_close": None, "entry": False}}
        self.climb, self.hop_after = None, False
        self.set_state("portal_open", now)

    def st_portal_open(self, now):           # i due portali si aprono
        if now - self.since >= 0.45:
            self.set_state("portal_in", now)

    def st_portal_in(self, now):             # ci entra camminando
        pt = self.portal
        d, src = pt["dir"], pt["src"]
        self.x += d * WALK
        self.anim += WALK
        if d * (self.x - (src["x"] + d * HIDDEN)) >= 0:
            src["t_close"] = now
            dst = pt["dst"]
            self.mon = dst["mon"]            # passa dall'altra parte
            self.x, self.y = dst["x"] - d * HIDDEN, dst["y"]
            self.set_state("portal_out", now)

    def st_portal_out(self, now):            # esce dal portale di destinazione
        pt = self.portal
        d = pt["dir"]
        self.x += d * WALK
        self.anim += WALK
        if d * (self.x - pt["exit_x"]) >= 0:
            self.x = pt["exit_x"]
            pt["dst"]["t_close"] = now
            self.portal_ready = now + PORTAL_COOLDOWN
            p = self.plat_at(self.x, self.y)
            if p:
                self.set_stand(p)
                self.set_state("idle", now)
                self.next_think = now + 0.4
            else:
                self.start_fall(now)         # il bordo d'arrivo è sparito nel frattempo

    def close_portal(self, now):
        if self.portal:
            for end in (self.portal["src"], self.portal["dst"]):
                if end["t_close"] is None:
                    end["t_close"] = now

    @staticmethod
    def portal_scale(end, now):
        s = min(1.0, (now - end["t_open"]) / 0.45)
        if end["t_close"] is not None:
            s *= max(0.0, 1.0 - (now - end["t_close"]) / 0.35)
        return s

    def update_portal(self, now):
        pt = self.portal
        if not pt:
            return
        ends = (pt["src"], pt["dst"])
        if all(e["t_close"] is not None and now - e["t_close"] > 0.35 for e in ends):
            self.portal = None
            return
        if self.portal_style != "sparks":
            return
        for end in ends:                     # scintille che schizzano dall'anello
            s = self.portal_scale(end, now)
            if s < 0.4:
                continue
            for _ in range(2):
                a = random.uniform(0, 2 * math.pi)
                ca, sa = math.cos(a), math.sin(a)
                self.particles.append({
                    "kind": "spark", "mon": end["mon"],
                    "x": end["x"] + PORTAL_RX * s * ca,
                    "y": end["y"] - PORTAL_RY + PORTAL_RY * s * sa,
                    "vx": -sa * 2.5 + ca * 0.8, "vy": ca * 2.5 + sa * 0.8,
                    "life": 10, "color": random.choice(SPARKS)})

    # ---- attività da supereroe -------------------------------------------------
    def start_activity(self, now, cur):
        wide = cur[3] - cur[2] > 6 * MARGIN
        act = random.choice(["heropose", "pushup", "flex"] + (["fly"] if wide else []))
        if act == "fly":
            self.fly_y = cur[1]
            lo, hi = cur[2] + MARGIN, cur[3] - MARGIN
            self.tx = lo if self.x > (lo + hi) / 2 else hi    # vola verso l'altro capo
            self.act_dir = 1 if self.tx >= self.x else -1
        self.set_state(act, now)

    def busy_elsewhere(self, now):
        """Un'attività si interrompe appena torni a muovere il mouse o c'è da fare."""
        return self.following(now) or self.food is not None or self.lecture is not None

    def st_heropose(self, now):
        if not self.supported(now):
            return
        if self.busy_elsewhere(now) or now - self.since > 3.6:
            self.set_state("idle", now)
            self.next_think = now + 0.3
        elif random.random() < 0.08:
            self.particles.append({"kind": "spark", "mon": self.mon,
                                   "x": self.x + 3 * P, "y": self.y - PET_H - 2,
                                   "vx": 0.4, "vy": -0.6, "life": 16, "color": STAR})

    def st_flex(self, now):
        if not self.supported(now):
            return
        if self.busy_elsewhere(now) or now - self.since > 3.0:
            self.set_state("idle", now)
            self.next_think = now + 0.3
        elif random.random() < 0.1:
            for sx in (-3 * P, 3 * P):
                self.particles.append({"kind": "spark", "mon": self.mon,
                                       "x": self.x + sx, "y": self.y - PET_H, "vx": 0,
                                       "vy": -0.5, "life": 14, "color": STAR})

    def st_pushup(self, now):
        if not self.supported(now):
            return
        if self.busy_elsewhere(now) or now - self.since > 3.6:
            self.set_state("idle", now)
            self.next_think = now + 0.3

    def st_fly(self, now):
        if self.busy_elsewhere(now):
            return self.start_fall(now)
        hover = self.fly_y - 30
        if self.y > hover:
            self.y = max(hover, self.y - 6)      # prima si alza in volo
            return
        d = self.tx - self.x
        speed = RUN * 1.7
        if abs(d) > speed:
            self.x += speed if d > 0 else -speed
            self.anim += speed
        else:
            self.x, self.y = self.tx, self.fly_y
            p = self.plat_at(self.x, self.y)
            if p:
                self.set_stand(p)
                self.set_state("idle", now)
                self.next_think = now + 0.5
            else:
                self.start_fall(now)

    # ---- arrampicate -----------------------------------------------------------
    # ---- super poteri: sale sui bordi e fluttua accanto al cursore ----------------
    def start_power(self, now, goal, anchor_y):
        self.power = (random.choice(POWERS) if self.power_pref == "random"
                      else self.power_pref)
        self.rise_goal = goal
        self.anchor_pt = (self.x, anchor_y)  # la ragnatela si attacca qui
        self.float_side = 1 if self.x >= self.mouse[0] else -1
        self.stand = None
        self.set_state("rise", now)

    def start_climb(self, now):              # sale sul bordo della finestra
        self.start_power(now, self.climb[1], self.climb[1])

    def climb_valid(self):
        p = self.plat_at(self.x, self.climb[1], tol=0)
        return p is not None and p[0] == self.climb[0]

    def start_hang(self, now):               # cursore fermo in alto: vola da lui
        self.climb = None
        self.start_power(now, self.float_target()[1], self.wa.top)

    def hang_wanted(self, now):
        return self.following(now) and self.monitor_at(*self.mouse) is self.mon

    def float_target(self):
        """Accanto al cursore, dal lato da cui è arrivata, senza coprirlo."""
        mx, my = self.mouse
        tx = mx + self.float_side * (PET_W / 2 + 16)
        ty = my + PET_H / 2 + 6
        return (min(max(tx, self.wa.left + MARGIN), self.wa.right - MARGIN),
                min(max(ty, self.wa.top + PET_H + 10), self.wa.bottom))

    def st_rise(self, now):                  # carica il potere e sale
        if self.climb is not None:
            if not self.climb_valid():
                return self.start_fall(now)  # il bordo è sparito
        elif not self.hang_wanted(now):
            return self.start_fall(now)      # il mouse se n'è andato
        else:
            tx, self.rise_goal = self.float_target()
            self.x += (tx - self.x) * 0.08
        if now - self.since < 0.35:          # spara la ragnatela / accende i razzi / si concentra
            return
        speed = CLIMB * {"web": 1.6, "rockets": 1.3}.get(self.power, 1.0)
        self.y = max(self.rise_goal, self.y - speed)
        self.anim += speed
        self.power_fx()
        if self.y <= self.rise_goal:
            if self.climb is not None:       # arrivata sul bordo
                self.set_stand(self.climb)
                self.climb = None
                self.set_state("idle", now)
                self.next_think = now + 0.5
            else:
                self.set_state("float", now)

    def st_float(self, now):                 # fluttua accanto al cursore e lo segue
        if not self.hang_wanted(now) or (self.food and self.food["state"] == "rest"):
            return self.start_fall(now)      # il mouse è fermo o altrove: si lascia cadere
        tx, ty = self.float_target()
        ty += 3 * math.sin(now * 3)
        self.x += (tx - self.x) * 0.18
        self.y += (ty - self.y) * 0.18
        self.anim += 1
        if self.power == "web" and abs(self.anchor_pt[0] - self.x) > 160:
            self.anchor_pt = (self.x, self.wa.top)   # nuova ragnatela più vicina
        self.power_fx()

    def power_fx(self):
        if self.power == "rockets":          # scarico dei razzi verso il basso
            for hx in (self.x - 4 * P, self.x + 4 * P, self.x):
                self.particles.append({"kind": "spark", "mon": self.mon,
                                       "x": hx + random.uniform(-2, 2), "y": self.y + 4,
                                       "vx": random.uniform(-0.6, 0.6),
                                       "vy": random.uniform(1.5, 3.5), "life": 9,
                                       "color": random.choice(FLAME)})
        elif self.power == "telekinesis" and random.random() < 0.5:   # pulviscolo che sale
            self.particles.append({"kind": "tele", "mon": self.mon,
                                   "x": self.x + random.uniform(-32, 32),
                                   "y": self.y - random.uniform(0, PET_H),
                                   "vx": random.uniform(-0.3, 0.3),
                                   "vy": random.uniform(-1.6, -0.6), "life": 26,
                                   "color": random.choice((TELE, TELE_SOFT))})

    # ---- carezze ---------------------------------------------------------------
    def check_petting(self, now, moved):
        """Il cursore che si muove sopra di lei, senza clic, sono carezze."""
        if (moved > 0 and not self.dragging and self.cursor_on_pet()
                and self.state in ("idle", "walk", "sleep", "happy")):
            self.rub = min(self.rub + moved, RUB_PX * 1.5)  # tetto: smette presto dopo le carezze
            self.last_rub = now
        else:
            self.rub = max(0.0, self.rub - 6)
        if self.rub > RUB_PX:
            if self.state != "happy":
                self.set_state("happy", now)
            self.happy_until = now + 1.0
            if now - self.last_heart > 0.28:
                self.last_heart = now
                self.add_heart()
                self.brain.bump_mood(0.012)      # le coccole la tirano su

    def add_heart(self):
        self.particles.append({"kind": "heart", "mon": self.mon,
                               "x": self.x + random.uniform(-14, 14),
                               "y": self.y - PET_H - 6, "vx": random.uniform(-0.4, 0.4),
                               "vy": -1.4, "life": 40})

    def st_happy(self, now):
        if self.supported(now) and now > self.happy_until:
            self.set_state("idle", now)
            self.next_think = now + 0.6

    # ---- cibo ------------------------------------------------------------------
    def give_food(self, _e):
        self.menu_until = 0.0
        mx, my = self.mouse
        self.food = {"kind": random.choice(("cookie", "apple")), "mon": self.monitor_at(mx, my),
                     "x": mx + 14, "y": my + 34, "vy": 0.0, "state": "carry",
                     "t0": time.time(), "bites": 0, "dx": 14, "dy": 34}

    def on_food_press(self, _e):
        f = self.food
        if f and f["state"] in ("rest", "fall"):
            mx, my = cursor_pos()
            f.update(state="drag", dx=f["x"] - mx, dy=f["y"] - my)
            if self.state == "eat":
                self.set_state("idle", time.time())

    def update_food(self, now):
        f = self.food
        if not f:
            return
        st = f["state"]
        if st in ("carry", "drag"):
            mx, my = self.mouse
            f["x"], f["y"] = mx + f["dx"], my + f["dy"]
            f["mon"] = self.monitor_at(mx, my)       # il cibo va dove va il cursore
            if st == "carry" and now - f["t0"] > 0.7 and now - self.last_move > 0.7:
                f.update(state="fall", vy=0.0)       # mouse fermo: lo lascia cadere
            elif st == "drag" and not user32.GetAsyncKeyState(0x01) & 0x8000:
                f.update(state="fall", vy=0.0)
        fm = f["mon"]
        if st == "fall":
            f["vy"] = min(f["vy"] + GRAVITY, 24.0)
            ny = f["y"] + f["vy"]
            land = [p for p in fm.plats if p[2] <= f["x"] <= p[3] and f["y"] <= p[1] <= ny]
            if land or ny >= fm.wa.bottom:
                f.update(y=min(p[1] for p in land) if land else fm.wa.bottom,
                         state="rest", vy=0.0)
                self.next_think = now        # lei se ne accorge subito
            else:
                f["y"] = ny
        elif st == "rest" and self.plat_at(f["x"], f["y"], mon=fm) is None:
            f.update(state="fall", vy=0.0)           # il bordo sotto è sparito
        f["x"] = min(max(f["x"], fm.wa.left + 10), fm.wa.right - 10)

    def start_eat(self, now):
        self.set_state("eat", now)

    def st_eat(self, now):                   # tre morsi, briciole, poi felicità
        f = self.food
        if not self.supported(now):
            return
        if not f or f["state"] != "rest":
            self.set_state("idle", now)
            return
        bites = min(3, int((now - self.since + 0.1) / 0.6))
        while f["bites"] < bites:
            f["bites"] += 1
            for _ in range(5):
                self.particles.append({"kind": "crumb", "mon": self.mon, "x": f["x"],
                                       "y": f["y"] - 10, "vx": random.uniform(-1.5, 1.5),
                                       "vy": random.uniform(-3, -1), "life": 18,
                                       "color": COOKIE_EDGE if f["kind"] == "cookie" else APPLE})
        if now - self.since > 2.4:
            self.food = None
            self.fed_at = now
            self.brain.bump_mood(0.15)           # un pasto la rende felice
            self.set_state("happy", now)
            self.happy_until = now + 1.8
            for _ in range(4):
                self.add_heart()

    def hungry(self, now):
        return now - self.fed_at > HUNGRY_MIN * 60

    def update_particles(self):
        keep = []
        for pt in self.particles:
            pt["life"] -= 1
            if pt["life"] <= 0:
                continue
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            if pt["kind"] == "crumb":
                pt["vy"] += GRAVITY * 0.6
            elif pt["kind"] == "spark":
                pt["vy"] += 0.25
            elif pt["kind"] == "dust":
                pt["vy"] += 0.12
            keep.append(pt)
        self.particles = keep

    # ---- mouse sulla mascotte ----------------------------------------------------
    def on_press(self, _e):
        if self.state == "lecture":          # durante la lezione non si fa trascinare
            return
        now = time.time()
        if self.state == "hide" and self.hide:   # nascondino: trovata!
            return self.found_hiding(now)
        mx, my = cursor_pos()
        self.dragging = True
        self.drag_dx, self.drag_dy = self.x - mx, self.y - my
        self.close_portal(now)
        self.stand, self.climb, self.hop_after = None, None, False
        self.set_state("drag", now)

    def on_release(self, _e=None):
        if self.dragging:
            self.dragging = False
            self.start_fall(time.time())

    def st_drag(self, now):
        if not user32.GetAsyncKeyState(0x01) & 0x8000:   # rilascio perso: lascia cadere
            return self.on_release()
        mx, my = self.mouse
        nx, ny = mx + self.drag_dx, my + self.drag_dy
        self.mon = self.monitor_at(mx, my)   # trascinata su un altro schermo: ci resta
        self.anim += abs(nx - self.x)
        self.x = nx
        self.y = min(max(ny, self.wa.top + PET_H), self.wa.bottom)

    def on_menu(self, _e):
        self.menu_until = time.time() + 5

    def toggle_follow(self, _e):
        self.follow = not self.follow
        self.menu_until = time.time() + 2

    def toggle_portal(self, _e):
        self.portal_style = "ovals" if self.portal_style == "sparks" else "sparks"
        self.menu_until = time.time() + 2

    def toggle_cape(self, _e):
        self.cape_on = not self.cape_on
        self.menu_until = time.time() + 2

    def cycle_power(self, _e):
        order = ("random",) + POWERS
        self.power_pref = order[(order.index(self.power_pref) + 1) % len(order)]
        self.menu_until = time.time() + 2

    def on_forget(self, _e):
        self.menu_until = 0.0
        self.brain.forget_all()                  # anche il diario
        self.sessions.forget()                   # e le trascrizioni in pet_sessions/
        self.chat_hist.clear()
        self.session_id, self.diary_due, self.diary_done, self.diary_sid = None, set(), {}, None
        self.set_bubble("chat", "Ho dimenticato tutto. Piacere, come ti chiami?", cat=None)

    # ---- vita: umore, bisogni, consigli ----------------------------------------
    def working_min(self, now):
        return (now - self.work_since) / 60 if now - self.last_move < BREAK_GAP_S else 0

    def quiet(self):                         # momento buono per parlare da sola
        return (self.state in ("idle", "walk", "sleep", "happy") and not self.bubble
                and not self.thinking and not self.lecture and not self.dragging
                and self.talk_win is None and not self.meeting and not self.hide
                and not self.ball)

    def update_life(self, now):
        # l'umore scivola lentamente verso la quiete, più in fretta se la ignori da tempo
        ignored = now - max(self.last_move, self.fed_at) > 600
        target = 0.3 if ignored else 0.55
        self.brain.mood += (target - self.brain.mood) * 0.0006
        if now - self.last_mood_save > 60:
            self.last_mood_save = now
            self.brain.save()
        if now - self.last_refresh < 0.02:   # l'app attiva la leggo di rado (al refresh)
            a = active_app(self.pid)
            if a:
                self.app = a
        if self.bubble:
            self.update_bubble(now)
        if self.advice_day != date.today().isoformat():
            self.advice_day, self.advice_today = date.today().isoformat(), 0
        if now >= self.next_spontaneous and self.quiet():
            self.next_spontaneous = now + random.uniform(150, 360)
            self.spontaneous(now)
        if self.diary_due and not self.thinking and self.talk_win is None:
            self.write_diary()
        if now >= self.next_chore and self.quiet() and not self.following(now):
            self.next_chore = now + CHORE_EVERY_S
            self.check_chores(now)
        if FEAT_UPDATES and now >= self.next_update:
            self.next_update = now + UPDATE_EVERY_S
            threading.Thread(target=lambda: self.work_q.put(("update", pet_update.latest())),
                             daemon=True).start()
        while not COSTS.empty():             # quanto costano le sue chiamate a Claude
            pet_work.add_spending(self.brain.data, COSTS.get_nowait())
            self.brain.save()
        while not self.work_q.empty():
            self.on_work(now, *self.work_q.get_nowait())
        if now >= self.next_meet:
            self.next_meet = now + 2
            self.check_meeting(now)
        if now >= self.next_sys:
            self.next_sys = now + 60
            self.check_system(now)
        if now >= self.next_watch:
            self.next_watch = now + 3
            if FEAT_SESSIONS:
                for kind, cwd in self.claude_watch.poll(now):
                    self.notify_session(now, kind, self.know.name_of(cwd))
            text = self.clip.poll() if FEAT_CLIP or FEAT_ERRORS else None
            if not FEAT_CLIP:
                self.clip.items.clear()      # niente cronologia: serve solo per gli errori
            if text and FEAT_ERRORS:
                self.on_copied(now, text)
        self.check_reminders(now)
        self.check_day(now)
        if (now >= self.next_dev_scan and (FEAT_DEV or FEAT_M2) and not self.dev_busy
                and not self.following(now)):
            self.next_dev_scan = now + DEV_SCAN_S
            self.scan_dev()

    # ---- faccende: riordino del desktop e file vecchi ---------------------------
    def check_chores(self, now, manual=False):
        """Dà un'occhiata a Desktop e Download e, se c'è da sistemare, te lo propone."""
        desk, down = known_folder("desktop"), known_folder("downloads")
        snooze = self.brain.data.setdefault("chores_snooze", {})
        dev = self.dev_found or {}
        plans = (("desktop", pet_chores.desktop_plan(desk)),
                 ("old", pet_chores.old_plan([desk, down])),
                 ("dev", dev.get("dev")), ("m2", dev.get("m2")))
        enabled = {"desktop": FEAT_DESKTOP, "old": FEAT_OLD, "dev": FEAT_DEV, "m2": FEAT_M2}
        for kind, moves in plans:
            if not moves or (not manual and (not enabled[kind]   # da sola: solo quelle accese
                                             or now - snooze.get(kind, 0) < CHORE_SNOOZE_S)):
                continue
            n, size = len(moves), size_label(sum(m[2] for m in moves))
            names = ", ".join(m[0].name for m in moves[:3]) + (", ..." if n > 3 else "")
            if kind == "desktop":
                months = sorted({m[1].parent.name for m in moves})
                text = (f"Sul desktop ci sono {n} file sparsi ({names}). Li metto in "
                        f"{len(months)} cartelle per mese, da {months[0]} a {months[-1]}?")
            elif kind == "dev":
                big = sorted(moves, key=lambda m: -m[2])[:3]
                names = ", ".join(f"{m[0].parent.name}\\{m[0].name}" for m in big)
                text = (f"Ci sono {n} cartelle di build di progetti fermi da 2 mesi: {size} "
                        f"da liberare ({names}...). Le elimino? Si rigenerano con npm install / mvn.")
            elif kind == "m2":
                text = (f"Nella cache di Maven (.m2) ci sono {n} versioni di librerie non usate "
                        f"da 6 mesi: {size}. Le elimino? Se servono, Maven le riscarica.")
            else:
                text = (f"Ho trovato {n} file non usati da 6 mesi fra Desktop e Download "
                        f"({size}: {names}). Li sposto nelle cartelle «Da rivedere»?")
            self.set_bubble("ask", text, thumbs=True)
            self.bubble["chore"] = (kind, moves)
            return
        if manual and self.dev_found is None:
            if not self.dev_busy:
                self.scan_dev()
            self.set_bubble("chat", "Desktop e Download sono in ordine! Ora cerco build vecchie "
                                    "nei progetti: ci metto un paio di minuti, poi ti dico.")
        elif manual:
            self.set_bubble("chat", "Ho controllato: è tutto in ordine!")

    def scan_dev(self):
        """Cerca (in un thread: ci vuole qualche minuto) build vecchie e cache Maven."""
        self.dev_busy = True
        paths = list(self.know.projects.values())

        def worker():
            self.work_q.put(("dev", {"dev": pet_chores.dev_plan(paths),
                                     "m2": pet_chores.m2_plan()}))
        threading.Thread(target=worker, daemon=True).start()

    def do_chore(self, kind, moves, yes):
        if not yes:
            self.brain.data.setdefault("chores_snooze", {})[kind] = time.time()
            self.brain.save()
            return self.set_bubble("chat", "Va bene, lascio tutto com'è.")
        if kind in ("dev", "m2"):            # eliminazione vera: niente "Annulla" possibile
            self.dev_found[kind] = []
            self.say("Faccio spazio…", None)

            def worker():
                self.work_q.put(("deleted", (kind, *pet_chores.delete_dirs(moves))))
            threading.Thread(target=worker, daemon=True).start()
            return self.set_bubble("chat", "Ci penso io, ci vorrà un po'.")
        done, failed = pet_chores.apply(moves)
        if done:
            self.chores.add(kind, done)
        text = f"Fatto! Ho spostato {len(done)} file."
        if failed:
            text += f" {failed} non li ho potuti toccare (forse sono aperti)."
        if done:
            text += " Se cambi idea: menu > Annulla pulizie."
        self.set_bubble("chat", text)

    def undo_chores(self, _e=None):
        self.menu_until = 0.0
        last = self.chores.pop()
        if not last:
            return self.set_bubble("chat", "Non ho pulizie da annullare.")
        back, failed = pet_chores.undo(last["moves"])
        text = f"Rimesso a posto: {back} file tornati dov'erano (pulizie del {last['t']})."
        if failed:
            text += f" {failed} non li ho trovati più."
        self.set_bubble("chat", text)

    # ---- lavori lunghi finiti in un thread ------------------------------------------
    def on_work(self, now, kind, data):
        if kind == "dev":
            self.dev_found, self.dev_busy = data, False
        elif kind == "deleted":
            what, freed, failed = data
            self.say(None, 0)
            text = f"Fatto! Ho liberato {size_label(freed)}."
            if failed:
                text += f" {failed} cartelle non sono riuscita a toglierle (file in uso?)."
            self.set_bubble("chat", text)
        elif kind == "standup":
            board, text, err, pending = data
            self.standup_busy = False
            if pending:
                text = (text or "") + "\n\n**In sospeso**\n" + "\n".join("- " + p for p in pending)
            board.answer(text or "Non ho trovato niente di ieri da raccontare.", bool(err) and not pending)
        elif kind == "explain":
            board, text, err = data
            board.answer(text or ("Non sono riuscita a capirlo: " + (err or "")), bool(err))
        elif kind == "update":
            self.offer_update(now, data)
        elif kind == "update_now":
            self.offer_update(now, data, manual=True)

    # ---- aggiornamenti --------------------------------------------------------------
    def check_update_now(self, _e=None):
        """Chiesto da te (chat o menu): controlla subito, anche le versioni a cui hai detto no."""
        self.menu_until = 0.0
        self.set_bubble("chat", "Controllo se c'è una versione nuova...")
        threading.Thread(target=lambda: self.work_q.put(("update_now", pet_update.latest())),
                         daemon=True).start()

    def offer_update(self, now, tag, manual=False):
        """È uscita una versione nuova: chiede se installarla (da sola, una volta per versione)."""
        if manual and not tag:
            return self.set_bubble("chat", "Non riesco a controllare adesso: riprova più tardi.")
        if manual and not pet_update.is_newer(tag):
            return self.set_bubble("chat", "Sono già all'ultima versione "
                                           f"({pet_update.__version__}).")
        if not tag or not pet_update.is_newer(tag) or (
                not manual and self.brain.data.get("update_skip") == tag):
            return
        if not manual and not self.quiet():  # sta facendo altro: riprova fra un'ora
            self.next_update = now + 3600
            return
        version = tag.lstrip("v")
        if not pet_update.installed():       # gira dai sorgenti: basta dirlo
            self.brain.data["update_skip"] = tag
            self.brain.save()
            return self.set_bubble("chat", f"È uscita la versione {version}! La trovi su "
                                           f"github.com/{pet_update.REPO}")
        self.set_bubble("ask", f"È uscita la versione {version}! La installo? Mi chiudo un "
                               "attimo e torno da sola.", thumbs=True)
        self.bubble["update"] = tag

    def do_update(self, tag, yes):
        if not yes:
            self.brain.data["update_skip"] = tag
            self.brain.save()
            return self.set_bubble("chat", "Va bene, te lo richiedo alla prossima versione.")
        running = ["hoppy.pet"] + [m for m in ("hoppy.inline", "hoppy.popup")
                                   if pet_config.is_running(m)]
        pet_update.start(tag, running, clean_env())
        pet_config.request_quit()            # anche popup e inline si chiudono
        self.brain.save()
        self.set_bubble("chat", "Mi aggiorno! Torno fra un minuto.")
        self.root.after(1500, self.root.destroy)

    # ---- guardiano della RAM (memoria che cresce con giorni di accensione) ---------------
    def check_system(self, now):
        s = self.sys_status = pet_watch.system_status()
        why = []
        if s["uptime_h"] >= RAM_UPTIME_H:
            why.append(f"il PC è acceso da {int(s['uptime_h'])} ore")
        if s["commit_pct"] >= RAM_COMMIT_PCT:
            why.append(f"la memoria impegnata è al {s['commit_pct']:.0f}%")
        if s["nonpaged_gb"] >= RAM_NONPAGED_GB:
            why.append(f"la memoria del kernel è a {s['nonpaged_gb']:.1f} GB")
        urgent = s["commit_pct"] >= 92
        if not why or not FEAT_RAM or self.meeting or now - self.last_ram_warn < (1800 if urgent else RAM_REPEAT_S):
            return
        self.last_ram_warn = now
        self.summon(now)
        self.set_bubble("need", "Attenzione: " + " e ".join(why) + ". Un riavvio libera "
                        "la memoria: " + ("riavvia appena puoi!" if urgent
                                                 else "a fine giornata riavviamo?"))

    def on_pc_info(self, _e=None):
        self.menu_until = 0.0
        s = self.sys_status or pet_watch.system_status()
        self.set_bubble("chat", f"PC acceso da {s['uptime_h']:.1f} ore. Memoria impegnata "
                        f"{s['commit_gb']:.0f} su {s['limit_gb']:.0f} GB ({s['commit_pct']:.0f}%), "
                        f"memoria del kernel {s['nonpaged_gb']:.1f} GB. Io questo mese ho speso "
                        + pet_work.spending_label(self.brain.data) + " di credito.")

    # ---- riunioni ----------------------------------------------------------------------
    # ---- impostazioni ------------------------------------------------------------------
    def open_settings(self, _e=None):
        self.menu_until = 0.0
        if self.settings_win is not None and self.settings_win.win.winfo_exists():
            return self.settings_win.win.lift()
        self.settings_win = pet_settings.SettingsWindow(self.root, pet_config.load(),
                                                        self.on_settings_saved, self.open_wizard)

    def open_wizard(self):
        cfg = pet_config.load()
        pet_settings.Wizard(self.root, cfg, self.on_settings_saved)

    def on_settings_saved(self, cfg):
        """Salva, applica subito quello che si può e, se serve, riavvia la mascotte."""
        old = pet_config.load()
        pet_config.save(cfg)
        apply_config(cfg)
        self.cape_on, self.power_pref, self.portal_style = CAPE, POWER, PORTAL_STYLE
        if not MEETING_MODE:
            self.meeting_call = False        # spegnendola a metà call: niente "Fine call!"
        self.check_meeting(time.time())
        if any(old[s.key] != cfg[s.key] for s in pet_config.SETTINGS if s.restart):
            self.set_bubble("chat", "Mi riavvio per le nuove impostazioni...")
            pet_config.restart_pet(clean_env())
            self.root.after(1200, self.root.destroy)
        else:
            self.set_bubble("chat", "Impostazioni salvate!")

    def toggle_meeting_mode(self, _e):
        cfg = pet_config.load()
        cfg["meeting"] = not MEETING_MODE
        self.on_settings_saved(cfg)
        self.menu_until = time.time() + 2

    def check_meeting(self, now):
        if not MEETING_MODE:                 # disattivata dal menu o dalle Impostazioni
            call, m = False, False
        else:
            call = bool(pet_watch.mic_users())
            m = call or pet_watch.fullscreen_state() in (2, 3, 4)
        if m == self.meeting:
            self.meeting_call = self.meeting_call or call
            return
        self.meeting = m
        if m:                                # entra in riunione: zitta e nell'angolo
            self.meeting_since, self.meeting_call = now, call
            if self.bubble and self.bubble["kind"] != "remind":
                self.bubble = None
            if self.state in ("rise", "float"):
                self.start_fall(now)
            self.next_think = now
            return
        queued, self.after_meeting = self.after_meeting, []
        for kind, name in queued:            # quello che è successo mentre eri in call
            self.notify_session(now, kind, name)
        if queued:
            return
        if FEAT_REACTIONS and self.meeting_call and now - self.meeting_since >= 300:   # fine call
            late = datetime.now().hour * 60 + datetime.now().minute >= 17 * 60 + 30
            self.set_bubble("need", "Fine call! Ultima della giornata?" if late
                            else "Fine call! Com'è andata?")
            self.set_state("happy", now)
            self.happy_until = now + 1.5
            for _ in range(3):
                self.add_heart()

    # ---- sessioni di Claude Code -------------------------------------------------------
    def notify_session(self, now, kind, name):
        if self.meeting:
            if (kind, name) not in self.after_meeting:
                self.after_meeting.append((kind, name))
            return
        text = (f"«{name}» ha finito!" if kind == "done"
                else f"«{name}» forse aspetta un tuo permesso.")
        self.summon(now)
        if self.bubble and (self.bubble["kind"] in ("ask", "remind", "wait")
                            or self.talk_win is not None):
            self.say(text, now + 6)          # non copre una domanda o la chat in corso
        else:
            self.set_bubble("need", text)

    # ---- appunti ed errori copiati ------------------------------------------------------
    def on_copied(self, now, text):
        if (not pet_watch.looks_like_error(text) or text == self.last_err_text
                or self.meeting or self.lecture or self.talk_win is not None
                or (self.bubble and self.bubble["kind"] in ("ask", "remind"))):
            return
        self.last_err_text = text
        self.set_bubble("ask", "Hai copiato un errore: te lo spiego sulla lavagna?", thumbs=True)
        self.bubble["explain"] = text

    def explain_error(self, now, text):
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "Errore")
        board = self.begin_lecture(now, None, {"q": first[:90]})
        system = ("Sei uno sviluppatore esperto e paziente. Spiega in italiano l'errore che ti "
                  "viene incollato: **Causa** in una o due frasi, poi **Come risolvere** in due-"
                  "quattro punti con '- '. Niente premesse, niente codice lungo.")

        def worker():
            out, err = ask_claude("ERRORE COPIATO:\n" + text[-6000:], system)
            self.work_q.put(("explain", (board, out, err)))
        threading.Thread(target=worker, daemon=True).start()

    def open_clipboard(self, _e=None):
        self.menu_until = 0.0
        if self.clip_win is not None:
            return
        if not self.clip.items:
            return self.set_bubble("chat", "Non ho ancora visto niente di copiato "
                                           "(le password e i testi privati non li guardo).")
        win = self.clip_win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BORDER)
        tk.Label(win, text="Appunti recenti (doppio clic = copia, Esc = chiudi)", bg=MENU_BORDER,
                 fg="white", font=("Segoe UI", 8)).pack(anchor="w", padx=6, pady=(3, 0))
        lb = tk.Listbox(win, width=60, height=min(12, len(self.clip.items)), font=("Segoe UI", 9),
                        relief="flat", bd=4, activestyle="none")
        for t in self.clip.items:
            line = " ".join(t.split())
            lb.insert("end", line if len(line) <= 80 else line[:77] + "…")
        lb.pack(padx=6, pady=(0, 6))

        def close(_e=None):
            if self.clip_win is not None:
                self.clip_win.destroy()
                self.clip_win = None

        def pick(_e=None):
            sel = lb.curselection()
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.clip.items[sel[0]])
                self.root.update()
                self.say("Copiato!", time.time() + 1.5)
            close()
        lb.bind("<Double-Button-1>", pick)
        lb.bind("<Return>", pick)
        win.bind("<Escape>", close)
        win.bind("<FocusOut>", close)
        win.update_idletasks()
        wa = self.mon.wa
        bw, bh = win.winfo_reqwidth(), win.winfo_reqheight()
        x = min(max(self.x - bw / 2, wa.left + 6), wa.right - bw - 6)
        y = min(max(self.y - PET_H - 20 - bh, wa.top + 6), wa.bottom - bh - 6)
        win.geometry(f"+{int(x)}+{int(y)}")
        lb.focus_force()
        lb.selection_set(0)

    # ---- promemoria e timer -----------------------------------------------------------
    def add_reminder(self, at, text):
        self.brain.data.setdefault("reminders", []).append({"at": at, "text": text[:200]})
        self.brain.save()

    def reminders_context(self):
        rs = sorted(self.brain.data.get("reminders", []), key=lambda r: r["at"])
        return "; ".join(f"{datetime.fromtimestamp(r['at']):%d/%m %H:%M} {r['text']}" for r in rs[:8])

    def check_reminders(self, now):
        rs = self.brain.data.get("reminders", [])
        due = [r for r in rs if r["at"] <= now]
        if not due:
            return
        self.brain.data["reminders"] = [r for r in rs if r["at"] > now]
        self.brain.save()
        lines = []
        for r in due:
            late = now - r["at"] > 120       # scaduto mentre la mascotte era chiusa
            lines.append(r["text"] + (f" (era per le {datetime.fromtimestamp(r['at']):%H:%M})"
                                      if late else ""))
        self.summon(now)
        self.set_bubble("remind", "⏰ " + "\n⏰ ".join(lines))
        for _ in range(3):
            self.add_heart()

    def chat_tags(self, now, tags, reply):
        """Promemoria, timer e comandi chiesti in chat. Ritorna (testo, comando da confermare)."""
        cmd = None
        for tag, val in tags:
            if tag == "#PROMEMORIA:":
                when, _, what = val.partition("|")
                try:
                    at = datetime.strptime(when.strip(), "%Y-%m-%d %H:%M").timestamp()
                    self.add_reminder(at, what.strip() or "Promemoria!")
                except ValueError:
                    reply += "\n(Non ho capito per quando è il promemoria.)"
            elif tag == "#TIMER:":
                mins, _, what = val.partition("|")
                try:
                    self.add_reminder(now + float(mins.strip()) * 60,
                                      (what.strip() or "Timer") + ": tempo scaduto!")
                except ValueError:
                    reply += "\n(Non ho capito quanti minuti.)"
            elif tag == "#COMANDO:":
                cmd = self.commands.find(val)
                if not cmd:
                    reply += f"\n(Non conosco il comando «{val}».)"
        return reply, cmd

    def do_command(self, cmd, yes):
        if not yes:
            return self.set_bubble("chat", "Ok, non lancio niente.")
        ok = pet_work.run_command(cmd)
        self.set_bubble("chat", f"Lanciato «{cmd['nome']}»!" if ok
                        else f"Non sono riuscita a lanciare «{cmd['nome']}» (cartella sbagliata?).")

    # ---- giornata: buongiorno, standup, weekend ------------------------------------------
    def check_day(self, now):
        if now - self.last_move > 5 or self.meeting:   # aspetta che tu sia lì
            return
        d, today, dt = self.brain.data, date.today().isoformat(), datetime.now()
        if (FEAT_STANDUP and d.get("standup_day") != today and dt.weekday() < 5
                and dt.hour >= STANDUP_HOUR):
            d["standup_day"] = d["greet_day"] = today
            self.brain.save()
            return self.start_standup(greet=True)
        if not FEAT_REACTIONS:
            return
        if d.get("greet_day") != today and dt.hour >= 6 and self.quiet():
            d["greet_day"] = today
            self.brain.save()
            name = (" " + self.brain.name) if self.brain.name else ""
            return self.set_bubble("need", f"Buongiorno{name}!")
        if (dt.weekday() == 4 and (dt.hour, dt.minute) >= (17, 30)
                and d.get("weekend_day") != today and self.quiet()):
            d["weekend_day"] = today
            self.brain.save()
            self.set_bubble("need", "È venerdì sera: buon weekend in arrivo!")
            self.set_state("happy", now)
            self.happy_until = now + 2.0
            for _ in range(5):
                self.add_heart()

    def start_standup(self, greet=False):
        """Standup sulla lavagna: sessioni di Claude Code e commit dell'ultimo giorno lavorativo."""
        if self.standup_busy:
            return
        now = time.time()
        self.standup_busy = True
        title = "Buongiorno! Il tuo standup di oggi" if greet else "Il tuo standup"
        board = self.begin_lecture(now, None, {"q": title})
        since = pet_work.prev_workday()
        until = datetime.combine(date.today(), datetime.min.time())
        paths, name_of = list(self.know.projects.values()), self.know.name_of

        def worker():
            prompts = pet_work.session_prompts(project_roots(), since, until, name_of)
            repos = pet_work.git_scan(paths, since, until)
            pending = pet_work.pending_lines(repos)
            text, err = None, None
            if prompts or any(r["commits"] for r in repos):
                text, err = ask_claude(pet_work.standup_prompt(prompts, repos, since),
                                       pet_work.STANDUP_SYSTEM, timeout=120)
            self.work_q.put(("standup", (board, text, err, pending)))
        threading.Thread(target=worker, daemon=True).start()

    # ---- giochi: palla e nascondino -----------------------------------------------------
    def toggle_ball(self, _e=None):
        self.menu_until = 0.0
        if self.ball:
            self.ball = None
            return
        now = time.time()
        mx, my = self.mouse
        self.ball = {"mon": self.monitor_at(mx, my), "x": mx + 14, "y": my + 30, "vx": 0.0,
                     "vy": 0.0, "state": "carry", "t0": now, "touch": now, "dx": 14, "dy": 30}
        self.set_bubble("chat", "Palla! Lanciala (trascinala e lasciala andare) e io la rincorro.")
        if self.state == "sleep":
            self.set_state("idle", now)

    def on_ball_press(self, _e):
        b = self.ball
        if b:
            mx, my = cursor_pos()
            b.update(state="drag", dx=b["x"] - mx, dy=b["y"] - my, touch=time.time())

    def update_ball(self, now):
        b = self.ball
        if not b:
            return
        if now - b["touch"] > BALL_IDLE_S:   # nessuno ci gioca più: la mette via
            self.ball = None
            return
        R = 9
        if b["state"] in ("carry", "drag"):
            mx, my = self.mouse
            b["x"], b["y"] = mx + b["dx"], my + b["dy"]
            b["mon"] = self.monitor_at(mx, my)
            if ((b["state"] == "carry" and now - b["t0"] > 0.7 and now - self.last_move > 0.7)
                    or (b["state"] == "drag" and not user32.GetAsyncKeyState(0x01) & 0x8000)):
                t0, (x0, y0) = self.mouse_hist[0]
                k = FRAME_MS / 1000 / max(now - t0, 0.01)   # velocità del mouse, per fotogramma
                b.update(state="fly", touch=now, vx=max(-30, min(30, (mx - x0) * k)),
                         vy=max(-30, min(30, (my - y0) * k)))
            return
        fm = b["mon"]
        wa = fm.wa
        if b["state"] == "rest":
            if self.plat_at(b["x"], b["y"], mon=fm) is None:
                b.update(state="fly", vy=0.0)        # il bordo sotto è sparito
            return
        b["vy"] = min(b["vy"] + GRAVITY, 24.0)
        nx, ny = b["x"] + b["vx"], b["y"] + b["vy"]
        if not wa.left + R <= nx <= wa.right - R:    # rimbalza sui lati dello schermo
            b["vx"] *= -0.8
            nx = min(max(nx, wa.left + R), wa.right - R)
        if ny - 2 * R < wa.top:
            ny, b["vy"] = wa.top + 2 * R, abs(b["vy"]) * 0.5
        if b["vy"] > 0:
            land = [p[1] for p in fm.plats if p[2] <= nx <= p[3] and b["y"] <= p[1] <= ny]
            if land or ny >= wa.bottom:
                ny = min(land) if land else wa.bottom
                if b["vy"] > 3:                      # rimbalzo
                    b["vy"] *= -0.55
                    b["vx"] *= 0.85
                else:                                # rotola e si ferma
                    b["vy"] = 0.0
                    b["vx"] *= 0.9
                    if abs(b["vx"]) < 0.3:
                        b.update(state="rest", vx=0.0)
                        self.next_think = now
        b["x"], b["y"] = nx, ny

    def kick_ball(self, now):
        b = self.ball
        d = 1 if self.mouse[0] >= b["x"] else -1     # te la ripassa
        b.update(state="fly", vx=d * random.uniform(8, 14), vy=-random.uniform(10, 16),
                 kicks=b.get("kicks", 0) + 1)   # "touch" lo aggiorni solo tu: se smetti, finisce
        self.set_state("happy", now)
        self.happy_until = now + 0.6
        self.brain.bump_mood(0.02)
        self.add_heart()

    def hide_spot(self, H=None):
        """Un bordo di finestra dove nascondersi (o la posizione aggiornata di quello scelto)."""
        if H:
            T = next((p for p in H["mon"].plats if p[0] == H["T"][0]), None)
            if T:
                return H["mon"], T
        spots = [(m, p) for m in self.mons for p in m.plats
                 if p[0] is not None and p[3] - p[2] > 4 * MARGIN]
        return random.choice(spots) if spots else (None, None)

    def start_hide(self, _e=None):
        self.menu_until = 0.0
        if self.hide:
            return
        now = time.time()
        m, T = self.hide_spot()
        if not m:
            return self.set_bubble("chat", "Non ci sono finestre dietro cui nascondermi!")
        self.ball = None
        self.hide = {"mon": m, "T": T, "x": random.uniform(T[2] + MARGIN, T[3] - MARGIN),
                     "t0": now}
        if self.state == "sleep":
            self.set_state("idle", now)
        self.set_bubble("chat", "Nascondino! Conta fino a dieci... poi trovami e cliccami!")
        self.next_think = now + 2.5

    def st_hide(self, now):
        H = self.hide
        if not H:
            return self.set_state("idle", now)
        if not self.supported(now):          # la finestra si è chiusa: scoperta!
            self.hide = None
            return
        if now - H["t0"] > HIDE_S:
            self.hide = None
            self.set_state("happy", now)
            self.happy_until = now + 1.5
            self.set_bubble("chat", "Non mi hai trovata! Ho vinto io!")

    def found_hiding(self, now):
        secs = int(now - self.hide["t0"])
        self.hide = None
        self.set_state("happy", now)
        self.happy_until = now + 2.0
        self.brain.bump_mood(0.08)
        for _ in range(6):
            self.add_heart()
        self.set_bubble("chat", f"Mi hai trovata in {secs} secondi! Bravo!")

    def draw_ball(self):
        b = self.ball
        m = b["mon"]
        c = m.c
        R = 9
        x, y = b["x"] - m.ox, b["y"] - m.oy - R
        c.create_oval(x - R, y - R, x + R, y + R, fill="#FFFFFF", outline=MENU_FG, width=2,
                      tags=("ball",))
        a = b["x"] / R                       # gira mentre rotola
        for k in range(3):
            t = a + k * 2 * math.pi / 3
            px_, py_ = x + 5 * math.cos(t), y + 5 * math.sin(t)
            c.create_oval(px_ - 2.5, py_ - 2.5, px_ + 2.5, py_ + 2.5, fill=ORANGE, width=0,
                          tags=("ball",))

    def spontaneous(self, now):
        wm = self.working_min(now)
        hour = datetime.now().hour
        if (FEAT_ADVICE and (wm > LONG_WORK_MIN or hour >= 23 or hour < 6)
                and self.advice_today < MAX_ADVICE_PER_DAY):
            self.advice_today += 1
            return self.give_advice(now, spontaneous=True)
        if (random.random() < 0.06            # di rado, al massimo una volta al giorno
                and self.brain.data.get("last_proposal_day") != date.today().isoformat()):
            return self.propose_improvements(now, auto=True)
        if now - self.last_need > 240:       # altrimenti un commento sui suoi bisogni (gratis)
            self.last_need = now
            self.say_need(now)

    def say_need(self, now):
        if self.hungry(now):
            lines = ["Ho un certo languorino... un biscotto?", "Mi daresti qualcosa da sgranocchiare?"]
            cat = "fame"
        elif now - self.last_move > 300 and self.brain.mood < 0.4:
            lines = ["Mi sento un po' sola quassù.", "Ci sei ancora? Mi mancavi."]
            cat = "solitudine"
        else:
            name = (" " + self.brain.name) if self.brain.name else ""
            lines = [f"Ciao{name}! Tutto bene?", "Sto facendo due passi sui bordi.",
                     "Se ti serve una mano, doppio clic su di me."]
            rec = self.know.recent_projects()
            if rec:                          # i progetti su cui lavori ultimamente
                p = random.choice(rec)
                lines += [f"Come procede {p}?", f"Se vuoi ti apro Claude su {p}: chiedimelo!"]
            cat = "saluto"
        self.set_bubble("need", random.choice(lines), cat=cat)

    def ask_async(self, kind, prompt, system):
        """Lancia una chiamata a Claude in un thread; il risultato torna in think_q."""
        if self.thinking:
            return False
        self.thinking = kind
        if kind in ("chat", "advice"):
            self.set_bubble("wait", "", cat=None)

        def worker():
            self.think_q.put((kind, *ask_claude(prompt, system)))
        threading.Thread(target=worker, daemon=True).start()
        return True

    def on_thought(self, now, kind, text, err):
        self.thinking = None
        if kind == "proposals":
            return self.on_proposals(now, text, err)
        if kind == "diary":
            sid, self.diary_sid = self.diary_sid, None
            if sid and text and not err:
                self.brain.add_diary(sid, text)
            return
        if err or not text:
            if kind == "chat" and self.chat_hist and self.chat_hist[-1][0] == "Utente":
                self.chat_hist.pop()             # domanda rimasta senza risposta
            fallback = {"chat": "Scusa, mi si è annodata la lingua. Riprova!",
                        "advice": "Mmm, non mi viene in mente nulla di furbo adesso."}
            return self.set_bubble("chat", fallback.get(kind, "..."), cat=None)
        launch, skill, tags, keep = None, None, [], []
        for line in text.splitlines():           # #AVVIA:, #PROMEMORIA:... valgono solo in chat
            up = line.strip().upper()
            tag = next((t for t in CHAT_TAGS if up.startswith(t)), None) if kind == "chat" else None
            if tag == "#AVVIA:":
                launch = line.split(":", 1)[1].strip()
            elif tag == "#SKILL:":
                skill = line.split(":", 1)[1].strip()
            elif tag:
                tags.append((tag, line.split(":", 1)[1].strip()))
            else:
                keep.append(line)
        clean, name, facts = Brain.parse_tags("\n".join(keep))
        if name:
            self.brain.set_name(name)
        for f in facts:
            self.brain.remember(f)
        clean = clean or ("Ci penso io!" if launch or tags else text)
        cmd = None
        if kind == "chat":
            if launch or skill:
                clean = self.launch_from_chat(launch, clean, skill)
            clean, cmd = self.chat_tags(now, tags, clean)
            self.chat_hist = (self.chat_hist + [("Tu", clean)])[-CHAT_TURNS:]
            self.chat_at = now
            if self.session_id:
                self.sessions.append(self.session_id, "Tu", clean)
        if cmd:                                  # un comando si lancia solo col tuo sì
            self.set_bubble("ask", f"{clean}\nLancio «{cmd['nome']}»? ({cmd['comando']})",
                            thumbs=True)
            self.bubble["command"] = cmd
            return
        self.set_bubble("advice" if kind == "advice" else "chat", clean,
                        cat=self.last_fb_cat if kind == "advice" else None,
                        thumbs=(kind == "advice"))

    def give_advice(self, now, spontaneous):
        wm = int(self.working_min(now))
        hour = datetime.now().hour
        part = ("mattina" if hour < 12 else "pomeriggio" if hour < 18
                else "sera" if hour < 23 else "notte fonda")
        self.last_fb_cat = ("pausa" if wm > LONG_WORK_MIN else "riposo" if hour >= 23 or hour < 6
                            else "generico")
        prompt = (f"È {part} (ore {hour}). L'utente sta lavorando da circa {wm} minuti "
                  f"senza pause. Programma in primo piano: {self.app or 'sconosciuto'}. "
                  f"COSA RICORDO: {self.brain.context()}\n" + self.knowledge_block("") +
                  f"{'Proponi tu, spontaneamente,' if spontaneous else 'Ti ha chiesto'} "
                  "UN consiglio breve e gentile adatto a questo momento, in una frase.")
        self.ask_async("advice", prompt, PERSONA.format(user=self.brain.name or "qualcuno",
                                                        who=WHO[CHARACTER]))

    def propose_improvements(self, now, auto):
        if self.thinking:
            return
        if auto:
            if self.brain.data.get("last_proposal_day") == date.today().isoformat():
                return
            self.brain.data["last_proposal_day"] = date.today().isoformat()
            self.brain.save()
        try:
            code = Path(__file__).read_text(encoding="utf-8")[:48000]
        except OSError:
            return
        self.say("Rifletto su come potrei migliorarmi...", now + 6)
        system = ("Sei un revisore di codice Python conciso. Ti viene dato il sorgente di una "
                  "mascotte da desktop in tkinter. Proponi 3 migliorie CONCRETE e piccole "
                  "(bug, chiarezza, piccole feature), ognuna come '- [ ] titolo: una riga di "
                  "spiegazione'. Solo la lista, niente altro.")
        self.ask_async("proposals", "SORGENTE:\n" + code, system)

    def on_proposals(self, now, text, err):
        if err or not text:
            return self.say("Non sono riuscita a farmi venire idee, pazienza.", now + 3)
        try:
            with PROPOSALS_PATH.open("a", encoding="utf-8") as fh:
                fh.write(f"\n## {datetime.now():%Y-%m-%d %H:%M}\n{text.strip()}\n")
            self.say("Ho scritto qualche idea in pet_proposals.md, decidi tu!", now + 4)
        except OSError:
            self.say("Avevo delle idee ma non riesco a salvarle.", now + 3)

    # ---- fumetti e chat --------------------------------------------------------
    def set_bubble(self, kind, text, cat=None, thumbs=False):
        self.bubble = {"kind": kind, "full": text, "shown": 0, "thumbs": thumbs,
                       "cat": cat, "t0": time.time(), "done_t": None}

    def update_bubble(self, now):
        b = self.bubble
        if b["kind"] == "wait":
            return
        if b["shown"] < len(b["full"]):
            b["shown"] = min(len(b["full"]), b["shown"] + 2)
        elif b["done_t"] is None:
            b["done_t"] = now
        if (b["done_t"] is not None and not b["thumbs"] and b["kind"] != "remind"   # resta finché
                and not (b["kind"] == "chat" and self.talk_win is not None)):   # non la chiudi
            hold = 3 + len(b["full"]) * 0.045
            if now - b["done_t"] > hold:
                self.bubble = None

    def bubble_skip_or_close(self):
        b = self.bubble
        if not b:
            return
        if b["shown"] < len(b["full"]):
            b["shown"] = len(b["full"])
        elif not b["thumbs"]:
            self.bubble = None

    def on_thumb(self, good):
        b = self.bubble
        if not b or not b["thumbs"]:
            return
        if "chore" in b:                     # domanda sulle faccende: sì / no
            return self.do_chore(*b["chore"], good)
        if "update" in b:                    # versione nuova: la installo?
            return self.do_update(b["update"], good)
        if "command" in b:                   # comando rapido chiesto in chat
            return self.do_command(b["command"], good)
        if "explain" in b:                   # errore copiato
            self.bubble = None
            if good:
                self.explain_error(time.time(), b["explain"])
            return
        if b["cat"]:
            self.brain.feedback(b["cat"], good)
        self.set_bubble("chat", "Grazie, me lo segno!" if good else "Ok, cambio registro.",
                        cat=None)

    def open_talk(self, _e=None):
        if self.talk_win is not None or self.state == "lecture":
            return
        if self.dragging:
            self.on_release()
        win = self.talk_win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BORDER)
        tk.Label(win, text="Parliamo! (Invio = manda, Esc = chiudi)", bg=MENU_BORDER,
                 fg="white", font=("Segoe UI", 8)).pack(anchor="w", padx=6, pady=(3, 0))
        ent = self.talk_ent = tk.Entry(win, width=34, font=("Segoe UI", 10), relief="flat", bd=4)
        ent.pack(padx=6, pady=(0, 6))
        ent.bind("<Return>", lambda e: self.send_talk(ent.get()))
        ent.bind("<Escape>", lambda e: self.close_talk())
        win.bind("<FocusOut>", lambda e: self.close_talk())
        win.update_idletasks()
        bw, bh = win.winfo_reqwidth(), win.winfo_reqheight()
        wa = self.mon.wa
        x = self.x + PET_W / 2 + 14          # di lato, così non copre il fumetto
        if x + bw > wa.right - 6:
            x = self.x - PET_W / 2 - 14 - bw
        y = min(max(self.y - bh, wa.top + 6), wa.bottom - bh - 6)
        win.geometry(f"+{int(x)}+{int(y)}")
        ent.focus_force()

    def close_talk(self):
        if self.talk_win is not None:
            self.talk_win.destroy()
            self.talk_win = self.talk_ent = None
            self.queue_diary()               # finita (per ora) la chiacchierata: nel diario

    def send_talk(self, text):
        text = text.strip()
        if not text or self.thinking:
            return                           # sta ancora rispondendo: il testo resta lì
        if self.talk_ent is not None:
            self.talk_ent.delete(0, "end")
        now = time.time()
        low = text.lower()
        if any(k in low for k in ("cosa faccio", "che faccio", "consiglio", "consigli", "suggeri")):
            return self.give_advice(now, spontaneous=False)
        if "standup" in low:
            return self.start_standup()
        if re.search(r"\b(aggiornati|aggiornamenti|nuova versione)\b", low):
            return self.check_update_now()
        if now - self.chat_at > CHAT_FORGET_S or self.session_id is None:
            self.queue_diary()               # la chiacchierata precedente va nel diario
            self.chat_hist, self.session_id = [], self.sessions.new_id()
        self.chat_hist = (self.chat_hist + [("Utente", text)])[-CHAT_TURNS:]
        self.chat_at = now
        self.sessions.append(self.session_id, "Utente", text)
        talk = "\n".join(f"{who}: {line}" for who, line in self.chat_hist)
        query = " ".join(t for w, t in self.chat_hist[-4:] if w == "Utente")  # anche "e quello?"
        extra = ""
        if self.commands.hint():
            extra += "COMANDI RAPIDI: " + self.commands.hint() + "\n"
        if self.reminders_context():
            extra += "PROMEMORIA ATTIVI: " + self.reminders_context() + "\n"
        if self.asked_launch(text) and self.know.skills_hint():   # solo se serve: costa
            extra += "SKILL DI CLAUDE CODE: " + self.know.skills_hint() + "\n"
        prompt = (f"COSA RICORDO: {self.brain.context()} Sei {self.brain.mood_label()}.\n"
                  + self.knowledge_block(query) + extra
                  + f"CONVERSAZIONE FINORA (Tu = la mascotte):\n{talk}\n"
                  "Rispondi all'ultimo messaggio dell'utente, in carattere, tenendo conto di "
                  "quanto vi siete già detti. " + LAUNCH_HINT + " " + REMEMBER_HINT + " "
                  + REMIND_HINT.format(now=datetime.now().strftime("%A %Y-%m-%d %H:%M")))
        self.ask_async("chat", prompt, PERSONA.format(user=self.brain.name or "qualcuno",
                                                      who=WHO[CHARACTER]))

    def knowledge_block(self, query):
        """Cosa sa di te e del tuo lavoro, da mettere nel prompt: poche righe sempre,
        più i pezzi di memorie e di vecchie chiacchierate pertinenti a query."""
        parts = []
        ov = self.know.overview()
        if ov:
            parts.append("PROGETTI: " + ov)
        di = self.brain.diary_context()
        if di:
            parts.append("DIARIO DELLE VOSTRE CHIACCHIERATE:\n" + di)
        if query:
            mem = self.know.search(query)
            if mem:
                parts.append("MEMORIE DI CLAUDE CODE PERTINENTI:\n" + mem)
            past = self.sessions.search(query, exclude=self.session_id)
            if past:
                parts.append("CONVERSAZIONI PASSATE PERTINENTI:\n" + past)
        return "".join(p + "\n" for p in parts)

    @staticmethod
    def asked_launch(text):
        """Nel messaggio chiedi di aprire/avviare qualcosa (o scrivi /skill)?"""
        return (text.lstrip().startswith("/")
                or bool(re.search(r"\b(" + "|".join(LAUNCH_WORDS) + r")\b", norm(text))))

    def launch_from_chat(self, name, reply, skill=None):
        """Apre Claude Code sul progetto (e/o con una skill già avviata), ma solo se
        nell'ultimo messaggio l'hai chiesto tu."""
        asked = next((t for w, t in reversed(self.chat_hist) if w == "Utente"), "")
        if not self.asked_launch(asked):
            return reply                     # nessuna richiesta esplicita: non apre nulla
        prompt, work, have = "", None, set()
        if skill:
            sname, _, args = skill.strip().lstrip("/").partition(" ")
            have = {w for n, _, w in self.know.skills() if n.lower() == sname.lower()}
            if not have:
                return reply + f"\n(Non trovo la skill «{sname}».)"
            prompt = f"/{sname} {args}".strip()
        if name:
            key, path = self.know.find_project(name)
            if not path:
                return reply + f"\n(Non trovo il progetto «{name}».)"
            work = self.know.is_work(path)
        else:                                # solo la skill: si apre nella tua cartella
            key, path = prompt.split()[0], str(Path.home())
        if have and work not in have:        # la skill sta solo nell'altro profilo
            work = True in have
        if not launch_claude(path, key, work=work, prompt=prompt):
            return reply + "\n(Non sono riuscita ad aprire Claude Code.)"
        return reply

    # ---- diario delle chiacchierate ---------------------------------------------
    def queue_diary(self):
        """Se la chiacchierata in corso ha battute nuove, la mette in coda per il diario."""
        sid = self.session_id
        if sid and len(self.sessions.load(sid)) > max(1, self.diary_done.get(sid, 0)):
            self.diary_due.add(sid)

    def write_diary(self):
        sid = self.diary_due.pop()
        turns = self.sessions.load(sid)
        self.diary_done[sid] = len(turns)    # anche se fallisce: niente tentativi a ripetizione
        talk = "\n".join(f"{w}: {t[:400]}" for w, t in turns[-24:])
        system = ("Scrivi il diario di una mascotte da desktop: una o due frasi in italiano, in "
                  "prima persona (io = la mascotte), su di cosa abbiamo parlato e cosa ho capito "
                  "dell'utente. Niente elenchi, niente saluti.")
        if self.ask_async("diary", "CHIACCHIERATA:\n" + talk, system):
            self.diary_sid = sid

    # ---- disegno ---------------------------------------------------------------
    def draw(self, now):
        for m in self.mons:
            m.c.delete("!board")             # la lavagna resta: è fatta di widget veri
        if self.ball:
            self.draw_ball()
        self.draw_portals(now, front=False)
        self.draw_pet(now)
        self.draw_portals(now, front=True)
        f = self.food                        # davanti a lei: se no il corpo lo copre
        if f and f["bites"] < 3:
            fm = f["mon"]
            self.draw_food(fm.c, f["kind"], f["x"] - fm.ox, f["y"] - fm.oy - 10, f["bites"],
                           1 if self.x >= f["x"] else -1, ("food",))
        self.draw_particles()
        if (self.hungry(now) and not self.food and now % 25 < 4
                and self.state in ("idle", "walk", "happy")):
            self.draw_thought()
        if self.say_text and (self.say_until is None or now < self.say_until):
            self.draw_say()
        if self.bubble:
            self.draw_bubble(now)
        if now < self.menu_until:
            self.draw_menu()

    def draw_bubble(self, now):
        c = self.c
        b = self.bubble
        if b["kind"] == "wait":
            txt = "." * (1 + int(now / 0.3) % 3)
            shown = txt
        else:
            shown = b["full"][:b["shown"]]
        if not shown:
            shown = "."
        pad, maxw = 10, 300
        cx = self.x - self.ox
        anchor_y = self.y - self.oy - PET_H - 16
        tmp = c.create_text(0, -1000, text=shown, font=("Segoe UI", 10), width=maxw, anchor="nw")
        x0, y0, x1, y1 = c.bbox(tmp)
        tw, th = x1 - x0, y1 - y0
        bx0 = min(max(cx - tw / 2 - pad, 6), int(c.cget("width")) - tw - 2 * pad - 6)
        extra = 24 if (b["thumbs"] and b["shown"] >= len(b["full"])) else 0
        by1 = anchor_y
        by0 = by1 - th - 2 * pad - extra
        if by0 < 6:                          # non entra sopra: mettilo sotto la mascotte
            by0 = self.y - self.oy + 6
            by1 = by0 + th + 2 * pad + extra
        c.coords(tmp, bx0 + pad, by0 + pad)
        col = {"need": "#FFF7E6", "advice": "#EAF4FF", "chat": MENU_BG,
               "wait": MENU_BG}.get(b["kind"], MENU_BG)
        rect = round_rect(c, bx0, by0, bx0 + tw + 2 * pad, by1, 12, fill=col,
                          outline=MENU_BORDER, width=2, tags=("bubble",))
        tail = cx                            # codina verso la mascotte
        tail = min(max(tail, bx0 + 12), bx0 + tw + 2 * pad - 12)
        if by1 <= anchor_y + 1:
            c.create_polygon(tail - 7, by1 - 1, tail + 7, by1 - 1, tail, by1 + 11,
                             fill=col, outline=MENU_BORDER, width=2, tags=("bubble",))
        c.tag_raise(tmp)
        c.itemconfigure(tmp, tags=("bubble",))
        if extra:                            # pollici su/giù per i consigli (sì/no per le faccende)
            fy = by1 - 16
            yes = "Sì" if b["kind"] == "ask" else "Utile"
            c.create_text(bx0 + pad + 6, fy, text="\U0001F44D  " + yes, anchor="w",
                          fill="#2E7D32", font=("Segoe UI", 9), tags=("bubble", "thumb_up"))
            c.create_text(bx0 + tw + pad - 6, fy, text="No  \U0001F44E", anchor="e",
                          fill="#B3261E", font=("Segoe UI", 9), tags=("bubble", "thumb_down"))

    def draw_say(self):
        c = self.c
        x, y = self.x - self.ox, self.y - self.oy - PET_H - 18
        t = c.create_text(x, y, text=self.say_text, fill=MENU_FG, font=("Segoe UI", 9),
                          anchor="s")
        x0, y0, x1, y1 = c.bbox(t)
        r = c.create_rectangle(x0 - 8, y0 - 4, x1 + 8, y1 + 4, fill=MENU_BG,
                               outline=MENU_BORDER, width=2)
        c.create_polygon(x - 5, y1 + 3, x + 5, y1 + 3, x, y1 + 10, fill=MENU_BG,
                         outline=MENU_BORDER)
        c.tag_lower(r, t)

    def draw_portals(self, now, front):
        if not self.portal:
            return
        for end in (self.portal["src"], self.portal["dst"]):
            s = self.portal_scale(end, now)
            if s <= 0:
                continue
            m = end["mon"]
            c = m.c
            cx, cy = end["x"] - m.ox, end["y"] - m.oy - PORTAL_RY
            rx, ry = PORTAL_RX * s, PORTAL_RY * s
            if self.portal_style == "sparks":
                if front:                    # anello di scintille che gira
                    c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, outline="#FF8F00", width=2)
                    for i in range(32):
                        a = 2 * math.pi * i / 32 + now * 5
                        j = random.uniform(-1.5, 1.5)
                        x, y = cx + (rx + j) * math.cos(a), cy + (ry + j) * math.sin(a)
                        c.create_rectangle(x - 1.5, y - 1.5, x + 1.5, y + 1.5,
                                           fill=random.choice(SPARKS), width=0)
            else:
                col, glow, inner = OVALS[end["entry"]]
                if not front:                # superficie del portale, dietro alla mascotte
                    c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=inner, width=0)
                    for i in range(8):       # vortice
                        a = now * 3 + i * 0.8
                        k = (i + 1) / 9
                        x, y = cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)
                        c.create_rectangle(x - 1, y - 1, x + 2, y + 2, fill=col, width=0)
                else:                        # bordo luminoso, davanti
                    c.create_oval(cx - rx - 3, cy - ry - 3, cx + rx + 3, cy + ry + 3,
                                  outline=glow, width=2)
                    c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, outline=col, width=4)

    def draw_food(self, c, kind, cx, cy, bites, side, tags, r=9):
        if kind == "cookie":
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=COOKIE, outline=COOKIE_EDGE,
                          width=2, tags=tags)
            for dx, dy in ((-4, -3), (3, -4), (-1, 3), (4, 2)):
                k = r / 9
                c.create_rectangle(cx + dx * k - 1, cy + dy * k - 1, cx + dx * k + 2,
                                   cy + dy * k + 2, fill=CHIP, width=0, tags=tags)
        else:
            c.create_oval(cx - r, cy - r + 1, cx + r, cy + r, fill=APPLE, outline=APPLE_EDGE,
                          width=1, tags=tags)
            c.create_rectangle(cx - 1, cy - r - 4, cx + 1, cy - r + 2, fill=STEM, width=0,
                               tags=tags)
            c.create_oval(cx + 1, cy - r - 5, cx + 8 * r / 9, cy - r, fill=LEAF, width=0,
                          tags=tags)
        for k in range(bites):               # i morsi "bucano" il cibo (colore trasparente)
            by = cy + (-5, 1, 6)[k] * r / 9
            c.create_oval(cx + side * r * 0.9 - 5, by - 5, cx + side * r * 0.9 + 5, by + 5,
                          fill=KEY, width=0, tags=tags)

    def draw_particles(self):
        for pt in self.particles:
            m = pt["mon"]
            c = m.c
            x, y = pt["x"] - m.ox, pt["y"] - m.oy
            if pt["kind"] == "heart":
                x += 2 * math.sin(pt["life"] / 5)
                for r, row in enumerate(HEART_PIX):
                    for col, ch in enumerate(row):
                        if ch == "X":
                            c.create_rectangle(round(x + col * 2), round(y + r * 2),
                                               round(x + col * 2 + 2), round(y + r * 2 + 2),
                                               fill=HEART, width=0)
            elif pt["kind"] == "qmark":
                c.create_text(x, y, text="?", fill=CHALK, font=(CHALK_FONT, 13, "bold"))
            else:
                c.create_rectangle(x - 1, y - 1, x + 2, y + 2, fill=pt["color"], width=0)

    def draw_thought(self):
        c = self.c
        x, y = self.x - self.ox + PET_W / 2 + 4, self.y - self.oy - PET_H - 10
        c.create_oval(x - 6, y + 2, x - 2, y + 6, fill=MENU_BG, outline=MENU_BORDER)
        c.create_oval(x, y - 6, x + 7, y + 1, fill=MENU_BG, outline=MENU_BORDER)
        c.create_oval(x + 4, y - 34, x + 36, y - 6, fill=MENU_BG, outline=MENU_BORDER, width=2)
        self.draw_food(c, "cookie", x + 20, y - 20, 0, 1, (), r=8)

    def draw_pet(self, now):
        c, st, p = self.c, self.state, P
        x, y = self.x - self.ox, self.y - self.oy
        bx, by = x - 3.5 * p, y - 7 * p      # angolo in alto a sinistra del corpo
        if st == "happy":
            bx += 1.5 * math.sin(now * 14)   # ondeggia di gioia
        walking = st in ("walk", "portal_in", "portal_out")
        lp = self.lecture.phase if st == "lecture" and self.lecture else None
        step = int(self.anim / 10) % 2
        sit = p if st == "sleep" else 0
        d = (-1 if walking and step else 0) + sit
        if st == "pushup":                   # su e giù come a fare flessioni
            d += 1.4 * abs(math.sin((now - self.since) * 6))
        if st == "hide":                     # acquattata dietro al bordo: spunta solo la testa
            d += 3.6 * p
        clip = None                          # metà nascosta oltre il centro del portale
        if st == "portal_in":
            clip = (self.portal["src"]["x"] - self.ox, -self.portal["dir"])
        elif st == "portal_out":
            clip = (self.portal["dst"]["x"] - self.ox, self.portal["dir"])

        octo = CHARACTER == "octopus"
        body = OCTO if octo else ORANGE

        def px(c0, r0, c1, r1, fill=None, dy=0.0, dx=0.0):
            fill = fill or body
            x0, x1 = bx + c0 * p + dx, bx + c1 * p + dx
            if clip:
                if clip[1] < 0:
                    x1 = min(x1, clip[0])
                else:
                    x0 = max(x0, clip[0])
                if x1 <= x0:
                    return
            c.create_rectangle(round(x0), round(by + r0 * p + dy), round(x1),
                               round(by + r1 * p + dy), fill=fill, width=0, tags=("pet",))

        pw = self.power if st in ("rise", "float") else None   # potere in uso
        if pw == "telekinesis":                 # aura della telecinesi, dietro a tutto
            r = 34 + 3 * math.sin(now * 5)
            cy = by + 3.5 * p + d
            for k, col in ((0, TELE_SOFT), (7, TELE)):
                c.create_oval(x - r - k, cy - r - k, x + r + k, cy + r + k, outline=col,
                              width=2, dash=(5, 3), tags=("pet",))

        # mantello da supereroe, dietro al corpo (con ragnatela e razzi lo toglie)
        if (self.cape_on and lp is None and st not in ("drag", "sleep")
                and pw in (None, "telekinesis")):
            if st == "fly":
                face = self.act_dir
            elif walking:
                face = 1 if self.tx >= self.x else -1
            else:
                face = 1
            moving = walking or st == "fly"
            sway = 4 * math.sin(now * 6)
            stream = (-face * 13 if moving else 0) + sway
            nx1, nx2, ny = bx + 2.3 * p, bx + 4.7 * p, by + 0.4 * p + d   # stretto al collo
            hy = by + 7.6 * p + d                                          # largo e lungo
            hx1, hx2 = bx - 0.6 * p + stream, bx + 7.6 * p + stream
            c.create_polygon(nx1, ny, nx2, ny, hx2, hy, (hx1 + hx2) / 2, hy + 7,
                             hx1, hy, fill=CAPE_COL, outline=CAPE_DARK, width=1,
                             smooth=False, tags=("pet",))

        for i, col in enumerate((0, 2, 4, 6)):              # zampe (o tentacoli)
            if st == "sleep":
                px(col, 6, col + 1, 7)
            elif st == "fly":                               # in volo: zampe raccolte dietro
                px(col, 5, col + 1, 6, dy=d)
            elif octo:                                      # tentacoli che ondeggiano e
                out = -1 if i < 2 else 1                    # si arricciano verso l'esterno
                wave = 0.25 * math.sin(now * (9 if walking else 3) + i * 1.6)
                px(col, 5, col + 1, 6.4, dy=d)
                px(col + out * 0.5 + wave, 6.2, col + 1 + out * 0.5 + wave, 7, dy=d)
                px(col + 0.3, 5.6, col + 0.7, 6, OCTO_DARK, dy=d)   # ventosa
            else:
                moving = walking or st == "drag" or pw == "web"
                lift = 0.6 if moving and i % 2 == step else 0
                px(col, 5, col + 1, 7 - lift, dy=d)
        px(0, 0, 7, 5, dy=d)                                # corpo
        if octo:                                            # testa a cupola e macchioline
            px(1, -1, 6, 0, dy=d)
            px(2, -1.5, 5, -1, dy=d)
            px(1.6, -0.6, 2.2, -0.1, OCTO_DARK, dy=d)
            px(4.6, -1.1, 5.1, -0.6, OCTO_DARK, dy=d)
            px(3.3, -0.4, 3.8, 0.1, OCTO_DARK, dy=d)
        ang = st == "lecture" and self.lecture and self.lecture.style == "presenter"
        if ang:                                             # divulgatore: capelli in ordine,
            px(0, -0.5, 7, 0.5, HAIR, dy=d)                 # riga di lato, giacca e cravatta
            px(2.2, -0.9, 7, -0.4, HAIR, dy=d)
            if octo:                                        # i capelli coprono la cupola
                px(1, -1.1, 6, -0.4, HAIR, dy=d)
                px(2, -1.6, 5, -1, HAIR, dy=d)
            px(0, 4.1, 2.6, 5, JACKET, dy=d)
            px(4.4, 4.1, 7, 5, JACKET, dy=d)
            px(2.6, 4.0, 4.4, 4.4, SHIRT, dy=d)
            px(3.2, 4.2, 3.8, 5, TIE, dy=d)
        elif st == "lecture":                               # parrucca: cade in testa
            fall = -50 * max(0.0, 1 - (now - self.wig_t) / 0.3)
            for c0, r0, c1, r1, col in WIG_PARTS:
                px(c0, r0, c1, r1, col, dy=d + fall)

        if st == "fly":                                     # pugni in avanti da supereroe
            la = ra = -0.6
        elif st == "flex":                                  # bicipiti in alto
            la = ra = -0.4
        elif st == "heropose":                              # mani sui fianchi
            la = ra = 3.2
        elif st == "pushup":
            la = ra = 4.2
        elif st in ("fall", "drag"):                        # braccia
            la = ra = 0
        elif pw == "web":                                # braccio alzato che tira la tela
            la, ra = 2, -0.8
        elif pw == "rockets":                               # palmi giù a spingere
            la = ra = 3.6
        elif pw == "telekinesis":                              # mano tesa verso l'alto
            la, ra = 2, 0.4
        elif walking:
            la, ra = (2.5, 2) if step else (2, 2.5)
        elif lp in ("rise", "think"):                       # si gratta la testa
            la, ra = (0.6 if int(now / 0.25) % 2 else 0.1), 2
        elif lp == "talk":                                  # gesticola verso la lavagna
            la, ra = 2, 1 + 0.4 * math.sin(now * 9)
        elif lp:
            la, ra = 2, 1.6
        else:
            la = ra = 2
        px(-1, la, 0, la + 1, dy=d)
        px(7, ra, 8, ra + 1, dy=d)
        if st == "heropose":                                # avambracci piegati verso i fianchi
            px(-0.2, la + 1, 0.3, la + 1.6, dy=d)
            px(6.7, ra + 1, 7.2, ra + 1.6, dy=d)
        if st == "flex":                                    # pugni serrati in alto
            px(-1.2, la - 0.4, 0.2, la, dy=d)
            px(6.8, ra - 0.4, 8.2, ra, dy=d)
        if st == "pushup" and (now - self.since) % 1 < 0.5:  # sbuffo di fatica
            c.create_text(x + 4.6 * p, by - 0.2 * p + d, text="!", fill=CAPE_COL,
                          font=("Segoe UI", 9, "bold"), tags=("pet",))
        if st == "fall" and self.chute:                     # paracadute aperto
            topy = by - 3.4 * p
            c.create_arc(x - 38, topy - 32, x + 38, topy + 30, start=0, extent=180,
                         style="chord", fill=CHUTE_COL, outline=CHUTE_STR, width=2,
                         tags=("pet",))
            for seg in (-19, 0, 19):                        # spicchi chiari
                c.create_arc(x - 38, topy - 32, x + 38, topy + 30, start=70 - seg * 1.2,
                             extent=14, style="pieslice", fill=CHUTE_ALT, outline="",
                             tags=("pet",))
            for ex in (-34, -12, 12, 34):                   # funi verso le braccia
                c.create_line(x + ex, topy, x + ex * 0.2, by + 2 * p, fill=CHUTE_STR,
                              width=1, tags=("pet",))
        if lp in ("talk", "idle"):                          # bacchetta verso la lavagna
            hx, hy = bx + 8 * p, by + (ra + 0.5) * p + d
            wob = 6 * math.sin(now * 9) if lp == "talk" else 0
            tx, ty = hx + 40, hy - 24 - wob
            c.create_line(hx, hy, tx, ty, fill=WOOD_DARK, width=3, tags=("pet",))
            c.create_rectangle(tx - 2, ty - 2, tx + 2, ty + 2,
                               fill=STUDIO_GOLD if ang else CHALK, width=0, tags=("pet",))
        if pw == "web":                                  # ragnatela dalla mano all'aggancio
            hx, hy = bx + 7.5 * p, by + ra * p + d
            ax, ay = self.anchor_pt[0] - self.ox, self.anchor_pt[1] - self.oy
            k = min(1.0, (now - self.since) / 0.25) if st == "rise" else 1.0
            ex, ey = hx + (ax - hx) * k, hy + (ay - hy) * k
            c.create_line(hx, hy, ex, ey, fill=WEB, width=2, tags=("pet",))
            if k >= 1.0:                                    # stella di tela dove si attacca
                for a in range(0, 360, 60):
                    t = math.radians(a)
                    c.create_line(ex, ey, ex + 8 * math.cos(t), ey + 8 * math.sin(t),
                                  fill=WEB, width=1, tags=("pet",))
        elif pw == "rockets":                               # fiamme dai palmi e dai piedi
            fl = random.uniform(0, 6)
            for fx, fy, size in ((bx - 0.5 * p, by + (la + 1) * p + d, 1.0),
                                 (bx + 7.5 * p, by + (ra + 1) * p + d, 1.0),
                                 (x, y + d, 1.5)):
                L = (12 + fl) * size
                c.create_polygon(fx - 5 * size, fy, fx + 5 * size, fy, fx, fy + L,
                                 fill=FLAME[2], width=0, tags=("pet",))
                c.create_polygon(fx - 2.5 * size, fy, fx + 2.5 * size, fy, fx, fy + L * 0.6,
                                 fill=FLAME[0], width=0, tags=("pet",))

        if now >= self.next_blink:                          # occhi
            self.blink_until = now + 0.13
            self.next_blink = now + random.uniform(2.5, 5.0)
        if st == "sleep":
            for col in (1, 5):
                px(col - 0.2, 2.3, col + 1.2, 2.7, EYE, dy=d)
        elif st in ("happy", "eat"):                        # occhi a "^ ^" e guance rosa
            for col in (1, 5):
                px(col - 0.15, 2.2, col + 0.35, 2.6, EYE, dy=d)
                px(col + 0.3, 1.8, col + 0.7, 2.2, EYE, dy=d)
                px(col + 0.65, 2.2, col + 1.15, 2.6, EYE, dy=d)
            px(0.1, 3.0, 1.1, 3.4, BLUSH, dy=d)
            px(5.9, 3.0, 6.9, 3.4, BLUSH, dy=d)
            if st == "eat" and int((now - self.since) / 0.15) % 2:
                px(3, 3.3, 4, 4.2, EYE, dy=d)               # bocca che mastica
        elif pw == "rockets":                               # occhialoni da aviatore
            px(0, 1.3, 7, 2.5, GOGGLE_STRAP, dy=d)
            for c0 in (0.6, 4.2):
                px(c0, 0.9, c0 + 2.2, 2.9, GOGGLE_STRAP, dy=d)
                px(c0 + 0.3, 1.2, c0 + 1.9, 2.6, GOGGLE_LENS, dy=d)
                px(c0 + 0.7, 1.5, c0 + 1.5, 2.4, EYE, dy=d)
        else:
            if st == "rise":
                ex, ey = 0.0, -0.35 * p                     # guarda in su
            elif lp in ("rise", "think"):
                ex, ey = -0.3 * p, -0.35 * p                # pensieroso, in alto a sinistra
            elif lp == "talk":
                ex, ey = 0.35 * p, -0.1 * p                 # guarda la lavagna
            elif st.startswith("portal"):
                ex, ey = self.portal["dir"] * 0.35 * p, 0.0  # guarda il portale
            elif st == "fly":
                ex, ey = self.act_dir * 0.4 * p, -0.1 * p    # sguardo deciso in avanti
            elif st in ("heropose", "flex"):
                ex, ey = 0.0, -0.1 * p                       # fiero, davanti a sé
            elif st == "pushup":
                ex, ey = 0.0, 0.35 * p                       # guarda in giù
            else:
                mx, my = self.mouse
                ex = max(-1.0, min(1.0, (mx - self.x) / 150)) * 0.35 * p
                ey = max(-1.0, min(1.0, (my - (self.y - PET_H / 2)) / 150)) * 0.3 * p
            top = 2 if now < self.blink_until else 1
            for col in (1, 5):
                px(col, top, col + 1, 3, EYE, dy=d + ey, dx=ex)
        if st in ("fall", "drag", "portal_open"):
            px(3, 3.4, 4, 4.3, EYE, dy=d)                   # boccuccia a "o"
        if lp and ang:                                      # sorriso da divulgatore
            px(2.4, 3.3, 4.6, 3.6, EYE, dy=d)
            if lp == "talk" and int(now / 0.12) % 2:
                px(2.9, 3.4, 4.1, 3.9, EYE, dy=d)           # parla
        elif lp:                                            # baffoni da professore
            px(1.6, 3.0, 5.4, 3.6, MUSTACHE, dy=d)
            px(1.3, 3.3, 1.8, 3.8, MUSTACHE, dy=d)
            px(5.2, 3.3, 5.7, 3.8, MUSTACHE, dy=d)
            if lp == "talk" and int(now / 0.12) % 2:
                px(3, 3.8, 4, 4.5, EYE, dy=d)               # parla


        if st == "sleep":                                   # zzz
            for k in range(3):
                f = (now * 0.6 + k / 3) % 1
                c.create_text(x + 2.5 * p + f * 14, y - 7 * p - f * 40, text="z",
                              fill="#6B6A65", font=("Segoe UI", int(7 + f * 6), "bold"),
                              tags=("pet",))
        if st == "hide":                    # sotto il bordo: colore trasparente = "dietro" la finestra
            c.create_rectangle(x - PET_W, y, x + PET_W, y + PET_H + 4 * p, fill=KEY, width=0)

    def draw_menu(self):
        c = self.c
        style = "Scintille" if self.portal_style == "sparks" else "Ovali"
        s = self.sys_status
        pc = (f"PC: {s['uptime_h']:.0f} h · mem {s['commit_pct']:.0f}% · "
              if s else "PC e spesa: ") + pet_work.spending_label(self.brain.data).split(" ·")[0]
        rows = (("menu_talk", "Parla con me", MENU_FG),
                ("menu_advice", "Dammi un consiglio", MENU_FG),
                ("menu_standup", "Standup di oggi", MENU_FG),
                ("menu_feed", "Dai da mangiare", MENU_FG),
                ("menu_ball", "Basta palla" if self.ball else "Gioca a palla", MENU_FG),
                ("menu_hide", "Nascondino", MENU_FG),
                ("menu_clip", "Appunti recenti", MENU_FG),
                ("menu_follow", "Segui il mouse: " + ("sì" if self.follow else "no"), MENU_FG),
                ("menu_portal", "Portale: " + style, MENU_FG),
                ("menu_cape", "Mantello: " + ("sì" if self.cape_on else "no"), MENU_FG),
                ("menu_power", "Potere: " + POWER_NAMES[self.power_pref], MENU_FG),
                ("menu_meeting", "Zitta in riunione: " + ("sì" if MEETING_MODE else "no"), MENU_FG),
                ("menu_pc", pc, "#6B6A65"),
                ("menu_chores", "Fai le pulizie", MENU_FG),
                ("menu_undo", "Annulla pulizie", MENU_FG),
                ("menu_propose", "Proponi miglioramenti", MENU_FG),
                ("menu_settings", "Impostazioni…", MENU_FG),
                ("menu_update", "Cerca aggiornamenti", MENU_FG),
                ("menu_forget", "Dimentica tutto", MENU_FG),
                ("menu_quit", "Esci", MENU_RED))
        rh = 24
        w, h = 220, len(rows) * rh + 4
        x0 = min(max(self.x - self.ox - w / 2, 4), int(c.cget("width")) - w - 4)
        y0 = max(self.y - self.oy - PET_H - 16 - h, 4)
        c.create_rectangle(x0, y0, x0 + w, y0 + h, fill=MENU_BG, outline=MENU_BORDER,
                           width=2, tags=("menu",))
        for i, (tag, label, fg) in enumerate(rows):
            ry = y0 + 2 + i * rh
            c.create_rectangle(x0 + 2, ry, x0 + w - 2, ry + rh, fill=MENU_BG,
                               width=0, tags=("menu", tag))
            c.create_text(x0 + 12, ry + rh / 2, text=label, anchor="w", fill=fg,
                          font=("Segoe UI", 9), tags=("menu", tag))


def apply_config(cfg):
    """Impostazioni (pet_config) nelle costanti di questo modulo e degli altri."""
    pet_config.apply(cfg, {"pet": sys.modules[__name__], "kn": pet_knowledge,
                           "watch": pet_watch, "chores": pet_chores})


def main():
    if "--after" in sys.argv:                # riavvio: aspetta che la vecchia mascotte esca
        pet_config.wait_for_exit(int(sys.argv[sys.argv.index("--after") + 1]))
    if not pet_config.mark_running("hoppy.pet"):
        return                               # c'è già una mascotte
    cfg = pet_config.load()
    apply_config(cfg)
    pet_config.drop_old_shortcuts()
    if START_COMPANIONS:
        pet_config.start_companions(clean_env())
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # coordinate fisiche come DWM
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    root.withdraw()                          # le finestre vere sono una per schermo
    pet = Pet(root)
    res = pet_update.take_result()          # appena aggiornata: com'è andata
    if res:
        text = (f"Eccomi! Ora sono la versione {str(res.get('tag', '')).lstrip('v')}." if res.get("ok")
                else "Non sono riuscita ad aggiornarmi: i dettagli sono in update.log, "
                     "nella cartella dei dati.")
        root.after(3000, lambda: pet.set_bubble("chat", text))
    if not cfg["wizard_done"]:               # prima volta: la presentazione
        root.after(1500, pet.open_wizard)
    root.mainloop()


if __name__ == "__main__":
    main()
