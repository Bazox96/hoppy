"""Cosa osserva la mascotte, senza mai avviare processi (solo API di Windows e file).

- system_status(): ore di accensione e memoria (per accorgersi di memoria che non torna libera).
- mic_users() / fullscreen_state(): microfono in uso (call), schermo intero / presentazione.
- ClaudeWatch: le sessioni di Claude Code che hanno finito o aspettano un permesso.
- Clipboard: gli ultimi testi copiati (solo in RAM, mai le password).
"""
import ctypes
import ctypes.wintypes as wt
import json
import re
import time
import winreg
from pathlib import Path

user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32


# ---- memoria e accensione -----------------------------------------------------
class _PerfInfo(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD)] + [(n, ctypes.c_size_t) for n in (
        "CommitTotal", "CommitLimit", "CommitPeak", "PhysicalTotal", "PhysicalAvailable",
        "SystemCache", "KernelTotal", "KernelPaged", "KernelNonpaged", "PageSize")] + [
        ("HandleCount", wt.DWORD), ("ProcessCount", wt.DWORD), ("ThreadCount", wt.DWORD)]


kernel32.GetTickCount64.restype = ctypes.c_uint64


def system_status():
    """{'uptime_h', 'commit_pct', 'commit_gb', 'limit_gb', 'nonpaged_gb'}"""
    pi = _PerfInfo()
    pi.cb = ctypes.sizeof(pi)
    ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(pi), pi.cb)
    gb = pi.PageSize / 2**30
    return {"uptime_h": kernel32.GetTickCount64() / 3.6e6,
            "commit_pct": 100 * pi.CommitTotal / max(1, pi.CommitLimit),
            "commit_gb": pi.CommitTotal * gb, "limit_gb": pi.CommitLimit * gb,
            "nonpaged_gb": pi.KernelNonpaged * gb}


# ---- riunioni -------------------------------------------------------------------
MIC_KEY = (r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager"
           r"\ConsentStore\microphone")


def mic_users():
    """App che stanno usando il microfono adesso (Teams, Zoom, browser...)."""
    out = []

    def walk(path):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
        except OSError:
            return
        with k:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                try:
                    with winreg.OpenKey(k, sub) as s:
                        if (winreg.QueryValueEx(s, "LastUsedTimeStop")[0] == 0
                                and winreg.QueryValueEx(s, "LastUsedTimeStart")[0]):
                            out.append(sub.split("#")[-1])
                except OSError:
                    pass
                if sub == "NonPackaged":
                    walk(path + "\\" + sub)
    walk(MIC_KEY)
    return out


def fullscreen_state():
    """2 = app a schermo intero, 3 = gioco/video D3D, 4 = modalità presentazione."""
    st = ctypes.c_int()
    if ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(st)) != 0:
        return 0
    return st.value


# ---- sessioni di Claude Code --------------------------------------------------------
WAIT_S = 25          # tool fermo da tanto senza risultato: probabilmente aspetta il tuo permesso
ACTIVE_S = 30 * 60   # guarda solo le sessioni toccate negli ultimi 30 minuti
TAIL = 96 * 1024


def last_turn(path):
    """Stato della sessione dalle ultime righe: 'done', 'tool' o 'working' (+ cwd)."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - TAIL))
            lines = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None, ""
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        t = rec.get("type")
        if t == "user":
            return "working", rec.get("cwd", "")
        if t == "assistant":
            stop = (rec.get("message") or {}).get("stop_reason")
            if stop == "tool_use":
                return "tool", rec.get("cwd", "")
            if stop in ("end_turn", "stop_sequence", "max_tokens"):
                return "done", rec.get("cwd", "")
            return "working", rec.get("cwd", "")
    return None, ""


class ClaudeWatch:
    """Segue le sessioni attive e segnala quando una ha finito o aspetta un permesso."""

    def __init__(self, roots):
        self.roots = [Path(r) for r in roots]
        self.seen = {}               # file -> (mtime, stato, già segnalata l'attesa)
        self.cwd = {}                # file -> cartella del progetto

    def poll(self, now=None):
        now = now or time.time()
        events = []
        for root in self.roots:
            try:
                files = [f for f in root.glob("*/*.jsonl")]
            except OSError:
                continue
            for f in files:
                try:
                    mt = f.stat().st_mtime
                except OSError:
                    continue
                if now - mt > ACTIVE_S:
                    self.seen.pop(f, None)
                    continue
                old = self.seen.get(f)
                if old and old[0] == mt:
                    st, warned = old[1], old[2]
                    if st == "tool" and not warned and now - mt >= WAIT_S:
                        self.seen[f] = (mt, st, True)
                        events.append(("waiting", self.cwd.get(f, "")))
                    continue
                st, cwd = last_turn(f)
                if cwd:
                    self.cwd[f] = cwd
                if old and st == "done" and old[1] in ("working", "tool"):
                    events.append(("done", self.cwd.get(f, "")))
                self.seen[f] = (mt, st, False)
        return events                # [(done|waiting, cartella della sessione)]


# ---- appunti ----------------------------------------------------------------------
CF_UNICODETEXT = 13
user32.GetClipboardData.restype = wt.HANDLE
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [wt.HANDLE]
kernel32.GlobalUnlock.argtypes = [wt.HANDLE]
_EXCLUDE = user32.RegisterClipboardFormatW("ExcludeClipboardContentFromMonitorProcessing")
_NO_HISTORY = user32.RegisterClipboardFormatW("CanIncludeInClipboardHistory")
SECRET_RE = re.compile(
    r"(?i)(pass(word|wd)?|secret|token|api[_-]?key|bearer|authorization)\s*[:=]"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY|\bAKIA[0-9A-Z]{16}\b|\beyJ[\w-]{10,}\.[\w-]{10,}"
    r"|\b(sk|ghp|gho|xox[bp])[-_][\w-]{16,}")
ERROR_RE = re.compile(
    r"Traceback \(most recent call last\)|\b\w+(Exception|Error)\b[:\s]|\bat [\w.$<>]+\(\S*:\d+\)"
    r"|^\s*(ERROR|FATAL|FAILED|panic:)|npm ERR!|error TS\d+|BUILD FAILURE", re.M)


def looks_secret(text):
    t = text.strip()
    if SECRET_RE.search(t):
        return True
    # una sola "parola" lunga con lettere, numeri e simboli: probabile password o token
    if " " not in t and "\n" not in t and 12 <= len(t) <= 200 and not re.match(r"https?://|[A-Za-z]:\\|/", t):
        classes = sum(bool(re.search(p, t)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^\w]"))
        return classes >= 3
    return False


def looks_like_error(text):
    return len(text) >= 40 and bool(ERROR_RE.search(text))


def read_clipboard_text():
    """(letto, testo): letto=False se gli appunti sono occupati da un altro programma;
    testo=None se non c'è testo o è segnato come privato (i password manager lo fanno)."""
    if not user32.OpenClipboard(None):
        return False, None
    try:
        if user32.IsClipboardFormatAvailable(_EXCLUDE) or user32.IsClipboardFormatAvailable(_NO_HISTORY):
            return True, None
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return True, None
        p = kernel32.GlobalLock(h)
        if not p:
            return True, None
        try:
            return True, ctypes.wstring_at(p)
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()


class Clipboard:
    """Ultimi testi copiati, solo in memoria (si perdono chiudendo la mascotte)."""
    KEEP = 20

    def __init__(self):
        self.seq = user32.GetClipboardSequenceNumber()
        self.items = []

    def poll(self):
        """Il testo appena copiato (se nuovo e non segreto), altrimenti None."""
        seq = user32.GetClipboardSequenceNumber()
        if seq == self.seq:
            return None
        ok, text = read_clipboard_text()
        if not ok:
            return None                      # appunti occupati: riprova al prossimo giro
        self.seq = seq
        if text is None:
            return None                      # niente testo, o privato
        text = text[:20000]
        if not text.strip() or looks_secret(text):
            return None
        self.items = [t for t in self.items if t != text]
        self.items.insert(0, text)
        del self.items[self.KEEP:]
        return text
