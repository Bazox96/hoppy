"""Faccende della mascotte: riordino del desktop e caccia ai file vecchi.

Non cancella mai nulla: sposta soltanto, e solo dopo il tuo sì. Ogni giro di
spostamenti finisce in un registro (pet_chores.json) e si può annullare.

- Desktop: i file sciolti (non cartelle, non collegamenti, non nascosti) non toccati da
  almeno RECENT_DAYS giorni vanno in sottocartelle per mese, tipo "2026-10" (data di modifica).
- File vecchi: nel Desktop (anche nelle cartelle per mese) e in Download, i file non
  aperti né modificati da OLD_DAYS giorni vanno in una cartella "Da rivedere" accanto.
Tutto resta sullo stesso disco (anche OneDrive: è solo una rinomina, nessun download).
- Build dei progetti fermi (node_modules, target, .next, build) e cache Maven vecchia:
  queste sì si eliminano davvero (dopo il tuo sì), perché si rigenerano da sole.
"""
import ctypes
import json
import os
import re
import shutil
import time
from pathlib import Path

from .i18n import T

RECENT_DAYS = 7          # i file toccati da poco restano dove sono: ci stai lavorando
OLD_DAYS = 180           # "vecchio e non usato": niente modifiche né aperture da 6 mesi
REVIEW_DIR = "Da rivedere"
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
SKIP_EXT = {".lnk", ".url", ".ini", ".tmp", ".crdownload", ".part", ".partial"}
FILE_ATTRIBUTE_HIDDEN, FILE_ATTRIBUTE_SYSTEM = 0x2, 0x4
LOG_KEEP = 20            # giri di spostamenti ricordati (per annullare)


def known_folder(name):
    """Desktop e Download veri (anche se spostati in OneDrive)."""
    if name == "desktop":
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)  # CSIDL_DESKTOPDIRECTORY
        return Path(buf.value)
    guid = ctypes.c_byte * 16
    fid = guid.from_buffer_copy(bytes.fromhex("90e24d373f126545916439c4925e467b"))  # FOLDERID_Downloads
    p = ctypes.c_wchar_p()
    ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, None, ctypes.byref(p))
    out = Path(p.value)
    ctypes.windll.ole32.CoTaskMemFree(p)
    return out


def loose_files(folder):
    """File "veri" di una cartella (primo livello): niente collegamenti, nascosti, temporanei."""
    out = []
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return out
    for e in entries:
        try:
            if not e.is_file(follow_symlinks=False):
                continue
            st = e.stat(follow_symlinks=False)
        except OSError:
            continue
        if (Path(e.name).suffix.lower() in SKIP_EXT or e.name.startswith("~$")
                or st.st_file_attributes & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)):
            continue
        out.append((Path(e.path), st))
    return out


def last_used(st):
    """Ultimo uso: la più recente fra modifica, apertura e arrivo (creazione) del file."""
    return max(st.st_mtime, st.st_atime, st.st_ctime)


def desktop_plan(desktop, now=None):
    now = now or time.time()
    moves = []
    for p, st in loose_files(desktop):
        if now - last_used(st) < RECENT_DAYS * 86400:
            continue
        month = time.strftime("%Y-%m", time.localtime(st.st_mtime))
        moves.append((p, desktop / month / p.name, st.st_size))
    return moves


def old_plan(folders, now=None):
    """folders: Desktop e Download. Nel Desktop guarda anche dentro le cartelle per mese."""
    now = now or time.time()
    moves = []
    for root in folders:
        dirs = [root]
        try:
            dirs += [Path(e.path) for e in os.scandir(root)
                     if e.is_dir(follow_symlinks=False) and MONTH_RE.match(e.name)]
        except OSError:
            continue
        for d in dirs:
            for p, st in loose_files(d):
                if now - last_used(st) >= OLD_DAYS * 86400:
                    moves.append((p, root / REVIEW_DIR / p.name, st.st_size))
    return moves


def free_name(dst):
    """dst se libero, altrimenti "nome (2).ext", "nome (3).ext", ..."""
    n = 2
    out = dst
    while out.exists():
        out = dst.with_name(f"{dst.stem} ({n}){dst.suffix}")
        n += 1
    return out


def apply(moves):
    """Sposta (rinomina) i file; restituisce (fatti, falliti). Mai sovrascritture."""
    done, failed = [], 0
    for src, dst, _size in moves:
        try:
            dst.parent.mkdir(exist_ok=True)
            real = free_name(dst)
            os.rename(src, real)              # stesso disco: rinomina, non copia
            done.append((str(src), str(real)))
        except OSError:
            failed += 1                       # aperto in un programma, permessi...: resta lì
    return done, failed


def undo(done):
    """Rimette a posto i file di un giro; le cartelle rimaste vuote spariscono."""
    back, failed = 0, 0
    for src, dst in reversed(done):
        try:
            os.rename(dst, free_name(Path(src)))
            back += 1
        except OSError:
            failed += 1
    for d in {Path(dst).parent for _src, dst in done}:
        try:
            d.rmdir()                         # solo se vuota
        except OSError:
            pass
    return back, failed


class ChoreLog:
    """Registro dei giri di spostamenti (per "Annulla ultime pulizie")."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def add(self, kind, done):
        log = self.load() + [{"t": time.strftime("%Y-%m-%d %H:%M"), "kind": kind, "moves": done}]
        self.path.write_text(json.dumps(log[-LOG_KEEP:], ensure_ascii=False, indent=1),
                             encoding="utf-8")

    def pop(self):
        log = self.load()
        if not log:
            return None
        last = log.pop()
        self.path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        return last


# ---- pulizie da sviluppatore: build rigenerabili dei progetti fermi --------------------
DEV_STALE_DAYS = 60      # progetto senza modifiche da N giorni: le sue build si possono buttare
M2_STALE_DAYS = 180      # versioni della cache Maven non usate da N giorni
# cartella di build -> file che deve stare accanto (così "target" o "build" a caso non si toccano)
JUNK = {"node_modules": "package.json", ".next": "package.json", "target": "pom.xml",
        "build": "build.gradle", ".gradle": "build.gradle"}
SKIP_WALK = set(JUNK) | {".git", ".venv", "venv", "__pycache__", ".idea"}


def tree_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def newest_change(project, after):
    """True se nel progetto (build escluse) c'è un file modificato dopo `after`."""
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_WALK]
        for f in files:
            try:
                if os.stat(os.path.join(root, f)).st_mtime > after:
                    return True
            except OSError:
                pass
    return False


def dev_plan(projects, now=None, depth=3):
    """Cartelle di build dei progetti fermi da DEV_STALE_DAYS: [(cartella, None, byte)].
    Un progetto toccato di recente in qualunque punto (anche in un altro sottoprogetto) si salta."""
    now = now or time.time()
    cut = now - DEV_STALE_DAYS * 86400
    found, seen = [], set()
    for proj in projects:
        base = Path(proj)
        if not base.is_dir() or newest_change(base, cut):
            continue
        stack = [(base, 0)]
        while stack:
            d, lev = stack.pop()
            try:
                subs = [e for e in os.scandir(d) if e.is_dir(follow_symlinks=False)]
            except OSError:
                continue
            for e in subs:
                p = Path(e.path)
                key = str(p).lower()
                if e.name in JUNK and (d / JUNK[e.name]).exists() or (
                        e.name == "build" and (d / "build.gradle.kts").exists()):
                    if key not in seen:
                        seen.add(key)
                        found.append((p, None, tree_size(p)))
                elif e.name not in SKIP_WALK and lev < depth:
                    stack.append((p, lev + 1))
    return found


def m2_plan(repo=None, now=None):
    """Versioni in ~/.m2/repository non usate da M2_STALE_DAYS (si riscaricano da sole)."""
    repo = Path(repo or Path.home() / ".m2" / "repository")
    now = now or time.time()
    out = []
    for root, dirs, files in os.walk(repo):
        if not any(f.endswith(".pom") for f in files):
            continue
        dirs[:] = []                          # cartella di una versione: non scendere oltre
        used, size = 0.0, 0
        for f in files:
            try:
                st = os.stat(os.path.join(root, f))
            except OSError:
                continue
            used, size = max(used, st.st_mtime, st.st_atime), size + st.st_size
        if now - used >= M2_STALE_DAYS * 86400:
            out.append((Path(root), None, size))
    return out


def delete_dirs(items):
    """Elimina definitivamente le cartelle (solo build rigenerabili). (byte liberati, fallite)."""
    freed, failed = 0, 0

    def unlock(func, path, _exc):             # file in sola lettura (es. .git dentro node_modules)
        try:
            os.chmod(path, 0o666)
            func(path)
        except OSError:
            pass
    for path, _dst, size in items:
        try:
            shutil.rmtree(path, onerror=unlock)
        except OSError:
            pass
        if Path(path).exists():
            failed += 1
        else:
            freed += size
    return freed, failed


def size_label(n):
    return f"{n / 2**30:.1f} GB" if n >= 2**30 else f"{n / 2**20:.0f} MB" if n >= 2**20 else T("pochi KB")
