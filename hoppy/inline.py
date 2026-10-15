"""Claude inline trigger (Windows) - un text-expander con AI.

Due modalità, scelte dal marcatore di chiusura:

  ;;traduci in inglese: ciao a tutti;;   TRASFORMA: il testo tra i marcatori va a
                                         Claude e viene sostituito inline dalla risposta.
  ;;spiegami la pagina??                 CHIEDI: il trigger viene cancellato, l'intero
                                         documento corrente (Ctrl+A, Ctrl+C) va a Claude
                                         come contesto e la risposta compare in una
                                         finestra di lettura. Il documento non viene toccato.

- Nulla viene scritto su disco. In rete va solo il testo tra i tuoi marcatori e,
  in modalità CHIEDI, il contenuto del documento corrente, inviati alla CLI
  `claude` (piano abbonamento, nessuna API key).
- Un indicatore sempre in basso a destra mostra lo stato; il pulsante Esci chiude.
- Non viene tenuto alcun log di ciò che digiti: il buffer serve solo a riconoscere
  i marcatori e vive in memoria.

La cattura si annulla con Invio, Esc, Tab, frecce o oltre MAX_LEN caratteri.
"""
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
import queue
import random
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path

from . import config as pet_config
from .i18n import T

# ---- configurazione ---------------------------------------------------------
START = ";;"        # marcatore di apertura
END = ";;"          # chiusura modalità TRASFORMA (sostituisce inline)
ASK_END = "??"      # chiusura modalità CHIEDI (legge il documento, risponde in finestra)
MODEL = pet_config.load()["inline_model"]   # dalle Impostazioni della mascotte
MAX_LEN = 2000      # caratteri massimi di una richiesta prima di annullare
MAX_CONTEXT = 150_000  # caratteri massimi di documento inviati come contesto
TIMEOUT_S = 180
SYSTEM_PROMPT = T(
    "Sei un assistente integrato in un campo di testo su Windows. L'utente ti "
    "invia un'ISTRUZIONE. Rispondi SOLO con il testo risultante, pronto per "
    "essere inserito dove si trova il cursore: niente preamboli, spiegazioni, "
    "virgolette o markdown. Mantieni la lingua dell'istruzione. Sii conciso."
)
ASK_PROMPT = T(
    "Sei un assistente integrato nel desktop di Windows. Ricevi il CONTENUTO del "
    "documento o della pagina che l'utente ha aperto e una sua DOMANDA. Rispondi "
    "alla domanda basandoti sul contenuto, in modo chiaro e ordinato, nella lingua "
    "della domanda. Puoi usare paragrafi ed elenchi puntati semplici; niente "
    "tabelle markdown. Se il contenuto è vuoto o non pertinente, dillo in una riga."
)
# -----------------------------------------------------------------------------

TEST_MODE = os.environ.get("CLAUDE_INLINE_TEST") == "1"
PET_PORT = 48761    # porta locale della mascotte da desktop (hoppy.pet)


def pet_connect():
    """Connessione locale alla mascotte da desktop, o None se non è avviata."""
    try:
        return socket.create_connection(("127.0.0.1", PET_PORT), timeout=0.3)
    except OSError:
        return None


def pet_send(sock, **msg):
    try:
        sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        return True
    except OSError:
        return False

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
LLKHF_INJECTED = 0x10
KEYEVENTF_KEYUP = 0x0002

VK_BACK, VK_TAB, VK_RETURN, VK_ESCAPE = 0x08, 0x09, 0x0D, 0x1B
VK_SHIFT, VK_CONTROL, VK_MENU, VK_CAPITAL = 0x10, 0x11, 0x12, 0x14
VK_A, VK_C, VK_V, VK_LEFT = 0x41, 0x43, 0x56, 0x25
LWIN, RWIN = 0x5B, 0x5C
SHIFTS = (0x10, 0xA0, 0xA1)
CTRLS = (0x11, 0xA2, 0xA3)
ALTS = (0x12, 0xA4, 0xA5)
CANCEL_VKS = {VK_RETURN, VK_ESCAPE, VK_TAB,
              0x21, 0x22, 0x23, 0x24,            # PgUp PgDn End Home
              0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E}  # frecce, Insert, Delete
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
CREATE_NO_WINDOW = 0x08000000
GWL_EXSTYLE, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW = -20, 0x08000000, 0x80

LRESULT = ctypes.c_ssize_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD),
                ("flags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wt.DWORD]
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.GetKeyboardLayout.restype = ctypes.c_void_p

events = queue.Queue()


# ---- traduzione tasto -> carattere -----------------------------------------
class Modifiers:
    """Stato dei modificatori ricostruito dal flusso di eventi (affidabile in LL hook)."""
    def __init__(self):
        self.shift = self.ctrl = self.alt = False
        self.caps = bool(user32.GetKeyState(VK_CAPITAL) & 1)

    def update(self, vk, down):
        if vk in SHIFTS:
            self.shift = down
        elif vk in CTRLS:
            self.ctrl = down
        elif vk in ALTS:
            self.alt = down
        elif vk == VK_CAPITAL and down:
            self.caps = not self.caps

    def state_array(self, vk):
        buf = (ctypes.c_ubyte * 256)()
        if self.shift:
            buf[VK_SHIFT] = 0x80
        if self.ctrl:
            buf[VK_CONTROL] = 0x80
        if self.alt:
            buf[VK_MENU] = 0x80
        if self.caps:
            buf[VK_CAPITAL] = 0x01
        buf[vk] = 0x80
        return buf


def vk_to_char(vk, scan, mods):
    """Ritorna il carattere stampabile prodotto dal tasto, o None."""
    out = ctypes.create_unicode_buffer(8)
    hkl = user32.GetKeyboardLayout(
        user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None))
    n = user32.ToUnicodeEx(vk, scan, mods.state_array(vk), out, len(out), 0x4, hkl)
    if n == 1 and out[0] >= " ":
        return out[0]
    return None


# ---- hook -------------------------------------------------------------------
class Listener:
    def __init__(self):
        self.mods = Modifiers()
        self.state = "idle"   # idle | capture
        self.recent = ""      # coda per riconoscere START quando idle
        self.request = ""     # testo catturato (comprende END finché non si valuta)
        self.typed = 0        # caratteri stampabili scritti dall'inizio di START
        self.busy = False     # True mentre elaboriamo una richiesta
        self._cb = HOOKPROC(self._proc)

    def run(self):
        hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._cb, None, 0)
        if not hook:
            events.put(("fatal", f"SetWindowsHookEx fallita (err {ctypes.get_last_error()})"))
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _proc(self, nCode, wParam, lParam):
        if nCode == 0:
            self._handle(wParam, ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents)
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _handle(self, msg, kb):
        vk, injected = kb.vkCode, bool(kb.flags & LLKHF_INJECTED)
        down = msg in (WM_KEYDOWN, WM_SYSKEYDOWN)
        up = msg in (WM_KEYUP, WM_SYSKEYUP)
        if down or up:
            self.mods.update(vk, down)
        if not down:
            return
        # Il nostro stesso output (iniettato) e tutto mentre siamo occupati non
        # devono rientrare nella cattura. In test accettiamo l'input iniettato.
        if self.busy:
            return
        if injected and not TEST_MODE:
            return

        if vk == VK_BACK:
            if self.state == "capture":
                if self.request:
                    self.request = self.request[:-1]
                    self.typed -= 1
                else:
                    self._reset()
            return
        if vk in CANCEL_VKS or vk in (LWIN, RWIN):
            if self.state == "capture":
                self._reset()
            return

        ch = vk_to_char(vk, kb.scanCode, self.mods)
        if ch is None:
            return
        if self.state == "idle":
            self.recent = (self.recent + ch)[-len(START):]
            if self.recent == START:
                self.state = "capture"
                self.request = ""
                self.typed = len(START)
                self.recent = ""
        else:  # capture
            self.request += ch
            self.typed += 1
            mode = ("transform" if self.request.endswith(END)
                    else "ask" if self.request.endswith(ASK_END) else None)
            if mode:
                closer = END if mode == "transform" else ASK_END
                text = self.request[:-len(closer)].strip()
                total = self.typed
                self.busy = True
                self._reset()
                if text:
                    events.put(("fire", mode, text, total))
                else:
                    events.put(("abort", total))  # delimitatori vuoti
            elif self.typed - len(START) > MAX_LEN:
                self._reset()

    def _reset(self):
        self.state = "idle"
        self.recent = ""
        self.request = ""
        self.typed = 0


# ---- invio tasti / clipboard ------------------------------------------------
def tap(vk):
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def backspaces(n):
    for _ in range(n):
        tap(VK_BACK)
        time.sleep(0.004)


def paste_via_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    time.sleep(0.03)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    tap(VK_V)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def ctrl_tap(vk):
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    tap(vk)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def get_clip(root):
    try:
        return root.clipboard_get()
    except tk.TclError:
        return ""


def grab_document(root):
    """Ctrl+A, Ctrl+C sul documento in primo piano; ripristina la clipboard. Ritorna il testo."""
    backup = get_clip(root)
    root.clipboard_clear()
    root.update()
    ctrl_tap(VK_A)
    time.sleep(0.05)
    ctrl_tap(VK_C)
    text = ""
    for _ in range(20):  # fino a ~1 s: pagine lunghe impiegano un po' a copiare
        time.sleep(0.05)
        root.update()
        text = get_clip(root)
        if text:
            break
    tap(VK_LEFT)  # toglie la selezione totale, così un tasto non cancella tutto
    root.clipboard_clear()
    if backup:
        root.clipboard_append(backup)
    root.update()
    return text


def type_unicode(text):
    """Scrive testo arbitrario via SendInput (per ripristinare l'originale su errore)."""
    INPUT_KEYBOARD, KEYEVENTF_UNICODE = 1, 0x0004

    class KI(ctypes.Structure):
        _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                    ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("ki", KI)]
        _anonymous_ = ("u",)
        _fields_ = [("type", wt.DWORD), ("u", _U)]

    arr = []
    for ch in text:
        for up in (0, KEYEVENTF_UNICODE | 0x0002):
            i = INPUT(type=INPUT_KEYBOARD)
            i.ki = KI(wVk=0, wScan=ord(ch), dwFlags=KEYEVENTF_UNICODE | up,
                      time=0, dwExtraInfo=None)
            arr.append(i)
    if arr:
        buf = (INPUT * len(arr))(*arr)
        user32.SendInput(len(arr), buf, ctypes.sizeof(INPUT))


# ---- chiamata a Claude ------------------------------------------------------
def ask_claude(instruction, context=None):
    """context=None: modalità TRASFORMA. Stringa (anche vuota): modalità CHIEDI."""
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    if not Path(exe).exists():
        return None, T("Eseguibile 'claude' non trovato nel PATH.")
    if context is None:
        system, prompt = SYSTEM_PROMPT, T("ISTRUZIONE:") + f"\n{instruction}"
    else:
        system = ASK_PROMPT
        prompt = (T("CONTENUTO DEL DOCUMENTO:") + f"\n<<<\n{context[:MAX_CONTEXT]}\n>>>\n\n"
                  + T("DOMANDA:") + f"\n{instruction}")
    cmd = [exe, "-p", "--model", MODEL, "--output-format", "text",
           "--no-session-persistence", "--setting-sources", "",
           "--strict-mcp-config", "--tools", "", "--system-prompt", system]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True,
                           text=True, encoding="utf-8", timeout=TIMEOUT_S,
                           cwd=tempfile.gettempdir(), creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None, T("Nessuna risposta entro {secs}s.").format(secs=TIMEOUT_S)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout or f"exit code {r.returncode}").strip()
    return r.stdout.strip(), None


# ---- indicatore di stato (trasparenza + kill switch) ------------------------
class Chip:
    def __init__(self, root, on_quit, text):
        w = self.win = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True, "-alpha", 0.92)
        w.configure(bg="#1e1e1e")
        frame = tk.Frame(w, bg="#1e1e1e", padx=8, pady=4)
        frame.pack()
        self.dot = tk.Label(frame, text="●", bg="#1e1e1e", fg="#5fb85f", font=("Segoe UI", 9))
        self.dot.pack(side="left")
        self.lbl = tk.Label(frame, text=text, bg="#1e1e1e",
                            fg="#cfcfcf", font=("Segoe UI", 9))
        self.lbl.pack(side="left", padx=6)
        tk.Button(frame, text=T("Esci"), command=on_quit, bg="#2b2b2b", fg="#cfcfcf",
                  relief="flat", font=("Segoe UI", 8), padx=6, cursor="hand2").pack(side="left")
        w.update_idletasks()
        bw, bh = w.winfo_reqwidth(), w.winfo_reqheight()
        # Angolo in basso a destra del monitor PRINCIPALE (area di lavoro, esclusa taskbar).
        rect = wt.RECT()
        if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):  # SPI_GETWORKAREA
            x, y = rect.right - bw - 16, rect.bottom - bh - 16
        else:
            x = w.winfo_screenwidth() - bw - 16
            y = w.winfo_screenheight() - bh - 56
        w.geometry(f"+{x}+{y}")
        w.lift()
        # trascinabile
        for widget in (frame, self.lbl):
            widget.bind("<Button-1>", self._press)
            widget.bind("<B1-Motion>", self._drag)

    def _press(self, e):
        self._dx, self._dy = e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y()

    def _drag(self, e):
        self.win.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def set(self, text, color):
        self.dot.config(fg=color)
        self.lbl.config(text=text)


def work_area():
    """Area di lavoro del monitor principale (esclusa la taskbar)."""
    rect = wt.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
    return rect


def round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


class Mascot:
    """Hoppy (o il granchietto): sbuca dal bordo inferiore dello schermo, aspetta
    con te e 'parla' la risposta in un fumetto. Non prende mai il focus, così il
    documento resta la finestra attiva per incollare."""
    KEY = "#010203"   # colore reso trasparente (e click-through)
    ORANGE, EYE = "#D97757", "#1F1E1D"
    OCTOPUS = pet_config.load()["character"] == "octopus"   # Hoppy (default) o il granchietto
    BODY = "#A77BD6" if OCTOPUS else ORANGE
    OCTO_DARK = "#7E57B0"
    BUBBLE, INK, DIM, ERR, BTN2 = "#FAF9F5", "#1F1E1D", "#6B6A65", "#B3261E", "#ECE9E1"
    PX = 12            # lato di un "pixel" della pixel art
    W, H = 620, 440

    def __init__(self, root, mode, question, prev_hwnd, context_len=None):
        self.root, self.mode, self.prev_hwnd = root, mode, prev_hwnd
        self.alive = True
        self.phase = "emerge"       # emerge | think | talk | idle | leave
        self.t0 = time.time()
        self.pending = None         # risposta arrivata mentre sta ancora sbucando
        self.chars, self.pos = [], 0
        self.answer_plain = ""
        self.error = False
        self.leave_after_talk = False
        self.bob = 0
        self.arm_up = False
        self.blink_until = 0.0
        self.next_blink = self.t0 + 1.5
        self.dots = -1

        w = self.win = tk.Toplevel(root)
        w.withdraw()
        w.overrideredirect(True)
        w.configure(bg=self.KEY)
        w.attributes("-topmost", True, "-transparentcolor", self.KEY)
        self.c = tk.Canvas(w, width=self.W, height=self.H, bg=self.KEY,
                           highlightthickness=0, bd=0)
        self.c.pack()
        self._draw_crab()
        self._draw_bubble(question, context_len)

        r = work_area()
        x = r.left + (r.right - r.left - self.W) // 2
        w.geometry(f"{self.W}x{self.H}+{x}+{r.bottom - self.H}")
        w.update_idletasks()
        hwnd = int(w.frame(), 16)
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        w.deiconify()
        if prev_hwnd and user32.GetForegroundWindow() != prev_hwnd:
            user32.SetForegroundWindow(prev_hwnd)   # il focus resta nel documento
        self._tick()

    # ---- disegno ---------------------------------------------------------------
    def _draw_crab(self):
        p, c = self.PX, self.c
        bx = (self.W - 7 * p) // 2
        by = self.H - 2 - 7 * p              # bordo superiore del corpo a riposo
        self.crab_top = by
        self.hidden_off = 9 * p + 8          # anche la cupola del polipetto sta sotto il bordo

        def block(col, row, tags, fill=self.BODY, h=p, w=1.0):
            c.create_rectangle(bx + col * p, by + row * p, bx + (col + w) * p,
                               by + row * p + h, fill=fill, width=0, tags=tags)

        for row in range(5):                 # corpo 7x5
            for col in range(7):
                block(col, row, ("crab",))
        for col in (1, 5):                   # occhi: la riga alta fa da palpebra
            block(col, 1, ("crab", "eyetop"), self.EYE)
            block(col, 2, ("crab",), self.EYE)
        block(-1, 2, ("crab", "larm"))       # braccia
        block(7, 2, ("crab", "rarm"))
        if self.OCTOPUS:                     # Hoppy: cupola, macchioline e tentacoli arricciati
            block(1, -1, ("crab",), w=5)
            block(2, -1.5, ("crab",), h=p // 2, w=3)
            block(1.6, -0.6, ("crab",), self.OCTO_DARK, h=p // 2, w=0.6)
            block(4.6, -1.1, ("crab",), self.OCTO_DARK, h=p // 2, w=0.5)
            for i, col in enumerate((0, 2, 4, 6)):
                out = -0.5 if i < 2 else 0.5
                block(col, 5, ("crab",), h=int(1.4 * p))
                block(col + out, 6.2, ("crab",), h=int(0.8 * p))
                block(col + 0.3, 5.6, ("crab",), self.OCTO_DARK, h=p // 2, w=0.4)
        else:
            for col in (0, 2, 4, 6):         # zampe
                block(col, 5, ("crab",), h=2 * p)
        c.create_rectangle(bx + 2 * p, by + 3 * p + 3, bx + 5 * p, by + 4 * p - 2,
                           fill=self.EYE, width=0, tags=("crab", "mouth"), state="hidden")
        c.tag_bind("crab", "<Button-1>", lambda e: self._skip())
        c.move("crab", 0, self.hidden_off)   # parte nascosta sotto il bordo
        self.crab_off = self.hidden_off

    def _draw_bubble(self, question, context_len):
        c, W = self.c, self.W
        top, left, right = 6, 6, W - 6
        bottom = self.crab_top - 22
        round_rect(c, left, top, right, bottom, 22, fill=self.BUBBLE, outline=self.ORANGE,
                   width=2, tags=("bubble",))
        cx = W // 2                          # codina del fumetto verso la mascotte
        c.create_polygon(cx - 14, bottom - 1, cx + 14, bottom - 1, cx, bottom + 16,
                         fill=self.BUBBLE, outline=self.ORANGE, width=2, tags=("bubble",))
        c.create_rectangle(cx - 12, bottom - 4, cx + 12, bottom + 1, fill=self.BUBBLE,
                           width=0, tags=("bubble",))
        q = question if len(question) <= 80 else question[:77] + "…"
        head = T("Mi hai chiesto: «{q}»").format(q=q)
        if context_len is not None:
            head += T("   ·   ho letto {context_len} caratteri").format(context_len=context_len)
        c.create_text(28, 20, anchor="nw", text=head, fill=self.DIM, font=("Segoe UI", 9),
                      width=W - 56, tags=("bubble",))

        t = self.txt = tk.Text(c, wrap="word", bg=self.BUBBLE, fg=self.INK, relief="flat",
                               bd=0, highlightthickness=0, font=("Segoe UI", 10),
                               cursor="arrow", padx=0, pady=0, state="disabled")
        t.tag_configure("b", font=("Segoe UI", 10, "bold"))
        t.tag_configure("err", foreground=self.ERR)
        t.tag_configure("dim", foreground=self.DIM, font=("Segoe UI", 10, "italic"))
        c.create_window(28, 46, anchor="nw", window=t, width=W - 56,
                        height=bottom - 46 - 50, tags=("bubble",))

        bar = tk.Frame(c, bg=self.BUBBLE)
        self.btns = []
        for label, cmd, bg, fg in ((T("Incolla al cursore"), self.paste, self.ORANGE, "white"),
                                   (T("Copia"), self.copy, self.BTN2, self.INK),
                                   (T("Chiudi"), self.leave, self.BUBBLE, self.DIM)):
            b = tk.Button(bar, text=label, command=cmd, bg=bg, fg=fg, relief="flat", bd=0,
                          font=("Segoe UI", 9), padx=12, pady=4, cursor="hand2",
                          activebackground=bg, activeforeground=fg)
            b.pack(side="left", padx=(0, 8))
            self.btns.append(b)
        self.status = tk.Label(bar, text="", bg=self.BUBBLE, fg=self.DIM, font=("Segoe UI", 9))
        self.status.pack(side="left")
        c.create_window(28, bottom - 42, anchor="nw", window=bar, tags=("btns",))
        c.itemconfigure("bubble", state="hidden")
        c.itemconfigure("btns", state="hidden")

    def _set_text(self, segments):
        t = self.txt
        t.config(state="normal")
        t.delete("1.0", "end")
        for s, tag in segments:
            t.insert("end", s, tag)
        t.config(state="disabled")

    # ---- animazione ------------------------------------------------------------
    def _tick(self):
        if not self.alive:
            return
        now = time.time()
        t = now - self.t0
        c = self.c
        if self.phase == "emerge":
            step = min(self.crab_off, max(3, int(self.crab_off * 0.2)))
            c.move("crab", 0, -step)
            self.crab_off -= step
            if self.crab_off <= 0:
                c.itemconfigure("bubble", state="normal")
                self.phase = "think"
                if self.pending:
                    self._start_talk(*self.pending)
        elif self.phase == "leave":
            step = min(self.hidden_off - self.crab_off, max(3, int((self.crab_off + 6) * 0.25)))
            c.move("crab", 0, step)
            self.crab_off += step
            if self.crab_off >= self.hidden_off:
                self.destroy()
                return
        else:
            self._bob(t)
            self._blink(now)
            if self.phase == "think":
                self._arms(int(t / 0.45) % 2 == 1)
                d = int(t / 0.4) % 4
                if d != self.dots:
                    self.dots = d
                    msg = T("Sto leggendo la pagina") if self.mode == "ask" else T("Ci sto lavorando")
                    self._set_text([(msg + "." * d, "dim")])
            elif self.phase == "talk":
                self._arms(int(t / 0.18) % 2 == 1)
                c.itemconfigure("mouth", state="normal" if int(t / 0.11) % 2 else "hidden")
                self._write(max(2, len(self.chars) // 180))
            else:
                self._arms(False)
        self.root.after(30, self._tick)

    def _bob(self, t):
        target = round(3 * math.sin(t * 4.5))
        if target != self.bob:
            self.c.move("crab", 0, target - self.bob)
            self.bob = target

    def _blink(self, now):
        if self.blink_until and now >= self.blink_until:
            self.c.itemconfigure("eyetop", fill=self.EYE)
            self.blink_until = 0.0
        elif not self.blink_until and now >= self.next_blink:
            self.c.itemconfigure("eyetop", fill=self.BODY)
            self.blink_until = now + 0.13
            self.next_blink = now + random.uniform(2.2, 4.5)

    def _arms(self, up):
        if up != self.arm_up:
            d = -(self.PX // 2) if up else self.PX // 2
            self.c.move("larm", 0, d)        # braccia alternate: sembra gesticolare
            self.c.move("rarm", 0, -d)
            self.arm_up = up

    # ---- parlato ---------------------------------------------------------------
    def answer(self, text, error=False, then_leave=False):
        if not self.alive:
            return
        if self.phase == "emerge":
            self.pending = (text, error, then_leave)
        else:
            self._start_talk(text, error, then_leave)

    def _start_talk(self, text, error, then_leave):
        self.pending = None
        self.answer_plain = text.replace("**", "")
        self.error, self.leave_after_talk = error, then_leave
        self.chars = []
        for i, part in enumerate(text.split("**")):     # **grassetto** -> grassetto vero
            tag = "err" if error else ("b" if i % 2 else "")
            self.chars.extend((ch, tag) for ch in part)
        self.pos = 0
        self._set_text([])
        self.phase = "talk"

    def _write(self, n):
        end = min(len(self.chars), self.pos + n)
        if self.pos < end:
            t = self.txt
            t.config(state="normal")
            i = self.pos
            while i < end:                   # inserisce a gruppi con lo stesso stile
                tag, j = self.chars[i][1], i
                while j < end and self.chars[j][1] == tag:
                    j += 1
                t.insert("end", "".join(ch for ch, _ in self.chars[i:j]), tag)
                i = j
            t.config(state="disabled")
            t.see("end")
            self.pos = end
        if self.pos >= len(self.chars):
            self._finish_talk()

    def _skip(self):
        if self.phase == "talk":
            self._write(len(self.chars))

    def _finish_talk(self):
        self.c.itemconfigure("mouth", state="hidden")
        self.phase = "idle"
        if self.leave_after_talk:
            self.root.after(900, self.leave)
            return
        if self.error or self.mode != "ask":
            for b in self.btns[:2]:
                b.pack_forget()
        self.c.itemconfigure("btns", state="normal")

    # ---- azioni ----------------------------------------------------------------
    def copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.answer_plain)
        self.root.update()
        self.status.config(text=T("Copiato"))

    def paste(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.answer_plain)
        self.root.update()
        self.leave()
        if self.prev_hwnd:
            user32.SetForegroundWindow(self.prev_hwnd)
        self.root.after(150, lambda: ctrl_tap(VK_V))

    def leave(self):
        if not self.alive or self.phase == "leave":
            return
        for tag in ("bubble", "btns", "mouth"):
            self.c.itemconfigure(tag, state="hidden")
        self.phase = "leave"

    def destroy(self):
        self.alive = False
        try:
            self.win.destroy()
        except tk.TclError:
            pass


def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    if not pet_config.mark_running("hoppy.inline"):
        return                                   # gira già
    quit_h = pet_config.quit_event()
    root = tk.Tk()
    root.withdraw()
    idle_text = f"Claude  {START}…{END}  ·  {START}…{ASK_END}"
    chip = Chip(root, root.destroy, idle_text)
    listener = Listener()
    threading.Thread(target=listener.run, daemon=True).start()
    ui = {"mascot": None}

    def mascot_for(mode, text, prev_hwnd, context):
        """Ritorna la mascotte della richiesta corrente, creandola se serve."""
        m = ui["mascot"]
        if m is None or not m.alive:
            m = ui["mascot"] = Mascot(root, mode, text, prev_hwnd,
                                      None if context is None else len(context))
        return m

    def do_claude(mode, text, total, context, prev_hwnd):
        res, err = ask_claude(text, context)
        events.put(("done", mode, res, err, text, total, context, prev_hwnd))

    def poll():
        if pet_config.quit_requested(quit_h):        # la mascotte si aggiorna: esco
            return root.destroy()
        try:
            while True:
                kind, *data = events.get_nowait()
                if kind == "fire":
                    mode, text, total = data
                    prev_hwnd = user32.GetForegroundWindow()
                    chip.set("Claude…", "#d6a13b")
                    root.update()
                    backspaces(total)                 # rimuovi il testo delimitato
                    context = None
                    if mode == "ask":
                        time.sleep(0.05)
                        context = grab_document(root)
                    if ui["mascot"]:
                        ui["mascot"].destroy()        # una sola mascotte alla volta
                    # se la mascotte da desktop è attiva, spiega lei; altrimenti quella di qui
                    ui["link"] = pet_connect()
                    if ui["link"] and not pet_send(
                            ui["link"], t="start", mode=mode, q=text, hwnd=prev_hwnd,
                            ctx=None if context is None else len(context)):
                        ui["link"] = None
                    if not ui["link"]:
                        mascot_for(mode, text, prev_hwnd, context)
                    threading.Thread(target=do_claude, daemon=True,
                                     args=(mode, text, total, context, prev_hwnd)).start()
                elif kind == "abort":
                    (total,) = data
                    backspaces(total)
                    listener.busy = False
                    chip.set(idle_text, "#5fb85f")
                elif kind == "done":
                    mode, res, err, text, total, context, prev_hwnd = data
                    link, ui["link"] = ui.get("link"), None
                    delegated = False
                    if link:                          # la risposta va alla mascotte da desktop
                        delegated = pet_send(link, t="answer", mode=mode, error=bool(err),
                                             text=(T("Non ci sono riuscito: ") + err) if err else res)
                        link.close()
                    m = None if delegated else mascot_for(mode, text, prev_hwnd, context)
                    if err:
                        if mode == "transform":
                            type_unicode(START + text + END)  # ripristina ciò che avevi scritto
                        if m:
                            m.answer(T("Non ci sono riuscito: ") + err, error=True)
                        chip.set(T("Errore"), "#e06c6c")
                        root.after(2500, lambda: chip.set(idle_text, "#5fb85f"))
                    elif mode == "transform":
                        paste_via_clipboard(root, res)
                        if m:
                            m.answer(T("Fatto!"), then_leave=True)
                        chip.set(idle_text, "#5fb85f")
                    else:
                        if m:
                            m.answer(res)
                        chip.set(idle_text, "#5fb85f")
                    listener.busy = False
                elif kind == "fatal":
                    chip.set(T("Hook non attivo"), "#e06c6c")
        except queue.Empty:
            pass
        root.after(40, poll)

    root.after(40, poll)
    root.mainloop()


if __name__ == "__main__":
    main()
