"""Funzioni della mascotte in un ambiente FINTO: cartelle temporanee, Claude finto,
microfono/PC simulati, appunti simulati (gli appunti veri non vengono toccati)."""
import json, os, subprocess, time, tkinter as tk, pathlib, tempfile
from datetime import datetime, timedelta
import _setup  # noqa: F401
from hoppy import pet as cp
from hoppy import chores as pc, watch as pw, work as pk

ok = lambda c: "OK " if c else "NO "
tmp = pathlib.Path(tempfile.mkdtemp())

# ======================= 1. moduli, senza mascotte =======================
print("--- appunti: segreti ed errori")
for t, want in (("password: hunter2", True), ("Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkw.x", True),
                ("Xk9#mQ2!pL7z", True), ("https://example.com/a/b?c=1", False),
                ("ciao come stai", False), ("AKIAABCDEFGHIJKLMNOP", True)):
    print(ok(pw.looks_secret(t) == want), f"segreto? {t[:30]!r} -> {pw.looks_secret(t)}")
err = 'Traceback (most recent call last):\n  File "a.py", line 3\nKeyError: \'x\''
java = "java.lang.NullPointerException: boom\n\tat com.x.Foo.bar(Foo.java:42)"
print(ok(pw.looks_like_error(err) and pw.looks_like_error(java) and not pw.looks_like_error("una frase normale lunga abbastanza da contare")),
      "riconosce Traceback Python e stack Java, non le frasi normali")

class FakeU32:                                  # sequenza degli appunti simulata
    seq = 1
    def GetClipboardSequenceNumber(self):
        return self.seq
real_u32, real_read = pw.user32, pw.read_clipboard_text
pw.user32 = fu = FakeU32()
clip_text = [(True, "primo")]
pw.read_clipboard_text = lambda: clip_text[0]
cl = pw.Clipboard()
fu.seq = 2; a = cl.poll()
fu.seq = 3; clip_text[0] = (True, "password=segreta123"); b = cl.poll()
fu.seq = 4; clip_text[0] = (False, None); c = cl.poll(); seq_after_busy = cl.seq
clip_text[0] = (True, "secondo"); d = cl.poll()
print(ok(a == "primo" and b is None and c is None and seq_after_busy == 3 and d == "secondo"
         and cl.items == ["secondo", "primo"]),
      "cronologia: tiene i testi, salta le password, riprova se gli appunti sono occupati", cl.items)
pw.user32, pw.read_clipboard_text = real_u32, real_read

print("--- sessioni di Claude Code")
root = tmp / "projects"; (root / "proj-a").mkdir(parents=True)
sess = root / "proj-a" / "s.jsonl"
def write(*recs):
    with sess.open("a", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
write({"type": "user", "cwd": r"D:\Code\MyApp", "message": {"content": "fai x"}})
w = pw.ClaudeWatch([root]); e0 = w.poll()
time.sleep(0.05)
write({"type": "assistant", "cwd": r"D:\Code\MyApp", "message": {"stop_reason": "end_turn"}})
os.utime(sess, (time.time() + 1, time.time() + 1)); e1 = w.poll()
write({"type": "user", "message": {"content": "altro"}}, {"type": "assistant", "message": {"stop_reason": "tool_use"}})
os.utime(sess, (time.time() + 2, time.time() + 2)); e2 = w.poll()
e3 = w.poll(now=time.time() + 2 + pw.WAIT_S + 1); e4 = w.poll(now=time.time() + 2 + pw.WAIT_S + 5)
print(ok(e0 == [] and e1 == [("done", r"D:\Code\MyApp")] and e2 == []
         and e3 == [("waiting", r"D:\Code\MyApp")] and e4 == []),
      "finito -> 'done'; tool fermo da 25 s -> 'waiting' una volta sola", e1, e3)

print("--- RAM e riunioni (valori veri, sola lettura)")
s = pw.system_status()
print(ok(0 < s["commit_pct"] < 100 and s["uptime_h"] > 0), "stato PC:", {k: round(v, 1) for k, v in s.items()})
print(ok(isinstance(pw.mic_users(), list) and pw.fullscreen_state() in range(0, 8)),
      "microfono:", pw.mic_users(), "schermo intero:", pw.fullscreen_state())

print("--- pulizie da sviluppatore")
def old(p, days):
    t = time.time() - days * 86400
    for r, ds, fs in os.walk(p):
        for f in fs:
            os.utime(os.path.join(r, f), (t, t))
fermo, vivo = tmp / "fermo", tmp / "vivo"
for proj in (fermo, vivo):
    (proj / "node_modules" / "lib").mkdir(parents=True)
    (proj / "package.json").write_text("{}"); (proj / "node_modules" / "lib" / "x.js").write_text("x" * 5000)
    (proj / "target").mkdir(); (proj / "target" / "a.class").write_text("y" * 100)   # senza pom.xml: intoccabile
old(fermo, 90); old(vivo / "node_modules", 90)          # "vivo" ha package.json di oggi
dp = pc.dev_plan([fermo, vivo])
print(ok([d[0] for d in dp] == [fermo / "node_modules"] and dp[0][2] == 5000),
      "solo node_modules del progetto fermo (non 'target' senza pom.xml, non il progetto vivo)", dp)
m2 = tmp / "m2"; (m2 / "g" / "a" / "1.0").mkdir(parents=True); (m2 / "g" / "a" / "2.0").mkdir()
for v, days in (("1.0", 400), ("2.0", 5)):
    (m2 / "g" / "a" / v / "a.pom").write_text("p"); (m2 / "g" / "a" / v / "a.jar").write_text("j" * 10)
    old(m2 / "g" / "a" / v, days)
mp = pc.m2_plan(m2)
print(ok([d[0].name for d in mp] == ["1.0"]), "cache Maven: solo la versione non usata da 6 mesi")
freed, failed = pc.delete_dirs(dp + mp)
print(ok(freed == 5011 and failed == 0 and not (fermo / "node_modules").exists()
         and (fermo / "package.json").exists() and (m2 / "g" / "a" / "2.0").exists()),
      "eliminate solo quelle cartelle:", freed, "byte")

print("--- standup e git")
since = pk.prev_workday(datetime(2026, 10, 19, 9))      # lunedì -> da venerdì
print(ok(since == datetime(2026, 10, 16)), "lunedì: guarda da venerdì", since)
sroot = tmp / "sess"; (sroot / "p").mkdir(parents=True)
y = datetime.now() - timedelta(days=1)
with (sroot / "p" / "x.jsonl").open("w", encoding="utf-8") as fh:
    for txt, ts in (("sistema il login", y), ("This session is being continued...", y),
                    ("<command-name>/clear</command-name>", y), ("di oggi", datetime.now())):
        fh.write(json.dumps({"type": "user", "cwd": r"D:\Code\Atlas\initial_load",
                             "timestamp": ts.astimezone().isoformat(), "message": {"content": txt}}) + "\n")
d0 = datetime.combine(y.date(), datetime.min.time())
sp = pk.session_prompts([sroot], d0, d0 + timedelta(days=1), name_of=lambda c: "Atlas")
print(ok(sp == {"Atlas": ["sistema il login"]}), "richieste di ieri, senza riassunti automatici né comandi", sp)
repo = tmp / "repo"; repo.mkdir()
g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, creationflags=0x08000000)
g("init", "-q"); g("config", "user.email", "io@test"); g("config", "user.name", "Io")
(repo / "a.txt").write_text("1"); g("add", "a.txt"); g("commit", "-qm", "primo commit")
(repo / "a.txt").write_text("2"); t5 = time.time() - 5 * 86400; os.utime(repo / "a.txt", (t5, t5))
rs = pk.git_scan([repo], datetime.now() - timedelta(hours=1), datetime.now() + timedelta(hours=1))
pl = pk.pending_lines(rs)
print(ok(rs[0]["dirty"] == 1 and rs[0]["commits"] == ["primo commit"]
         and pl == ["repo: 1 file modificati e non committati da 5 giorni"]), "git:", pl, rs[0]["commits"])

print("--- comandi e spesa")
cp.COMMANDS_PATH.parent.mkdir(parents=True, exist_ok=True)
cp.COMMANDS_PATH.write_text(json.dumps([
    {"nome": "deploy demo", "descrizione": "pubblica la demo", "comando": "echo deploy", "cartella": "~"},
    {"nome": "Docker Desktop", "descrizione": "avvia Docker", "comando": "echo docker", "cartella": "~"}]),
    encoding="utf-8")
cmds = pk.Commands(cp.COMMANDS_PATH)
print(ok(cmds.find("deploy demo")["nome"] == "deploy demo" and cmds.find("docker")["nome"] == "Docker Desktop"
         and cmds.find("zorglub") is None), "comandi:", [c["nome"] for c in cmds.load()])
data = {}
pk.add_spending(data, 0.0123); pk.add_spending(data, 0.002)
print(ok(pk.spending_label(data) == "0.01 $ · 2 chiamate"), "spesa:", pk.spending_label(data))

# ======================= 2. la mascotte =======================
cp.PET_PORT = 48796
cp.MEM_PATH, cp.PROPOSALS_PATH = tmp / "m.json", tmp / "p.md"
cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "sessions", tmp / "chores.json"
cp.known_folder = lambda name: tmp / ("D" if name == "desktop" else "DL")
(tmp / "D").mkdir(); (tmp / "DL").mkdir()
cp.active_app = lambda pid: ""
WIN = [(4242, 300, 500, 1100, 900)]                    # una finestra finta per il nascondino
cp.window_rects = lambda pid: list(WIN)
pos = [700, 1000]
cp.cursor_pos = lambda: tuple(pos)
mic = []
cp.pet_watch.mic_users = lambda: list(mic)
cp.pet_watch.fullscreen_state = lambda: 1
sysv = {"uptime_h": 3.0, "commit_pct": 40.0, "commit_gb": 25.0, "limit_gb": 63.0, "nonpaged_gb": 1.0}
cp.pet_watch.system_status = lambda: dict(sysv)
ran = []
cp.pet_work.run_command = lambda c: ran.append(c["nome"]) or True
cp.pet_work.session_prompts = lambda *a, **k: {"MyApp": ["sistema il login"]}
cp.pet_work.git_scan = lambda *a, **k: [{"name": "MyApp", "path": "x", "branch": "main", "ahead": 2,
                                          "dirty": 0, "dirty_age_d": 0, "commits": ["fix login"]}]
replies, asked = [], []
def fake_claude(prompt, system, timeout=90):
    asked.append((system[:40], prompt))
    if system.startswith("Scrivi il diario"):
        return "Diario.", None
    if "standup" in system:
        return "**Ieri**\n- Ho sistemato il login", None
    if "errore" in system:
        return "**Causa** manca la chiave.", None
    return replies.pop(0), None
cp.ask_claude = fake_claude
cp.STANDUP_HOUR = 99                                   # niente standup automatico durante il test

root_tk = tk.Tk(); root_tk.withdraw()
pet = cp.Pet(root_tk)
pet.next_spontaneous = pet.next_chore = pet.next_dev_scan = time.time() + 99999
pet.brain.data["greet_day"] = pet.brain.data["standup_day"] = datetime.now().date().isoformat()
pet.claude_watch = pw.ClaudeWatch([tmp / "watch"])
fake_clip = []
pet.clip.poll = lambda: fake_clip.pop(0) if fake_clip else None
res = {}
steps = []
def step(f, delay=600):
    steps.append((f, delay))
def run_steps(i=0):
    if i >= len(steps):
        return root_tk.destroy()
    f, delay = steps[i]
    f()
    root_tk.after(delay, lambda: run_steps(i + 1))
class FakeEntry:
    def delete(self, *_): pass
def chat(text, reply):
    replies.append(reply)
    pet.talk_win, pet.talk_ent = object(), FakeEntry()
    pet.send_talk(text)

# promemoria, timer, comandi
step(lambda: chat("ricordami domani alle 9 la call", "Te lo ricordo!\n#PROMEMORIA: 2030-01-02 09:00 | call con Mario"), 1200)
step(lambda: res.update(rem=list(pet.brain.data.get("reminders", [])), rem_bubble=pet.bubble["full"],
                        prompt_has_hint="#PROMEMORIA:" in asked[-1][1] and "COMANDI RAPIDI" in asked[-1][1]))
step(lambda: chat("pomodoro di un attimo", "Via col pomodoro!\n#TIMER: 0.02 | pomodoro"), 1200)
step(lambda: (setattr(pet, "talk_win", None)), 2500)
step(lambda: res.update(timer=pet.bubble and pet.bubble["kind"] == "remind" and pet.bubble["full"]))
step(lambda: (setattr(pet, "bubble", None), chat("fai il deploy della demo", "Subito!\n#COMANDO: deploy demo")), 1200)
step(lambda: (res.update(cmd_ask=pet.bubble and pet.bubble["kind"] == "ask" and pet.bubble["full"]),
              pet.on_thumb(True), res.update(ran=list(ran), cmd_done=pet.bubble["full"]),
              setattr(pet, "talk_win", None)))
step(lambda: chat("lancia zorglub", "Ok!\n#COMANDO: zorglub"), 1200)
step(lambda: (res.update(cmd_unknown=pet.bubble["full"]), setattr(pet, "talk_win", None), setattr(pet, "bubble", None)))

# riunione: zitta, avvisi rimandati, reazione a fine call
step(lambda: mic.append("Teams"), 2600)
step(lambda: (res.update(meeting=pet.meeting), pet.notify_session(time.time(), "done", "MyApp"),
              res.update(meet_silent=pet.bubble is None)))
step(lambda: (setattr(pet, "meeting_since", pet.meeting_since - 400), mic.clear()), 2600)
step(lambda: (res.update(after_meet=pet.bubble and pet.bubble["full"], meeting_off=not pet.meeting),
              setattr(pet, "bubble", None), setattr(pet, "meeting_since", time.time() - 400),
              setattr(pet, "meeting_call", True)))
step(lambda: (mic.append("Teams")), 2600)
step(lambda: (setattr(pet, "meeting_since", pet.meeting_since - 400), mic.clear()), 2600)
step(lambda: (res.update(call_end=pet.bubble and pet.bubble["full"]), setattr(pet, "bubble", None)))

# RAM
step(lambda: (sysv.update(commit_pct=88.0, uptime_h=19.2), setattr(pet, "next_sys", 0)), 900)
step(lambda: (res.update(ram=pet.bubble and pet.bubble["full"]), setattr(pet, "bubble", None),
              setattr(pet, "next_sys", 0)), 900)
step(lambda: res.update(ram_once=pet.bubble is None))

# sessione di Claude che finisce
def sess_done():
    d = tmp / "watch" / "p"; d.mkdir(parents=True, exist_ok=True)
    f = d / "s.jsonl"
    f.write_text(json.dumps({"type": "user", "cwd": r"D:\Code\MyApp", "message": {"content": "x"}}) + "\n")
    pet.claude_watch.poll()
    with f.open("a") as fh:
        fh.write(json.dumps({"type": "assistant", "message": {"stop_reason": "end_turn"}}) + "\n")
    os.utime(f, (time.time() + 1, time.time() + 1))
step(sess_done, 3500)
step(lambda: (res.update(sess=pet.bubble and pet.bubble["full"]), setattr(pet, "bubble", None)))

# errore copiato -> lavagna
step(lambda: fake_clip.append(err), 3500)
step(lambda: (res.update(err_ask=pet.bubble and pet.bubble["full"]), pet.on_thumb(True)), 2500)
step(lambda: res.update(err_board=pet.lecture is not None and pet.lecture.pending is not None
                        and "manca la chiave" in (pet.lecture.pending or ("",))[0]
                        or (pet.lecture is not None and "manca la chiave" in pet.lecture.plain)))
step(lambda: pet.lecture and pet.lecture.close(), 1500)

# standup
step(lambda: pet.start_standup(), 2500)
step(lambda: res.update(standup=(pet.lecture.pending or (pet.lecture.plain,))[0] if pet.lecture else None))
step(lambda: pet.lecture and pet.lecture.close(), 1500)

# spesa
step(lambda: cp.COSTS.put(0.0421), 400)
step(lambda: res.update(spend=cp.pet_work.spending_label(pet.brain.data)))

# pulizie da sviluppatore (finte)
def dev():
    junk = tmp / "junkproj" / "node_modules"; junk.mkdir(parents=True); (junk / "f").write_text("z" * 2000)
    pet.dev_found = {"dev": [(junk, None, 2000)], "m2": []}
    pet.check_chores(time.time(), manual=True)
    res["dev_ask"] = pet.bubble and pet.bubble.get("chore", ("",))[0] == "dev" and pet.bubble["full"]
    pet.on_thumb(True)
step(dev, 1500)
step(lambda: (res.update(dev_done=pet.bubble and pet.bubble["full"],
                         dev_gone=not (tmp / "junkproj" / "node_modules").exists()),
              setattr(pet, "bubble", None)))

# appunti recenti
def clipwin():
    pet.clip.items = ["uno", "due"]
    pet.open_clipboard()
    res["clipwin"] = pet.clip_win is not None
    pet.clip_win.destroy(); pet.clip_win = None
step(clipwin)

# palla
def ball_throw():
    pet.mon = pet.monitor_at(*pos)
    pet.toggle_ball()
    b = pet.ball
    b.update(state="fly", vx=6.0, vy=-5.0)
step(ball_throw, 12000)
step(lambda: res.update(kicks=pet.ball and pet.ball.get("kicks", 0)))
step(lambda: (setattr(pet, "ball", None)))

# nascondino
step(lambda: pet.start_hide(), 9000)
step(lambda: (res.update(hiding=pet.state == "hide", hide_dbg=(pet.state, pet.hide and round(pet.hide["x"]),
                                                             round(pet.x), round(pet.y), pet.bubble and pet.bubble["full"])),
              pet.on_press(None)), 300)
step(lambda: res.update(found=pet.bubble and pet.bubble["full"], hide_off=pet.hide is None))

root_tk.after(800, run_steps)
root_tk.after(150000, root_tk.destroy)
root_tk.report_callback_exception = lambda *a: (__import__("traceback").print_exception(*a), root_tk.destroy())
root_tk.mainloop()

print("--- mascotte")
r = res
print(ok(r.get("rem") and r["rem"][0]["text"] == "call con Mario"
         and datetime.fromtimestamp(r["rem"][0]["at"]) == datetime(2030, 1, 2, 9)), "promemoria salvato:", r.get("rem"))
print(ok(r.get("prompt_has_hint")), "la chat sa dei promemoria e dei comandi rapidi")
print(ok(r.get("timer") and "pomodoro: tempo scaduto!" in r["timer"]), "timer scaduto ->", r.get("timer"))
print(ok(r.get("cmd_ask") and "Lancio «deploy demo»?" in r["cmd_ask"] and r.get("ran") == ["deploy demo"]),
      "comando: chiede conferma e poi lo lancia ->", r.get("cmd_done"))
print(ok(r.get("cmd_unknown") and "Non conosco il comando «zorglub»" in r["cmd_unknown"]), "comando sconosciuto")
print(ok(r.get("meeting") and r.get("meet_silent")), "in call: modalità riunione, avviso rimandato")
print(ok(r.get("meeting_off") and r.get("after_meet") == "«MyApp» ha finito!"), "fine call: arriva l'avviso rimandato ->", r.get("after_meet"))
print(ok(r.get("call_end") and r["call_end"].startswith("Fine call!")), "reazione a fine call ->", r.get("call_end"))
print(ok(r.get("ram") and "acceso da 19 ore" in r["ram"] and "88%" in r["ram"] and r.get("ram_once")),
      "RAM ->", r.get("ram"))
print(ok(r.get("sess") == "«MyApp» ha finito!"), "sessione di Claude finita ->", r.get("sess"))
print(ok(r.get("err_ask") and r.get("err_board")), "errore copiato -> chiede e spiega sulla lavagna")
print(ok(r.get("standup") and "Ho sistemato il login" in r["standup"] and "2 commit su main non ancora pushati" in r["standup"]),
      "standup ->", (r.get("standup") or "").replace("\n", " / "))
print(ok(r.get("spend", "").startswith("0.04 $")), "spesa ->", r.get("spend"))
print(ok(r.get("dev_ask") and r.get("dev_gone") and "Ho liberato" in (r.get("dev_done") or "")),
      "build vecchie ->", r.get("dev_ask"), "|", r.get("dev_done"))
print(ok(r.get("clipwin")), "finestra appunti recenti")
print("OK " if (r.get("kicks") or 0) >= 1 else "~~ ",                # dipende dai tempi: solo informativo
      "palla: la rincorre e la calcia, calci =", r.get("kicks"))
print(ok(r.get("hiding") and r.get("found", "").startswith("Mi hai trovata") and r.get("hide_off")),
      "nascondino ->", r.get("found"), r.get("hide_dbg"))
