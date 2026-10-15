"""Col menu aperto la mascotte non segue il cursore."""
import time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
tmp = pathlib.Path(tempfile.mkdtemp())
cp.PET_PORT = 48793
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.pet_watch.mic_users = lambda: []; cp.pet_watch.fullscreen_state = lambda: 1
cp.ask_claude = lambda *a, **k: ("x", None)
cp.STANDUP_HOUR = 99
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
pet.next_spontaneous = pet.next_chore = pet.next_dev_scan = time.time() + 99999
pet.brain.data["greet_day"] = time.strftime("%Y-%m-%d")
wa = pet.mons[0].wa
pos = [wa.left + 300, wa.bottom - 5]
cp.cursor_pos = lambda: tuple(pos)
res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("OK  " if cond else "NO  ") + name, extra)
def step0():                                   # appoggiata sulla barra, sotto il cursore
    pet.x, pet.y = wa.left + 300, wa.bottom
    pet.set_stand(pet.plat_at(pet.x, pet.y))
    pet.set_state("idle", time.time())
    root.after(800, step1)
def step1():
    check("parte appoggiata", pet.state in ("idle", "walk"), pet.state)
    pet.on_menu(None)                          # tasto destro: menu aperto
    root.after(100, step2)
def step2():
    s = (round(pet.x), pet.state)
    pos[0] = wa.left + 900                     # sposti il mouse verso le voci (e oltre)
    root.after(2500, lambda: step3(s))
def step3(s):
    check("menu aperto: resta ferma", abs(pet.x - s[0]) <= 1, f"x {s[0]} -> {round(pet.x)}, stato {pet.state}")
    pet.menu_until = 0.0                       # menu chiuso
    root.after(4000, step4)
def step4():
    check("menu chiuso: torna a seguire il cursore", pet.x > wa.left + 700, f"x={round(pet.x)}")
    print("TUTTO OK" if all(res) else "FALLITO")
    root.destroy()
root.after(1000, step0)
root.mainloop()
