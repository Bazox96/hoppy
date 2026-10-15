"""Nascondino con il nascondiglio vicino al bordo: prima apriva portali all'infinito."""
import time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
tmp = pathlib.Path(tempfile.mkdtemp())
cp.PET_PORT = 48794
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: [(4242, 300, 500, 1100, 900)]
cp.cursor_pos = lambda: (1500, 300)
cp.ask_claude = lambda *a, **k: ("x", None)
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
pet.next_spontaneous = pet.next_chore = pet.next_dev_scan = time.time() + 99999
pet.brain.data["greet_day"] = pet.brain.data["standup_day"] = time.strftime("%Y-%m-%d")
portals = []
_sp = pet.start_portal
pet.start_portal = lambda *a, **k: (portals.append(1), _sp(*a, **k))[1]
res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("OK  " if cond else "NO  ") + name, extra)

def go_hide(edge):
    pet.hide = None
    pet.start_hide()
    H = pet.hide
    T = [p for p in pet.mon.plats if p[0] == 4242][0] if any(p[0] == 4242 for p in pet.mon.plats) else H["T"]
    H.update(mon=pet.mons[0], T=T, x=(T[2] + cp.MARGIN + 3) if edge == "left" else (T[3] - cp.MARGIN - 3))
    portals.clear()

def run(step=0, edge="left"):
    if step == 0:
        pet.last_move = time.time() - 999
        go_hide(edge)
    if pet.state == "hide" or step > 400:
        check(f"nascondiglio vicino al bordo {edge}: si nasconde", pet.state == "hide",
              f"(portali: {len(portals)}, passi: {step})")
        check(f"...con al massimo un portale ({edge})", len(portals) <= 1)
        if edge == "left":
            pet.hide = None; pet.set_state("idle", time.time())
            pet.x = pet.mons[0].wa.left + 100; pet.y = pet.mons[0].wa.bottom
            return root.after(500, lambda: run(0, "right"))
        print("TUTTO OK" if all(res) else "FALLITO")
        return root.destroy()
    root.after(50, lambda: run(step + 1, edge))
root.after(1500, run)
root.mainloop()
