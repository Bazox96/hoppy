"""Il cibo si disegna davanti alla mascotte (prima finiva dietro il corpo e spariva)."""
import time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
tmp = pathlib.Path(tempfile.mkdtemp())
cp.PET_PORT = 48795
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: []
cp.ask_claude = lambda *a, **k: ("x", None)
cp.STANDUP_HOUR = 99
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
ok = []
def check(name, cond):
    ok.append(cond); print(("OK  " if cond else "ERR ") + name)
def run():
    for kind in ("cookie", "apple"):
        pet.food = {"kind": kind, "mon": pet.mon, "x": pet.x, "y": pet.y, "vy": 0.0,
                    "state": "rest", "t0": time.time(), "bites": 0, "dx": 0, "dy": 0}
        pet.draw(time.time())
        items = pet.mon.c.find_all()           # dal basso verso l'alto
        food = [i for i in items if "food" in pet.mon.c.gettags(i)]
        body = [i for i in items if "pet" in pet.mon.c.gettags(i)]
        check(f"{kind}: disegnato", bool(food) and bool(body))
        check(f"{kind}: sopra il corpo della mascotte", bool(food) and bool(body)
              and items.index(food[0]) > items.index(body[-1]))
    print("TUTTO OK" if all(ok) else "FALLITO")
    root.destroy()
root.after(1000, run)
root.after(20000, root.destroy)
root.mainloop()
