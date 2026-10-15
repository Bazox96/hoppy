"""Aiuti per il lavoro: standup del mattino, git in sospeso, comandi rapidi, spesa.

- standup_material(): cosa hai fatto l'ultimo giorno lavorativo, dalle sessioni di
  Claude Code (personali e di lavoro) e dai commit dei repo.
- git_scan(): per ogni repo, modifiche non committate dimenticate e commit non pushati.
  Avvia `git` (2 processi per repo): si usa una volta al giorno.
- Commands: i comandi in pet_commands.json, lanciati in una finestra PowerShell nuova.
- Spending: quanto spende la mascotte in chiamate a Claude, mese per mese.
"""
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .knowledge import clean_env

FORGOTTEN_DAYS = 2       # modifiche non committate ferme da almeno N giorni
NO_WINDOW = 0x08000000


def prev_workday(today=None):
    """Inizio dell'ultimo giorno lavorativo (il lunedì guarda da venerdì, weekend compreso)."""
    today = today or datetime.now()
    d = today.date() - timedelta(days=3 if today.weekday() == 0 else 1)
    if today.weekday() == 6:
        d = today.date() - timedelta(days=2)
    return datetime(d.year, d.month, d.day)


# ---- sessioni di Claude Code ----------------------------------------------------
AUTO_PROMPTS = ("This session is being continued", "Caveat:", "[Request interrupted")


def session_prompts(roots, since, until, name_of=None):
    """{progetto: [richieste che hai scritto a Claude]} nell'intervallo [since, until).
    name_of(cwd) dà il nome del progetto (default: il nome della cartella)."""
    name_of = name_of or (lambda cwd: Path(cwd).name)
    s_utc = since.astimezone(timezone.utc)
    u_utc = until.astimezone(timezone.utc)
    out = {}
    for root in roots:
        for f in Path(root).glob("*/*.jsonl"):
            try:
                if datetime.fromtimestamp(f.stat().st_mtime) < since:
                    continue
                fh = open(f, encoding="utf-8", errors="replace")
            except OSError:
                continue
            with fh:
                for line in fh:
                    if '"user"' not in line or '"tool_result"' in line:   # scarto veloce
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    text = (rec.get("message") or {}).get("content")
                    if (rec.get("isMeta") or not isinstance(text, str)
                            or text.lstrip().startswith(("<",) + AUTO_PROMPTS)):
                        continue
                    try:
                        ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                    except (KeyError, ValueError):
                        continue
                    if s_utc <= ts < u_utc:
                        name = name_of(rec.get("cwd") or f.parent.name)
                        out.setdefault(name, []).append(" ".join(text.split())[:160])
    return out


# ---- git --------------------------------------------------------------------------
def _git(args, cwd):
    exe = shutil.which("git")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *args], cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30, env=clean_env(),
                           creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _emails(repo):
    """Le tue email per git: quella globale e quella del repo (lette dai file, senza git)."""
    out = set()
    for cfg in (Path.home() / ".gitconfig", Path(repo) / ".git" / "config"):
        try:
            out |= set(re.findall(r"(?im)^\s*email\s*=\s*(\S+)", cfg.read_text(encoding="utf-8")))
        except OSError:
            pass
    return {e.lower() for e in out}


def git_scan(paths, since=None, until=None, now=None):
    """Per ogni repo: branch, modifiche dimenticate, commit non pushati, tuoi commit nell'intervallo."""
    now = now or datetime.now().timestamp()
    repos, seen = [], set()
    for p in paths:
        p = Path(p)
        if not (p / ".git").exists() or p.resolve() in seen:
            continue
        seen.add(p.resolve())
        st = _git(["status", "--porcelain=v2", "--branch"], p)
        if st is None:
            continue
        info = {"name": p.name, "path": str(p), "branch": "", "ahead": 0, "dirty": 0,
                "dirty_age_d": 0.0, "commits": []}
        newest = 0.0
        for line in st.splitlines():
            if line.startswith("# branch.head "):
                info["branch"] = line.split(" ", 2)[2]
            elif line.startswith("# branch.ab "):
                info["ahead"] = int(line.split()[2].lstrip("+"))
            elif line[:2] in ("1 ", "2 ", "u "):
                info["dirty"] += 1
                rel = line.split(" ", 8 if line[0] == "1" else 9 if line[0] == "2" else 10)[-1]
                try:
                    newest = max(newest, (p / rel.split("\t")[0]).stat().st_mtime)
                except OSError:
                    pass
        if info["dirty"]:
            info["dirty_age_d"] = (now - newest) / 86400 if newest else 0.0
        if since and until:
            log = _git(["log", "--all", f"--since={since:%Y-%m-%d %H:%M}",
                        f"--until={until:%Y-%m-%d %H:%M}", "--format=%ae%x09%s"], p) or ""
            mine = _emails(p)
            for line in log.splitlines():
                email, _, subj = line.partition("\t")
                if not mine or email.lower() in mine:
                    info["commits"].append(subj)
        repos.append(info)
    return repos


def pending_lines(repos):
    """Le righe "in sospeso" da mostrare: lavoro dimenticato e commit da pushare."""
    out = []
    for r in repos:
        if r["dirty"] and r["dirty_age_d"] >= FORGOTTEN_DAYS:
            out.append(f"{r['name']}: {r['dirty']} file modificati e non committati da "
                       f"{round(r['dirty_age_d'])} giorni")
        if r["ahead"]:
            out.append(f"{r['name']}: {r['ahead']} commit su {r['branch']} non ancora pushati")
    return out


def standup_prompt(prompts, repos, since):
    parts = [f"Ultimo giorno lavorativo: {since:%A %d/%m}."]
    for name, items in sorted(prompts.items(), key=lambda kv: -len(kv[1])):
        parts.append(f"Sessioni Claude Code su {name} ({len(items)} richieste): "
                     + " | ".join(items[:4]))
    for r in repos:
        if r["commits"]:
            parts.append(f"Commit su {r['name']}: " + " | ".join(r["commits"][:6]))
    return "\n".join(parts)


STANDUP_SYSTEM = (
    "Scrivi lo standup del mattino di uno sviluppatore, in italiano, dai dati sotto. "
    "Tre sezioni brevi con titolo in grassetto (**Ieri**, **Oggi**, **Blocchi**): elenchi "
    "puntati con '- ', al massimo 5 punti per sezione, frasi corte in prima persona. "
    "In **Oggi** proponi il seguito naturale del lavoro di ieri. In **Blocchi** scrivi "
    "'Nessuno' se non emerge nulla. Niente premesse né saluti.")


# ---- comandi rapidi ----------------------------------------------------------------
class Commands:
    """pet_commands.json: [{"nome", "descrizione", "comando", "cartella"}]."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return [c for c in data if isinstance(c, dict) and c.get("nome") and c.get("comando")]

    def find(self, name):
        name = name.strip().lower()
        cmds = self.load()
        return (next((c for c in cmds if c["nome"].lower() == name), None)
                or next((c for c in cmds if name in c["nome"].lower()), None))

    def hint(self):
        cmds = self.load()
        return "; ".join(f"«{c['nome']}» ({c.get('descrizione', '')})" for c in cmds)


def run_command(cmd):
    """Lancia il comando in una finestra PowerShell nuova, col titolo del comando."""
    shell = shutil.which("pwsh") or shutil.which("powershell")
    cwd = os.path.expandvars(os.path.expanduser(cmd.get("cartella") or str(Path.home())))
    if not shell or not os.path.isdir(cwd):
        return False
    title = "'" + cmd["nome"].replace("'", "''") + "'"
    try:
        subprocess.Popen([shell, "-NoExit", "-Command",
                          f"$Host.UI.RawUI.WindowTitle = {title}; {cmd['comando']}"],
                         cwd=cwd, env=clean_env(), creationflags=0x00000010)
    except OSError:
        return False
    return True


# ---- spesa ----------------------------------------------------------------------------
def add_spending(data, usd, month=None):
    """Somma una chiamata a Claude nel registro data["spend"][AAAA-MM]."""
    month = month or datetime.now().strftime("%Y-%m")
    m = data.setdefault("spend", {}).setdefault(month, {"usd": 0.0, "calls": 0})
    m["usd"] = round(m["usd"] + (usd or 0.0), 6)
    m["calls"] += 1


def spending_label(data, month=None):
    month = month or datetime.now().strftime("%Y-%m")
    m = data.get("spend", {}).get(month, {"usd": 0.0, "calls": 0})
    return f"{m['usd']:.2f} $ · {m['calls']} chiamate"
