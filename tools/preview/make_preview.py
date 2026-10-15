"""GIF di anteprima per il README: Hoppy su un desktop finto (fuori dallo schermo vero),
fumetto, menu, «Spiegami lo schermo» alla lavagna. Non chiama Claude (risposta finta).
Uso, dalla cartella del repo:
    python tools/preview/make_preview.py it docs/preview-it.gif
    python tools/preview/make_preview.py en docs/preview-en.gif"""
import ctypes, ctypes.wintypes as wt, os, pathlib, sys, tempfile, time

LANG, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
os.environ["HOPPY_LANG"] = LANG
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).parent))
ctypes.windll.shcore.SetProcessDpiAwareness(2)
import tkinter as tk
from hoppy import config
TMP = pathlib.Path(tempfile.mkdtemp())
config.DATA_DIR, config.CONFIG_PATH, config.STARTUP_DIR = TMP, TMP / "config.json", TMP / "startup"
from hoppy import pet as cp, screen
import gifenc

W, H, BAR = 880, 560, 40                      # area di lavoro + barra delle applicazioni
L, TOP = -7000, -7000                         # fuori da qualunque schermo vero
EN = LANG == "en"
TXT = {
    "hi": "Hi! Need a hand?" if EN else "Ciao! Ti serve una mano?",
    "answer": ("**What I see**\nThe app stopped with a KeyError: the user dictionary has no "
               "'user_id' key.\n\n**What to do**\n- Check that login saves 'user_id'\n"
               "- Use user.get('user_id') with a fallback")
    if EN else
    ("**Cosa vedo**\nIl programma si è fermato con un KeyError: nel dizionario user manca "
     "la chiave 'user_id'.\n\n**Cosa fare**\n- Controlla che il login salvi 'user_id'\n"
     "- Usa user.get('user_id') con un valore di riserva"),
    "q": "What's going on?" if EN else "Cosa succede?",
}

cp.PET_PORT = 48797
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = TMP / "m", TMP / "p", TMP / "s", TMP / "c"
cp.known_folder = lambda n: TMP
cp.monitor_rects = lambda: [((L, TOP, L + W, TOP + H + BAR), (L, TOP, L + W, TOP + H))]
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (L + W - 5, TOP + 5)
cp.pet_watch.mic_users = lambda: []
cp.pet_watch.fullscreen_state = lambda: 1
cp.STANDUP_HOUR = 99
cp.LECTURE, cp.MUSIC, cp.CHARACTER = "professor", False, "octopus"
cp.pet_screen.capture = lambda h: b"png"
cp.ask_claude = lambda *a, **k: (time.sleep(1.2), (TXT["answer"], None))[1]

root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
pet.follow = False
mon = pet.mons[0]
c = mon.c


def backdrop():
    """Desktop finto: sfondo, un editor con un errore (tag board: draw() non lo cancella)."""
    tag = ("board", "backdrop")
    for i in range(0, H, 8):                  # sfondo sfumato
        k = i / H
        col = "#%02x%02x%02x" % (int(40 + 30 * k), int(56 + 40 * k), int(92 + 50 * k))
        c.create_rectangle(0, i, W, i + 8, fill=col, width=0, tags=tag)
    x0, y0, x1, y1 = 40, 40, 470, 330
    c.create_rectangle(x0, y0, x1, y1, fill="#1E1E1E", outline="#3C3C3C", tags=tag)
    c.create_rectangle(x0, y0, x1, y0 + 26, fill="#323233", width=0, tags=tag)
    c.create_text(x0 + 12, y0 + 13, text="app.py", anchor="w", fill="#CCCCCC",
                  font=("Segoe UI", 9), tags=tag)
    code = [("def profile(user):", "#C586C0"), ("    uid = user['user_id']", "#9CDCFE"),
            ("    return load(uid)", "#9CDCFE"), ("", ""), ("profile(session.user)", "#DCDCAA")]
    for i, (line, col) in enumerate(code):
        c.create_text(x0 + 14, y0 + 44 + i * 18, text=line, anchor="w", fill=col,
                      font=("Consolas", 10), tags=tag)
    c.create_rectangle(x0, y0 + 160, x1, y1, fill="#181818", width=0, tags=tag)
    err = ["Traceback (most recent call last):", '  File "app.py", line 5, in <module>',
           '  File "app.py", line 2, in profile', "KeyError: 'user_id'"]
    for i, line in enumerate(err):
        c.create_text(x0 + 14, y0 + 178 + i * 18, text=line, anchor="w",
                      fill="#F14C4C" if i == 3 else "#CCCCCC", font=("Consolas", 9), tags=tag)
    c.tag_lower("backdrop")


backdrop()
mon.win.geometry(f"{W}x{H}+{L}+{TOP}")
hwnd = int(mon.win.frame(), 16)


def grab():
    """Pixel BGRA della finestra della mascotte (PrintWindow) + la barra disegnata sotto."""
    u, g = screen.user32, screen.gdi32
    wdc = u.GetWindowDC(hwnd)
    dc = g.CreateCompatibleDC(wdc)
    bmp = g.CreateCompatibleBitmap(wdc, W, H)
    old = g.SelectObject(dc, bmp)
    u.PrintWindow(hwnd, dc, screen.PW_RENDERFULLCONTENT)
    bi = screen.BITMAPINFOHEADER(ctypes.sizeof(screen.BITMAPINFOHEADER), W, -H, 1, 32, 0)
    buf = ctypes.create_string_buffer(W * H * 4)
    g.GetDIBits(dc, bmp, 0, H, buf, ctypes.byref(bi), 0)
    g.SelectObject(dc, old); g.DeleteObject(bmp); g.DeleteDC(dc); u.ReleaseDC(hwnd, wdc)
    return buf.raw + TASKBAR


TASKBAR = bytearray(b"\x2a\x22\x1c\x00" * (W * BAR))   # BGRA #1C222A
for k, colr in enumerate((b"\xd7\x78\x00\x00", b"\x38\xa8\xe8\x00", b"\x5f\xb8\x5f\x00")):
    cx = W // 2 - 40 + k * 40
    for yy in range(10, 30):
        for xx in range(cx - 10, cx + 10):
            TASKBAR[(yy * W + xx) * 4:(yy * W + xx) * 4 + 4] = colr
TASKBAR = bytes(TASKBAR)

frames, t0 = [], time.time()
SCRIPT = [(1.2, lambda: pet.set_bubble("chat", TXT["hi"])),
          (4.0, lambda: setattr(pet, "menu_until", time.time() + 2.5)),
          (6.5, lambda: pet.explain_screen(TXT["q"]))]
END = 17.0


def shoot():
    t = time.time() - t0
    while SCRIPT and t >= SCRIPT[0][0]:
        SCRIPT.pop(0)[1]()
    frames.append(grab())
    if t < END:
        root.after(100, shoot)
    else:
        root.quit()


root.after(800, lambda: (setattr(sys.modules[__name__], "t0", time.time()), shoot()))
root.mainloop()
print("fotogrammi", len(frames))
gifenc.write(OUT, W, H + BAR, frames, delay_cs=10, last_cs=400)
print("scritto", OUT, OUT.stat().st_size // 1024, "KB")
