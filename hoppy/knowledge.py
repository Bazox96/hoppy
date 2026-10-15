"""Cosa sa la mascotte del tuo lavoro, tutto in locale.

- Progetti: le cartelle in ~/.claude/projects (e in quella del secondo profilo, se
  WORK_ENABLED), ricondotte al percorso vero su disco.
- Memorie: i file memory/*.md di Claude Code, letti e mai modificati. A ogni domanda
  ne vengono scelti solo i pochi pertinenti, così a Claude arrivano pochi KB. Comprese
  quelle del secondo profilo, se WORK_MEMORIES è acceso.
- Sessioni: le vostre chiacchierate, salvate in pet_sessions/ (una riga JSON per battuta).
- Avvio di Claude Code in PowerShell, solo nella cartella di un progetto noto: col
  secondo profilo (WORK_LAUNCHER o CLAUDE_CONFIG_DIR) per i suoi progetti, con claude per gli altri.

Non legge credenziali, settings.json, CLAUDE.md né le trascrizioni di Claude Code.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
# secondo profilo di Claude Code (es. di lavoro): un'altra CLAUDE_CONFIG_DIR. Dalle Impostazioni.
WORK_ENABLED = False
WORK_HOME = Path.home() / ".claude-work"
WORK_LABEL = "lavoro"       # come lo chiama la mascotte
WORK_LAUNCHER = ""          # comando del profilo PowerShell che lo avvia (vuoto: claude)
WORK_MEMORIES = False       # legge anche le sue memorie. Attenzione: i pezzi pertinenti
                            # vanno a Claude dall'account personale.
                            # False = conosce e apre i progetti di lavoro, ma non ne legge le memorie.
RELOAD_S = 600              # rilegge memorie e progetti al massimo ogni 10 minuti
RECENT_DAYS = 14            # "ultimamente lavori su": memorie toccate negli ultimi N giorni
STOP = set("""che chi cosa come dove quando perche per con una uno del della dello dei
delle degli gli le lo la il di da in su tra fra non sei sono hai ho mi ti ci si ma anche
piu questo questa quello quella ora poi fa fare fai mio mia tuo tua suo sua sul sulla
nel nella alla allo agli alle dal dalla the and you are what how""".split())


def norm(s):
    """Minuscolo e senza accenti, per confronti semplici."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def flat(s):
    """Solo lettere e cifre: 'my app be' e 'MyApp-BE' diventano uguali."""
    return re.sub(r"[^a-z0-9]", "", norm(s))


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", norm(text)) if len(w) >= 3 and w not in STOP]


def slugify(name):
    return re.sub(r"[^A-Za-z0-9]", "-", name)


def resolve_slug(slug):
    """Ritrova la cartella vera dal nome usato in ~/.claude/projects
    (es. D--Code-My-App -> D:\\Code\\My App), cercandola su disco."""
    m = re.match(r"([A-Za-z])--(.*)$", slug)
    if not m:
        return None

    def walk(base, rest):
        if not rest:
            return base
        try:
            names = os.listdir(base)
        except OSError:
            return None
        for n in sorted(names, key=len, reverse=True):   # prima i nomi più lunghi
            s = slugify(n)
            if rest == s or rest.startswith(s + "-"):
                p = os.path.join(base, n)
                if os.path.isdir(p):
                    found = walk(p, rest[len(s) + 1:])
                    if found:
                        return found
        return None

    return walk(m.group(1).upper() + ":\\", m.group(2))


def parse_front(raw):
    """Frontmatter '---' semplice (chiave: valore, anche annidato); ritorna (meta, corpo)."""
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            meta = {}
            for line in raw[3:end].splitlines():
                k, sep, v = line.strip().partition(":")
                if sep and v.strip():
                    meta[k.strip()] = v.strip()
            return meta, raw[end + 4:]
    return {}, raw


def project_roots():
    """Le cartelle projects di Claude Code: la tua e, se c'è, quella del secondo profilo."""
    return [CLAUDE_PROJECTS] + ([Path(WORK_HOME) / "projects"] if WORK_ENABLED else [])


class Knowledge:
    """Progetti e memorie di Claude Code, in sola lettura."""

    def __init__(self, personal=None, work=None):
        roots = project_roots()
        personal = personal or roots[0]
        work = work or (roots[1] if len(roots) > 1 else None)
        self.roots = [(Path(personal), False)] + ([(Path(work), True)] if work else [])
        self.projects = {}      # nome leggibile -> percorso (solo cartelle esistenti)
        self.work = set()       # percorsi (normcase) dei progetti del secondo profilo
        self.docs = []
        self.loaded = 0.0
        self.reload()

    def maybe_reload(self):
        if time.time() - self.loaded > RELOAD_S:
            self.reload()

    def is_work(self, path):
        """Il progetto è del secondo profilo? Allora si apre con quello (WORK_LAUNCHER)."""
        return os.path.normcase(path) in self.work

    def reload(self):
        self.loaded = time.time()
        found = []                           # (cartella projects, slug, è lavoro?)
        for root, work in self.roots:
            try:
                found += [(root, p.name, work) for p in sorted(root.iterdir()) if p.is_dir()]
            except OSError:
                pass
        home = os.path.normcase(str(Path.home()))
        tmp = os.path.normcase(tempfile.gettempdir())
        where = {}                           # (root, slug) -> percorso vero
        for root, slug, _ in found:
            p = resolve_slug(slug)
            if not p:
                continue
            np_ = os.path.normcase(p)
            if np_ == home or np_ == tmp or np_.startswith(tmp + os.sep):
                continue                     # la home e le cartelle temporanee non sono progetti
            where[(root, slug)] = p
        paths = {os.path.normcase(p): p for p in where.values()}   # stesso progetto: una volta

        def parent_of(p):                    # progetto più vicino che contiene p
            return max((q for q in paths.values() if q != p
                        and os.path.normcase(p).startswith(os.path.normcase(q) + os.sep)),
                       key=len, default=None)

        kids = Counter(parent_of(p) for p in paths.values())
        name_of = {}
        for p in paths.values():             # sottoprogetto: "Padre/figlio", ma non sotto
            parent = parent_of(p)            # i contenitori (es. "Progetti GitHub")
            base = os.path.basename(p)
            name_of[os.path.normcase(p)] = (f"{os.path.basename(parent)}/{base}"
                                            if parent and kids[parent] < 3 else base)
        self.projects = {name_of[k]: p for k, p in paths.items()}
        self.work = {os.path.normcase(where[(root, slug)]) for root, slug, work in found
                     if work and (root, slug) in where}
        docs = []
        for root, slug, work in found:
            if work and not WORK_MEMORIES:   # memorie di lavoro: non vanno all'account personale
                continue
            p = where.get((root, slug))
            label = name_of[os.path.normcase(p)] if p else slug.split("--", 1)[-1]
            mdir = root / slug / "memory"
            if not mdir.is_dir():
                continue
            for f in sorted(mdir.glob("*.md")):
                if f.name == "MEMORY.md":    # è solo l'indice dei file qui sotto
                    continue
                try:
                    raw = f.read_text(encoding="utf-8", errors="replace")
                    mtime = f.stat().st_mtime
                except OSError:
                    continue
                meta, body = parse_front(raw)
                name, desc = meta.get("name") or f.stem, meta.get("description", "")
                docs.append({"project": label, "name": name, "desc": desc,
                             "type": meta.get("type", ""), "body": body.strip(), "mtime": mtime,
                             "head": Counter(words(name + " " + desc)),
                             "text": Counter(words(body))})
        self.docs = docs

    def recent_projects(self):
        limit = time.time() - RECENT_DAYS * 86400
        seen = []
        for d in sorted(self.docs, key=lambda d: -d["mtime"]):
            if d["mtime"] >= limit and d["project"] not in seen:
                seen.append(d["project"])
        return seen[:5]

    def overview(self):
        """Poche righe sempre presenti: i progetti e chi è l'utente."""
        self.maybe_reload()
        parts = []
        mine = sorted((n for n, p in self.projects.items() if not self.is_work(p)), key=str.lower)
        work = sorted((n for n, p in self.projects.items() if self.is_work(p)), key=str.lower)
        if mine:
            parts.append("I suoi progetti: " + ", ".join(mine) + ".")
        if work:
            parts.append(f"I suoi progetti di {WORK_LABEL} (si aprono con "
                         f"{WORK_LAUNCHER or 'il profilo ' + WORK_LABEL}): " + ", ".join(work) + ".")
        rec = self.recent_projects()
        if rec:
            parts.append("Ultimamente ci lavora su: " + ", ".join(rec) + ".")
        about = [d["body"][:300] for d in self.docs if d["type"] == "user"][:3]
        if about:
            parts.append("Su di lui: " + " ".join(about))
        return " ".join(parts)

    def search(self, query, k=3, budget=4500):
        """Le memorie più pertinenti alla frase, come testo da dare a Claude ('' se nessuna)."""
        self.maybe_reload()
        q = set(words(query))
        if not q:
            return ""
        fq = flat(query)
        scored = []
        for d in self.docs:
            s = sum(3 * d["head"][t] + min(d["text"][t], 3) for t in q)
            if flat(d["project"].split("/")[-1]) in fq:
                s += 4                       # nomina il progetto: le sue memorie contano di più
            if s > 0:
                scored.append((s, d["mtime"], d))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        out, used = [], 0
        for _, _, d in scored[:k]:
            room = min(1500, budget - used)
            if room < 200:
                break
            piece = f"[{d['project']}] {d['name']} — {d['desc']}\n{d['body'][:room]}"
            out.append(piece)
            used += len(piece)
        return "\n\n".join(out)

    def name_of(self, cwd):
        """Nome del progetto che contiene la cartella cwd (il più specifico), o il nome della cartella."""
        c = os.path.normcase(os.path.abspath(cwd)) if cwd else ""
        best = max(((n, p) for n, p in self.projects.items()
                    if c == os.path.normcase(p) or c.startswith(os.path.normcase(p) + os.sep)),
                   key=lambda np: len(np[1]), default=None)
        return best[0] if best else (Path(cwd).name if cwd else "una sessione")

    def skills(self):
        """Le skill dei profili di Claude Code: [(nome, descrizione, di lavoro?)]."""
        out = [(n, d, False) for n, d in read_skills(CLAUDE_PROJECTS.parent).items()]
        if WORK_ENABLED:
            out += [(n, d, True) for n, d in read_skills(WORK_HOME).items()]
        return out

    def skills_hint(self):
        """Le skill in una riga per il prompt (solo quando chiedi di aprire qualcosa)."""
        return "; ".join(f"{n} ({WORK_LABEL if w else 'personale'}): {d}"
                         for n, d, w in self.skills())

    def find_project(self, name):
        """Percorso del progetto col nome dato (esatto, poi parziale), o (None, None)."""
        self.maybe_reload()
        n = flat(name)
        for key, p in self.projects.items():
            if flat(key) == n or flat(key.split("/")[-1]) == n:
                return key, p
        hits = [(k, p) for k, p in self.projects.items() if n and n in flat(k)]
        return min(hits, key=lambda kp: len(kp[0])) if hits else (None, None)


class Sessions:
    """Le vostre conversazioni, una per file in <folder>/<id>.jsonl."""

    def __init__(self, folder):
        self.dir = Path(folder)

    @staticmethod
    def new_id():
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")

    def append(self, sid, who, text):
        try:
            self.dir.mkdir(exist_ok=True)
            with (self.dir / f"{sid}.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"t": datetime.now().isoformat(timespec="seconds"),
                                     "who": who, "text": text}, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def load(self, sid):
        try:
            lines = (self.dir / f"{sid}.jsonl").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for line in lines:
            try:
                r = json.loads(line)
                out.append((r["who"], r["text"]))
            except (ValueError, KeyError, TypeError):
                continue
        return out

    def search(self, query, exclude=None, k=2, budget=1800):
        """Scambi passati che c'entrano con la frase, con la data ('' se nessuno)."""
        q = set(words(query))
        if not q or not self.dir.is_dir():
            return ""
        hits = []
        for f in self.dir.glob("*.jsonl"):
            if f.stem == exclude:
                continue
            turns = self.load(f.stem)
            for i, (who, text) in enumerate(turns):
                s = sum(Counter(words(text))[t] for t in q)
                if s:
                    hits.append((s, f.stem, turns[i:i + 2]))
        hits.sort(key=lambda h: h[1], reverse=True)    # a parità di punteggio, le più recenti
        hits.sort(key=lambda h: -h[0])
        out, used = [], 0
        for _, sid, pair in hits[:k]:
            day = f"{sid[8:10]}/{sid[5:7]}"
            piece = f"({day}) " + " / ".join(f"{w}: {t[:300]}" for w, t in pair)
            if used + len(piece) > budget:
                break
            out.append(piece)
            used += len(piece)
        return "\n".join(out)

    def forget(self):
        if self.dir.is_dir():
            for f in self.dir.glob("*.jsonl"):
                try:
                    f.unlink()
                except OSError:
                    pass


def clean_env():
    """L'ambiente senza i segni di "sei dentro un'altra sessione di Claude Code".

    Se la mascotte è stata avviata da una sessione di Claude Code ne eredita CLAUDECODE,
    CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_CHILD_SESSION...: un `claude` lanciato con quelle
    variabili si crede una sotto-sessione e non salva la propria trascrizione. Le variabili
    che servono davvero (es. CLAUDE_CODE_PLUGIN_DIRS) Claude Code le rimette da settings.json.
    Toglie anche NO_COLOR, che i terminali degli strumenti di Claude Code impostano e che
    spegnerebbe i colori della console (chi la vuole davvero la mette nel profilo PowerShell),
    e CLAUDE_CONFIG_DIR: la configurazione la sceglie chi lancia (claude o claude-gen).
    """
    return {k: v for k, v in os.environ.items()
            if not (k.upper() in ("CLAUDECODE", "CLAUDE_PID", "NO_COLOR", "CLAUDE_CONFIG_DIR")
                    or k.upper().startswith("CLAUDE_CODE_"))}


def read_skills(home):
    """Le skill di un profilo di Claude Code (<home>/skills/*/SKILL.md): {nome: descrizione}."""
    out = {}
    for f in sorted(Path(home).glob("skills/*/SKILL.md")):
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            continue
        m = re.match(r"---\s*\n(.*?)\n---", head, re.S)
        meta = m.group(1) if m else ""
        name = re.search(r"^name:\s*(.+)$", meta, re.M)
        name = name.group(1).strip().strip("'\"") if name else f.parent.name
        desc = re.search(r"^description:\s*(?:[>|]-?\s*\n)?((?:.+\n?)(?:[ \t]+.+\n?)*)", meta + "\n", re.M)
        desc = " ".join(desc.group(1).split()).strip("'\"") if desc else ""
        if re.fullmatch(r"[\w.:-]+", name):
            out[name] = desc[:120]
    return out


def launch_claude(path, title, work=False, prompt=""):
    """Apre PowerShell (col tuo profilo) nella cartella del progetto e ci avvia Claude Code:
    con claude-gen se è un progetto di lavoro, con claude altrimenti; prompt (es. "/jira X")
    parte subito come primo messaggio. True se è partita."""
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not (shell and Path(exe).exists() and os.path.isdir(path)):
        return False

    def q(s):                                # stringa PowerShell tra apici singoli
        return "'" + str(s).replace("'", "''") + "'"

    arg = " " + q(" ".join(prompt.split())[:300]) if prompt.strip() else ""
    if work:                                 # il comando sta nel profilo; senza, fa lo stesso
        direct = f"$env:CLAUDE_CONFIG_DIR = {q(WORK_HOME)}; & {q(exe)}"
        cmd = WORK_LAUNCHER.strip()
        run = (f"if (Get-Command {q(cmd)} -ErrorAction SilentlyContinue) {{ & {q(cmd)}{arg} }} "
               f"else {{ {direct}{arg} }}") if cmd else direct + arg
        title += f" - Claude {WORK_LABEL}"
    else:
        run = f"& {q(exe)}{arg}"
        title += " - Claude"
    command = f"$Host.UI.RawUI.WindowTitle = {q(title)}; {run}"
    env = clean_env()
    env["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] = "1"   # il titolo resta il nome del progetto
    try:
        subprocess.Popen([shell, "-NoExit", "-Command", command], cwd=path, env=env,
                         creationflags=0x00000010)   # CREATE_NEW_CONSOLE: finestra sua
    except OSError:
        return False
    return True
