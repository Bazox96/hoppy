"""Mascotte (finestre nascoste): le novità finiscono sulla lavagna; «cosa succede?» in chat
fotografa l'ultima finestra usata e chiede a Claude (finto) con l'immagine."""
import ctypes, time, tkinter as tk, pathlib, tempfile
import _setup  # noqa: F401
from hoppy import pet as cp
tmp = pathlib.Path(tempfile.mkdtemp())
cp.PET_PORT = 48796
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: []
asked = []
cp.ask_claude = lambda *a, **k: (asked.append(k.get("image")), ("**Cosa vedo** un errore.", None))[1]
cp.STANDUP_HOUR = 99
cp.MUSIC = False
ctypes.windll.shcore.SetProcessDpiAwareness(2)
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

target = tk.Toplevel(root)
target.geometry("400x200-4000-4000")          # la "finestra di lavoro", fuori dallo schermo
tk.Label(target, text="Errore 404", bg="white").pack(expand=True, fill="both")

def news():
    pet.show_news(cp.pet_changelog.CHANGES[:1])
    board = pet.lecture
    check("novità: lavagna aperta", board is not None)
    check("novità: testo pronto per la lavagna",
          board.pending and board.pending[0].startswith("**Versione ") and not board.pending[1])
    pet.end_lecture(board)
    pet.app_hwnd = None
    pet.explain_screen()
    check("nessuna finestra: lo dice nel fumetto", pet.bubble and "finestra" in pet.bubble["full"]
          and not asked)
    target.update()
    pet.app_hwnd = ctypes.windll.user32.GetParent(target.winfo_id())
    pet.send_talk("cosa succede qui?")
    root.after(1500, screen)

def screen():
    check("chat: ha chiesto a Claude con la foto", asked and asked[0].startswith(b"\x89PNG"))
    check("chat: risposta sulla lavagna", pet.lecture is not None)
    print("TUTTO OK" if all(ok) else "FALLITO")
    root.destroy()

root.after(1000, news)
root.after(20000, root.destroy)
root.mainloop()
