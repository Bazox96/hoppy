"""Skill dei profili di Claude Code aperte dalla chat: lettura di SKILL.md, scelta del profilo,
comando PowerShell (provato davvero con un claude-gen finto, senza aprire finestre)."""
import os, pathlib, shutil, subprocess, tempfile, time, tkinter as tk
import _setup  # noqa: F401
from hoppy import pet as cp
from hoppy import knowledge as kn

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

tmp = pathlib.Path(tempfile.mkdtemp())
def skill(home, folder, text):
    d = home / "skills" / folder
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(text, encoding="utf-8")

personal, work = tmp / "personal", tmp / "work"
skill(personal, "deploy", "---\nname: deploy\ndescription: Pubblica il sito demo.\n---\n# x")
skill(work, "jira", "---\nname: jira\ndescription: Recupera una card Jira e mostra il contenuto.\n---\n")
skill(work, "release", "---\nname: release\ndescription: >\n  Prepara la release\n  del servizio.\n---\n")
skill(work, "rotta", "niente frontmatter")
skill(work, "strana", "---\nname: rm -rf /\ndescription: no\n---\n")

found = kn.read_skills(work)
check("legge nome e descrizione", found.get("jira") == "Recupera una card Jira e mostra il contenuto.")
check("descrizione su più righe (>)", found.get("release") == "Prepara la release del servizio.")
check("senza frontmatter: nome della cartella", "rotta" in found)
check("nome strano scartato", not any(" " in n for n in found))

kn.CLAUDE_PROJECTS = personal / "projects"
kn.WORK_ENABLED, kn.WORK_HOME, kn.WORK_LABEL, kn.WORK_LAUNCHER = True, work, "lavoro", "claude-gen"

# ---- il comando PowerShell, provato davvero con un claude-gen finto -----------------------
captured = []
real_popen = subprocess.Popen
real_which = shutil.which
fake_exe = tmp / "claude.exe"; fake_exe.write_text("")
kn.subprocess.Popen = lambda args, **k: captured.append((args, k)) or object()
kn.shutil.which = lambda name: str(fake_exe) if name == "claude" else real_which(name)
check("launch_claude parte", kn.launch_claude(str(tmp), "demo", work=True, prompt="/jira DEMO-1 l'utente"))
shell, command = captured[-1][0][0], captured[-1][0][-1]
subprocess.Popen = real_popen                 # da qui PowerShell vero (senza finestra)
out = subprocess.run([shell, "-NoProfile", "-Command",
                      "function claude-gen { $args | ForEach-Object { 'ARG=' + $_ } }; "
                      + command.split("; ", 1)[1]],
                     capture_output=True, text=True, timeout=60, creationflags=0x08000000)
check("claude-gen riceve il prompt intero, apostrofo compreso",
      "ARG=/jira DEMO-1 l'utente" in out.stdout.splitlines())
kn.subprocess.Popen = lambda args, **k: captured.append((args, k)) or object()
kn.launch_claude(str(tmp), "demo", work=False, prompt="/deploy")
check("profilo personale: claude con il prompt", captured[-1][0][-1].endswith(f"& '{fake_exe}' '/deploy'"))
kn.launch_claude(str(tmp), "demo", work=False)
check("senza prompt: come prima", captured[-1][0][-1].endswith(f"& '{fake_exe}'"))

subprocess.Popen = real_popen

# ---- dalla chat -------------------------------------------------------------------------
cp.PET_PORT = 48793
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: []
cp.STANDUP_HOUR = 99
cp.FEAT_UPDATES = False
prompts, launched = [], []
reply = {"text": ""}
cp.ask_claude = lambda prompt, system, timeout=90: (prompts.append(prompt), (reply["text"], None))[1]
cp.launch_claude = lambda path, title, work=False, prompt="": launched.append((path, title, work, prompt)) or True
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
pet.next_spontaneous = time.time() + 9999
pet.know.projects = {"MyApp": str(tmp)}
pet.know.is_work = lambda path: False

def say(text, answer):
    reply["text"] = answer
    pet.thinking = None
    pet.send_talk(text)
    for _ in range(100):
        while not pet.think_q.empty():
            pet.on_thought(time.time(), *pet.think_q.get_nowait())
        if not pet.thinking:
            break
        root.update(); time.sleep(0.03)

def run():
    say("ciao come stai", "Bene!")
    check("chiacchiera normale: niente elenco delle skill (costa)", "SKILL DI CLAUDE" not in prompts[-1])
    say("apri jira DEMO-123", "Apro Jira!\n#SKILL: jira DEMO-123")
    check("con 'apri': l'elenco delle skill va nel prompt", "jira (lavoro)" in prompts[-1])
    check("skill di lavoro senza progetto: claude-gen nella home",
          launched[-1] == (str(pathlib.Path.home()), "/jira", True, "/jira DEMO-123"))
    say("/release", "Via!\n#SKILL: release")
    check("scritta /release: parte anche senza 'apri'", launched[-1][3] == "/release" and launched[-1][2])
    say("lancia deploy su MyApp", "Ok\n#AVVIA: MyApp\n#SKILL: deploy")
    check("skill personale nel progetto personale",
          launched[-1] == (str(tmp), "MyApp", False, "/deploy"))
    say("apri jira su MyApp", "Ok\n#AVVIA: MyApp\n#SKILL: jira")
    check("skill solo di lavoro in progetto personale: profilo di lavoro", launched[-1][2] is True)
    n = len(launched)
    say("apri boh", "Ok\n#SKILL: inesistente")
    check("skill che non c'è: lo dice e non apre", len(launched) == n and "Non trovo la skill" in pet.bubble["full"])
    say("cosa fa jira?", "Recupera i ticket.\n#SKILL: jira")
    check("senza richiesta esplicita non apre nulla", len(launched) == n)
    print("TUTTO OK" if all(ok) else "FALLITO")
    root.destroy()

root.after(1000, run)
root.after(60000, root.destroy)
root.mainloop()
