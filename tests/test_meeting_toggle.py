"""Modalità riunione spenta e riaccesa dal menu, con una call in corso."""
import time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
tmp = pathlib.Path(tempfile.mkdtemp())
cp.PET_PORT = 48796
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: ["Teams"]; cp.pet_watch.fullscreen_state = lambda: 1
cp.ask_claude = lambda *a, **k: ("x", None)
cp.STANDUP_HOUR = 99
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
ok = []
def check(name, cond):
    ok.append(cond); print(("OK  " if cond else "ERR ") + name)
def run():
    now = time.time()
    pet.check_meeting(now)
    check("microfono acceso -> riunione", pet.meeting)
    pet.notify_session(now, "done", "X")
    check("avviso rimandato", pet.after_meeting == [("done", "X")])
    pet.toggle_meeting_mode(None)
    check("disattivata -> esce dalla riunione", not pet.meeting)
    check("avviso rimandato consegnato", pet.after_meeting == [])
    check("niente 'Fine call!'", not (pet.bubble and "Fine call" in pet.bubble.get("text", "")))
    pet.check_meeting(time.time())
    check("resta fuori col microfono acceso", not pet.meeting)
    check("salvato su disco", cp.pet_config.load()["meeting"] is False)
    pet.toggle_meeting_mode(None)
    check("riattivata -> di nuovo in riunione", pet.meeting)
    print("TUTTO OK" if all(ok) else "FALLITO")
    root.destroy()
root.after(1000, run)
root.mainloop()
