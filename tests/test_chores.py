"""Faccende della mascotte su un desktop e un Download FINTI (cartelle temporanee)."""
import ctypes, ctypes.wintypes as wt, os, time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
from hoppy import chores as pc

ok = lambda c: "OK " if c else "NO "
k32 = ctypes.windll.kernel32
k32.CreateFileW.restype = wt.HANDLE

def age(p, days):
    """Porta indietro di N giorni modifica, accesso E creazione del file."""
    t = time.time() - days * 86400
    os.utime(p, (t, t))
    ft = int((t + 11644473600) * 10**7)
    ftv = wt.FILETIME(ft & 0xFFFFFFFF, ft >> 32)
    h = k32.CreateFileW(str(p), 0x100, 7, None, 3, 0x02000000, None)  # FILE_WRITE_ATTRIBUTES
    k32.SetFileTime(h, ctypes.byref(ftv), ctypes.byref(ftv), ctypes.byref(ftv))
    k32.CloseHandle(h)

def mk(folder, name, days, hidden=False):
    p = folder / name
    p.write_text("x" * 10)
    age(p, days)
    if hidden:
        k32.SetFileAttributesW(str(p), 0x2)
    return p

def build():
    tmp = pathlib.Path(tempfile.mkdtemp())
    desk, down = tmp / "Desktop", tmp / "Downloads"
    desk.mkdir(); down.mkdir(); (desk / "Progetto").mkdir(); (desk / "2025-01").mkdir()
    mk(desk, "fattura.pdf", 30); mk(desk, "foto.jpeg", 60); mk(desk, "vecchio.zip", 400)
    mk(desk, "oggi.txt", 1); mk(desk, "App.lnk", 300); mk(desk, "~$bozza.docx", 300)
    mk(desk, "desktop.ini", 300, hidden=True); mk(desk, "nascosto.txt", 300, hidden=True)
    mk(desk / "Progetto", "sorgente.py", 900)                  # cartella non per mese: intoccabile
    mk(desk / "2025-01", "gennaio.xlsx", 400)
    mk(down, "setup.exe", 200); mk(down, "nuovo.pdf", 3); mk(down, "lento.crdownload", 300)
    return tmp, desk, down

# ---- 1. logica pura ------------------------------------------------------------
tmp, desk, down = build()
dp = pc.desktop_plan(desk)
names = sorted(m[0].name for m in dp)
print(ok(names == ["fattura.pdf", "foto.jpeg", "vecchio.zip"]),
      "desktop: solo file sciolti non recenti (no .lnk, ~$, nascosti, cartelle, oggi)", names)
print(ok(all(pc.MONTH_RE.match(m[1].parent.name) and m[1].parent.parent == desk for m in dp)),
      "desktop: destinazione = Desktop\\AAAA-MM")
op = pc.old_plan([desk, down])
print(ok(sorted(m[0].name for m in op) == ["gennaio.xlsx", "setup.exe", "vecchio.zip"]),
      "file vecchi: Desktop + cartelle per mese + Download, non Progetto né recenti",
      sorted(m[0].name for m in op))
print(ok({m[1].parent for m in op} == {desk / "Da rivedere", down / "Da rivedere"}),
      "file vecchi: «Da rivedere» accanto, sullo stesso disco")

(desk / "Da rivedere").mkdir(); (desk / "Da rivedere" / "vecchio.zip").write_text("altro")
op.append((desk / "sparito.txt", desk / "Da rivedere" / "sparito.txt", 0))
done, failed = pc.apply(op)
print(ok(len(done) == 3 and failed == 1 and (desk / "Da rivedere" / "vecchio (2).zip").exists()
         and (desk / "Da rivedere" / "vecchio.zip").read_text() == "altro"),
      "apply: niente sovrascritture (nome (2)), un file mancante conta come fallito")
back, bf = pc.undo(done)
print(ok(back == 3 and bf == 0 and (desk / "vecchio.zip").exists() and (down / "setup.exe").exists()
         and (desk / "2025-01" / "gennaio.xlsx").exists() and not (down / "Da rivedere").exists()
         and (desk / "Da rivedere").exists()),
      "undo: tutto torna al suo posto, sparisce solo la cartella rimasta vuota")
log = pc.ChoreLog(tmp / "log.json")
log.add("old", done); log.add("desktop", [])
print(ok(log.pop()["kind"] == "desktop" and log.pop()["kind"] == "old" and log.pop() is None),
      "registro: annulla l'ultimo giro, poi il precedente")
print(ok(pc.known_folder("desktop").is_dir() and pc.known_folder("downloads").is_dir()),
      "cartelle vere di Desktop e Download trovate (solo lette)")

# ---- 2. la mascotte ------------------------------------------------------------
tmp, desk, down = build()
cp.PET_PORT = 48797
cp.MEM_PATH, cp.PROPOSALS_PATH = tmp / "m.json", tmp / "p.md"
cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "sessions", tmp / "chores.json"
cp.known_folder = lambda name: desk if name == "desktop" else down
cp.ask_claude = lambda *a, **k: ("", "niente Claude nei test")
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
pos = [500, 900]
cp.cursor_pos = lambda: tuple(pos)

root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
pet.next_spontaneous = time.time() + 9999
res = {}

def s1():                                       # mouse appena mosso: la segue, niente faccende
    pet.next_chore = 0
    pet.last_move = time.time()
    root.after(800, s2)

def wait_ask(then, tries=200):                 # aspetta un momento "tranquillo" (niente flessioni)
    if (pet.bubble and "chore" in pet.bubble) or not tries:
        return then()
    root.after(100, lambda: wait_ask(then, tries - 1))

def s2():
    res["following_no_ask"] = pet.bubble is None
    pet.last_move = time.time() - 120           # non segue più il cursore
    pet.next_chore = 0
    wait_ask(s3)

def s3():
    b = pet.bubble
    res["ask1"] = b and b["kind"] == "ask" and b["chore"][0] == "desktop" and b["full"]
    pet.on_thumb(True)                          # sì
    res["after_yes"] = pet.bubble["full"]
    res["moved"] = sorted(p.relative_to(desk).as_posix() for p in desk.rglob("*") if p.is_file())
    pet.bubble = None
    pet.next_chore = 0
    wait_ask(s4)

def s4():
    b = pet.bubble
    res["ask2"] = b and b["chore"][0] == "old" and b["full"]
    pet.on_thumb(False)                         # no
    res["after_no"] = pet.bubble["full"]
    res["snoozed"] = "old" in pet.brain.data.get("chores_snooze", {})
    res["setup_still"] = (down / "setup.exe").exists()
    pet.bubble = None
    pet.next_chore = 0
    root.after(3000, s5)

def s5():
    res["no_reask"] = pet.bubble is None        # detto di no: non ripropone subito
    pet.check_chores(time.time(), manual=True)  # dal menu invece sì
    res["manual"] = pet.bubble and pet.bubble.get("chore", ("",))[0] == "old"
    pet.bubble = None
    pet.undo_chores()
    res["undo"] = pet.bubble["full"]
    res["restored"] = (desk / "fattura.pdf").exists() and not any(
        pc.MONTH_RE.match(p.name) and p.name != "2025-01" for p in desk.iterdir())
    pet.undo_chores()
    res["undo_empty"] = pet.bubble["full"]
    root.destroy()

root.after(500, s1)
root.after(60000, root.destroy)                 # rete di sicurezza: il test non resta appeso
root.report_callback_exception = lambda *a: (__import__("traceback").print_exception(*a),
                                             root.destroy())
root.mainloop()

print(ok(res["following_no_ask"]), "mentre segue il cursore non propone faccende")
print(ok(res["ask1"]), "a riposo propone il riordino:", res["ask1"])
print(ok("Ho spostato 3 file" in res["after_yes"]), "sì →", res["after_yes"])
print("   desktop dopo:", res["moved"])
print(ok(res["ask2"]), "poi propone i file vecchi:", res["ask2"])
print(ok(res["after_no"] == "Va bene, lascio tutto com'è." and res["snoozed"] and res["setup_still"]),
      "no → non tocca niente e se lo segna")
print(ok(res["no_reask"]), "dopo il no non lo ripropone da sola")
print(ok(res["manual"]), "dal menu «Fai le pulizie» lo ripropone")
print(ok(res["restored"]), "Annulla pulizie →", res["undo"])
print(ok(res["undo_empty"] == "Non ho pulizie da annullare."), "secondo annulla:", res["undo_empty"])
