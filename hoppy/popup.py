"""Claude a portata di hotkey (Windows).

Ctrl+Shift+Space      cattura il testo selezionato e apre il popup sotto il mouse
Invio                 invia l'istruzione a Claude (Shift+Invio = a capo)
Invio / Sostituisci   incolla la risposta al posto della selezione
Copia                 mette la risposta in clipboard senza incollarla
Esc                   chiude il popup e ripristina la clipboard precedente
"""
import ctypes
import ctypes.wintypes as wt
import queue
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from . import config as pet_config
from .i18n import T

# ---- configurazione ---------------------------------------------------------
# Evita Alt e Win: il loro rilascio "a vuoto" attiva barra menu / key tips nell'app
# in primo piano (es. Blocco note di Windows 11) e Ctrl+C / Ctrl+V non arrivano più
# all'editor. Verificato: con Ctrl+Alt la cattura fallisce, con Ctrl+Shift funziona.
HOTKEY_MODS = 0x0002 | 0x0004 | 0x4000  # MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
HOTKEY_VK = 0x20                        # VK_SPACE
MODEL = pet_config.load()["popup_model"]    # dalle Impostazioni della mascotte
TIMEOUT_S = 120
SYSTEM_PROMPT = T(
    "Sei un assistente integrato in un popup di sistema su Windows. "
    "L'utente ti dà un'ISTRUZIONE e, se presente, un TESTO SELEZIONATO. "
    "Rispondi SOLO con il testo risultante, pronto per essere incollato al posto "
    "della selezione: niente preamboli, spiegazioni, virgolette o markdown. "
    "Se non c'è testo selezionato, rispondi all'istruzione nel modo più conciso "
    "possibile. Mantieni la lingua del testo selezionato, o dell'istruzione se "
    "non c'è selezione."
)
# -----------------------------------------------------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True)
WM_HOTKEY = 0x0312
KEYEVENTF_KEYUP = 0x0002
VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN = 0x10, 0x11, 0x12, 0x5B, 0x5C
VK_C, VK_V = 0x43, 0x56
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 76, 77, 78, 79
CREATE_NO_WINDOW = 0x08000000

BG, BG_IN, BG_OUT = "#1e1e1e", "#2b2b2b", "#252526"
FG, FG_DIM, FG_ERR, ACCENT = "#e6e6e6", "#8a8a8a", "#f28b82", "#3b6fd6"
FONT, FONT_SMALL = ("Segoe UI", 10), ("Segoe UI", 9)

events = queue.Queue()


def hotkey_thread():
    """RegisterHotKey e il message loop devono vivere nello stesso thread."""
    if not user32.RegisterHotKey(None, 1, HOTKEY_MODS, HOTKEY_VK):
        events.put(("hotkey_error", ctypes.get_last_error()))
        return
    msg = wt.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            events.put(("hotkey", None))


def wait_modifiers_released(max_s=1.5):
    """Aspetta che Ctrl/Alt/Shift/Win siano rilasciati, altrimenti Ctrl+C diventa Ctrl+Alt+C."""
    deadline = time.time() + max_s
    mods = (VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)
    while time.time() < deadline:
        if not any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in mods):
            return
        time.sleep(0.01)


def send_ctrl(vk):
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def ask_claude(instruction, selection):
    """Ritorna (testo, None) oppure (None, messaggio di errore)."""
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    if not Path(exe).exists():
        return None, T("Eseguibile 'claude' non trovato nel PATH.")
    prompt = T("ISTRUZIONE:") + f"\n{instruction}"
    if selection:
        prompt += "\n\n" + T("TESTO SELEZIONATO:") + f"\n{selection}"
    cmd = [exe, "-p", "--model", MODEL, "--output-format", "text",
           "--no-session-persistence", "--setting-sources", "",
           "--strict-mcp-config", "--tools", "", "--system-prompt", SYSTEM_PROMPT]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           encoding="utf-8", timeout=TIMEOUT_S,
                           cwd=tempfile.gettempdir(), creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None, T("Nessuna risposta entro {secs}s.").format(secs=TIMEOUT_S)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout or f"exit code {r.returncode}").strip()
    return r.stdout.strip(), None


class Popup:
    def __init__(self, root):
        self.root = root
        self.prev_hwnd = None
        self.selection = ""
        self.clip_backup = ""
        self.result = None
        self.sent_instr = None
        self.busy = False

        w = self.win = tk.Toplevel(root)
        w.withdraw()
        w.title("Claude")
        w.attributes("-topmost", True, "-toolwindow", True)
        w.configure(bg=BG, padx=10, pady=8)
        w.protocol("WM_DELETE_WINDOW", self.close)
        w.bind("<Escape>", lambda e: self.close())

        self.info = tk.Label(w, text="", bg=BG, fg=FG_DIM, anchor="w", font=FONT_SMALL)
        self.info.pack(fill="x")

        self.entry = tk.Text(w, height=2, width=60, wrap="word", bg=BG_IN, fg=FG,
                             insertbackground=FG, relief="flat", font=FONT, padx=6, pady=4)
        self.entry.pack(fill="x", pady=(4, 6))
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)  # lascia inserire l'a capo

        self.out = tk.Text(w, height=8, width=60, wrap="word", bg=BG_OUT, fg=FG,
                           relief="flat", font=FONT, padx=6, pady=4, state="disabled")

        self.btns = tk.Frame(w, bg=BG)
        self.btns.pack(fill="x")
        self.btn_apply = self._button(self.btns, T("Sostituisci"), self.apply, ACCENT)
        self.btn_apply.pack(side="left")
        self.btn_copy = self._button(self.btns, T("Copia"), self.copy, BG_IN)
        self.btn_copy.pack(side="left", padx=(6, 0))
        self.status = tk.Label(self.btns, text="", bg=BG, fg=FG_DIM, font=FONT_SMALL)
        self.status.pack(side="left", padx=10)
        self._button(self.btns, T("Esci"), root.destroy, BG).pack(side="right")

    @staticmethod
    def _button(parent, text, cmd, bg):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=FG, relief="flat",
                         font=FONT_SMALL, padx=10, pady=3, activebackground=BG_OUT,
                         activeforeground=FG, disabledforeground=FG_DIM, cursor="hand2")

    # ---- clipboard -----------------------------------------------------------
    def get_clip(self):
        try:
            return self.root.clipboard_get()
        except tk.TclError:
            return ""

    def set_clip(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def capture_selection(self):
        wait_modifiers_released()
        self.root.clipboard_clear()
        self.root.update()
        send_ctrl(VK_C)
        for _ in range(10):  # alcune app copiano con qualche decina di ms di ritardo
            time.sleep(0.05)
            self.root.update()  # Tk deve ricevere l'avviso che la clipboard è cambiata
            text = self.get_clip()
            if text:
                return text
        return ""

    # ---- apertura / chiusura --------------------------------------------------
    def open(self):
        if self.win.state() == "normal":
            self.focus()
            return
        self.prev_hwnd = user32.GetForegroundWindow()
        self.clip_backup = self.get_clip()
        self.selection = self.capture_selection()
        self.result = None
        self.sent_instr = None
        self.entry.delete("1.0", "end")
        self.out.pack_forget()
        self.status.config(text="")
        n = len(self.selection)
        self.info.config(text=T("Selezione: {n} caratteri").format(n=n) if n
                         else T("Nessuna selezione"))
        self.btn_apply.config(text=T("Sostituisci") if n else T("Inserisci"), state="disabled")
        self.btn_copy.config(state="disabled")
        x, y = self.root.winfo_pointerxy()
        self.win.geometry(f"+{x}+{y}")
        self.win.deiconify()
        self.clamp_to_screen()
        self.focus()

    def clamp_to_screen(self):
        self.win.update_idletasks()
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        vx, vy = user32.GetSystemMetrics(SM_XVIRTUALSCREEN), user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        vw, vh = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN), user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        x = max(vx, min(self.win.winfo_x(), vx + vw - w - 10))
        y = max(vy, min(self.win.winfo_y(), vy + vh - h - 60))
        self.win.geometry(f"+{x}+{y}")

    def focus(self):
        self.win.lift()
        user32.SetForegroundWindow(int(self.win.frame(), 16))
        self.win.focus_force()
        self.entry.focus_set()

    def hide(self):
        self.win.withdraw()

    def close(self):
        if self.clip_backup:
            self.set_clip(self.clip_backup)
        self.hide()

    # ---- richiesta a Claude ---------------------------------------------------
    def on_enter(self, _event):
        instr = self.entry.get("1.0", "end").strip()
        if self.result is not None and instr == self.sent_instr:
            self.apply()
        else:
            self.send(instr)
        return "break"

    def send(self, instr):
        if not instr or self.busy:
            return
        self.busy = True
        self.sent_instr = instr
        self.status.config(text=T("Attendo Claude…"))
        self.btn_apply.config(state="disabled")
        self.btn_copy.config(state="disabled")
        threading.Thread(
            target=lambda: events.put(("result", ask_claude(instr, self.selection))),
            daemon=True).start()

    def on_result(self, text, err):
        self.busy = False
        self.status.config(text="")
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        if err:
            self.result = None
            self.out.insert("1.0", T("Errore: ") + err)
            self.out.config(fg=FG_ERR)
        else:
            self.result = text
            self.out.insert("1.0", text)
            self.out.config(fg=FG)
            self.btn_apply.config(state="normal")
            self.btn_copy.config(state="normal")
        self.out.config(state="disabled")
        self.out.pack(fill="both", expand=True, pady=(0, 6), before=self.btns)
        self.clamp_to_screen()

    # ---- uso del risultato ----------------------------------------------------
    def apply(self):
        if self.result is None:
            return
        self.set_clip(self.result)
        self.clip_backup = ""  # il risultato resta in clipboard volutamente
        self.hide()
        if self.prev_hwnd:
            user32.SetForegroundWindow(self.prev_hwnd)

        def paste():
            wait_modifiers_released()
            send_ctrl(VK_V)
        self.root.after(150, paste)

    def copy(self):
        if self.result is None:
            return
        self.set_clip(self.result)
        self.clip_backup = ""
        self.status.config(text=T("Copiato"))


def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # il Ctrl+C che inviamo non deve fermarci
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # testo nitido su schermi HiDPI
    except Exception:
        pass
    if not pet_config.mark_running("hoppy.popup"):
        return                                   # gira già
    quit_h = pet_config.quit_event()
    root = tk.Tk()
    root.withdraw()
    popup = Popup(root)
    threading.Thread(target=hotkey_thread, daemon=True).start()

    def poll():
        if pet_config.quit_requested(quit_h):        # la mascotte si aggiorna: esco
            return root.destroy()
        try:
            while True:
                kind, data = events.get_nowait()
                if kind == "hotkey":
                    popup.open()
                elif kind == "result":
                    popup.on_result(*data)
                elif kind == "hotkey_error":
                    messagebox.showerror(
                        "Claude Popup",
                        T("Impossibile registrare la hotkey (errore {data}). "
                          "Un'altra istanza è già in esecuzione?").format(data=data))
                    root.destroy()
                    return
        except queue.Empty:
            pass
        root.after(50, poll)

    root.after(50, poll)
    root.mainloop()


if __name__ == "__main__":
    main()
