"""Impostazioni e wizard della prima volta, in pixel art (tkinter, nessuna dipendenza).

- PixelWindow: finestra senza bordi con cornice a pixel, barra trascinabile, ✕, caselle;
  titoli col font a blocchi GLYPHS, pulsanti PixelButton, tutto disegnato sul canvas.
- SettingsWindow: una scheda per gruppo di SETTINGS (pet_config) + "Avvio e file", con i
  pulsanti per aprire config.json, i comandi rapidi, la memoria e la cartella dei dati.
- Wizard: presentazione in pochi passi (cosa sa fare, progetto hobbistico, cosa manda a
  Claude, cosa attivare), con Hoppy animato. Finché non arrivi in fondo ricompare all'avvio.
"""
import json
import math
import os
import random
import shutil
import time
import tkinter as tk

from . import __version__
from . import config as pc
from .i18n import T

COMMANDS_EXAMPLE = [{"nome": "esempio", "descrizione": "apre il Blocco note",
                     "comando": "notepad", "cartella": "~"}]


def open_file(path):
    try:
        os.startfile(str(path))
        return True
    except OSError:
        return False


# ---- testi del wizard ---------------------------------------------------------------------
PAGES = (
    (T("Ciao!"), T("Sono {app}: una mascotte che vive sul tuo desktop e ti porta Claude "
     "a portata di clic.\n\n"
     "Cammina sulla barra delle applicazioni e sui bordi delle finestre, ti segue col mouse, "
     "si addormenta se la lasci sola, e ogni tanto ha fame.\n\n"
     "In questa breve presentazione ti dico cosa so fare, cosa mando a Claude e cosa vuoi "
     "attivare. Puoi cambiare tutto in seguito: tasto destro su di me > Impostazioni.").format(
        app=pc.APP_NAME)),
    (T("Un progetto hobbistico"), T("Questo è un progetto amatoriale, fatto per divertimento.\n\n"
     "• Non è un prodotto di Anthropic e non è affiliato ad Anthropic.\n"
     "• Può contenere errori: non ha garanzie di nessun tipo.\n"
     "• Alcune funzioni (le pulizie, i comandi rapidi) spostano o eliminano file, o lanciano "
     "comandi: lo fanno solo dopo il tuo sì, ma controlla sempre cosa ti propongo.\n\n"
     "Lo usi a tuo rischio. Se trovi un problema, segnalalo: mi aiuti a migliorare.")),
    (T("Cosa so fare"), T("• Doppio clic su di me: chiacchieriamo. Ricordo il tuo nome e i tuoi "
     "progetti, apro Claude Code su un progetto, imposto promemoria e timer.\n"
     "• Scrivi ;;domanda?? in qualunque programma: ti spiego la risposta su una lavagna. "
     "Con ;;istruzione;; trasformo il testo al posto tuo.\n"
     "• Ctrl+Shift+Spazio: un popup per chiedere al volo.\n"
     "• Ti avviso quando una sessione di Claude Code finisce o aspetta un permesso.\n"
     "• Se copi un errore, posso spiegartelo.\n"
     "• Standup del mattino, cronologia degli appunti, riordino del desktop, pulizia delle "
     "build vecchie.\n"
     "• E poi giochi: palla, nascondino, carezze, biscotti.")),
    (T("Cosa mando a Claude"), T("Uso il tuo Claude Code (claude -p), col tuo account: niente "
     "chiavi da configurare.\n\n"
     "• A Claude va solo quello che serve alla domanda: il testo che scrivi o selezioni, e "
     "pochi pezzi pertinenti delle memorie dei tuoi progetti.\n"
     "• Le chiacchierate e la memoria restano in locale, in un file che puoi leggere.\n"
     "• La cronologia degli appunti resta solo in RAM e salta password e token.\n\n"
     "Ogni chiamata consuma credito del tuo abbonamento (per gli usi headless c'è un credito "
     "mensile separato). Quanto spendo lo vedi nel mio menu.")),
)
CHOICES = ("sessions", "errors", "clip", "ram", "standup", "advice", "reactions", "meeting",
           "music", "desktop", "old", "dev", "m2")

# ---- pixel art ----------------------------------------------------------------------------
PX_BG, PX_PANEL, PX_EDGE, PX_DARK = "#1D1733", "#2A2147", "#F3EBD8", "#0E0B1A"
PX_TEXT, PX_DIM, PX_YELLOW, PX_GREEN, PX_RED = "#F3EBD8", "#A99CC9", "#FFD166", "#7BD389", "#FF6B6B"
PX_OCTO, PX_OCTO_DARK, PX_CRAB, PX_EYE, PX_BLUSH = "#A77BD6", "#7E57B0", "#D97757", "#1F1E1D", "#F4A6A0"
BODY_FONT = ("Consolas", 10)
HELP_FONT = ("Consolas", 9)
TITLES = (T("CIAO!"), T("UN PROGETTO HOBBISTICO"), T("COSA SO FARE"), T("COSA MANDO A CLAUDE"),
          T("COSA ATTIVO?"), T("TUTTO PRONTO!"))
TAB_NAMES = {"Mascotte": T("Mascotte"), "Avvisi": T("Avvisi"), "Pulizie": T("Pulizie"),
             "Avvio e file": T("Avvio e file")}            # nome mostrato delle schede (chiave = pc.TABS)
ACCESSORY = ("wave", "helmet", "sparkles", "lock", "cheer", "hearts")
GLYPHS = {     # font a blocchi 5x7
    "A": ".###.#...##...#######...##...##...#", "B": "####.#...##...#####.#...##...#####.",
    "C": ".###.#...##....#....#....#...#.###.", "D": "####.#...##...##...##...##...#####.",
    "E": "######....#....####.#....#....#####", "F": "######....#....####.#....#....#....",
    "G": ".###.#...##....#.####...##...#.####", "H": "#...##...##...#######...##...##...#",
    "I": ".###...#....#....#....#....#...###.", "J": "..###...#....#....#.#..#.#..#..##..",
    "K": "#...##..#.#.#..##...#.#..#..#.#...#", "L": "#....#....#....#....#....#....#####",
    "M": "#...###.###.#.##.#.##...##...##...#", "N": "#...###..##.#.##..###...##...##...#",
    "O": ".###.#...##...##...##...##...#.###.", "P": "####.#...##...#####.#....#....#....",
    "Q": ".###.#...##...##...##.#.##..#..##.#", "R": "####.#...##...#####.#.#..#..#.#...#",
    "S": ".#####....#.....###.....#....#####.", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", "V": "#...##...##...##...##...#.#.#...#..",
    "W": "#...##...##...##.#.##.#.###.###...#", "X": "#...##...#.#.#...#...#.#.#...##...#",
    "Y": "#...##...#.#.#...#....#....#....#..", "Z": "#####....#...#...#...#...#....#####",
    "!": "..#....#....#....#....#.........#..", "?": ".###.#...#....#...#...#.........#..",
    ".": "................................#..", "-": "................###................",
    ":": ".......#...............#...........", "'": "..#....#...........................",
}


def pixel_text(cv, x, y, text, b, fill, tags):
    """Scritta col font a blocchi: ogni pixel del carattere è un quadrato di lato b."""
    for ch in text.upper():
        g = GLYPHS.get(ch)
        if g:
            for k, on in enumerate(g):
                if on == "#":
                    r, c = divmod(k, 5)
                    cv.create_rectangle(x + c * b, y + r * b, x + (c + 1) * b, y + (r + 1) * b,
                                        fill=fill, width=0, tags=tags)
        x += 6 * b
    return x


def pixel_box(cv, x0, y0, x1, y1, fill, edge=PX_EDGE, tags=(), b=3):
    """Riquadro con bordo a pixel e angoli smussati di un pixel."""
    cv.create_rectangle(x0 + b, y0, x1 - b, y1, fill=edge, width=0, tags=tags)
    cv.create_rectangle(x0, y0 + b, x1, y1 - b, fill=edge, width=0, tags=tags)
    cv.create_rectangle(x0 + b, y0 + b, x1 - b, y1 - b, fill=fill, width=0, tags=tags)


def draw_sprite(cv, sx, sy, p, t, character, acc):
    """Hoppy (o il granchietto) grande, con l'accessorio della pagina; sx, sy = angolo del corpo."""
    octo = character == "octopus"
    body = PX_OCTO if octo else PX_CRAB
    sy += p * 0.25 * (1 if int(t * 2.5) % 2 else 0)          # saltella

    def r(c0, r0, c1, r1, col=body):
        cv.create_rectangle(round(sx + c0 * p), round(sy + r0 * p), round(sx + c1 * p),
                            round(sy + r1 * p), fill=col, width=0, tags=("sprite",))
    for i, col in enumerate((0, 2, 4, 6)):
        if octo:
            out = -1 if i < 2 else 1
            wave = 0.25 * math.sin(t * 4 + i * 1.6)
            r(col, 5, col + 1, 6.4)
            r(col + out * 0.5 + wave, 6.2, col + 1 + out * 0.5 + wave, 7)
            r(col + 0.3, 5.6, col + 0.7, 6, PX_OCTO_DARK)
        else:
            r(col, 5, col + 1, 7)
    r(0, 0, 7, 5)
    if octo:
        r(1, -1, 6, 0)
        r(2, -1.5, 5, -1)
        r(1.6, -0.6, 2.2, -0.1, PX_OCTO_DARK)
        r(4.6, -1.1, 5.1, -0.6, PX_OCTO_DARK)
        r(3.3, -0.4, 3.8, 0.1, PX_OCTO_DARK)
    la = ra = 2                                              # braccia
    if acc == "wave":
        ra = -0.6 if int(t * 3) % 2 else 0.4
    elif acc in ("cheer", "hearts"):
        la = ra = -0.5 + 0.4 * (int(t * 3) % 2)
    r(-1, la, 0, la + 1)
    r(7, ra, 8, ra + 1)
    if acc in ("hearts", "cheer"):                           # occhi felici a "^ ^"
        for c0 in (1, 5):
            r(c0 - 0.15, 2.2, c0 + 0.35, 2.6, PX_EYE)
            r(c0 + 0.3, 1.8, c0 + 0.7, 2.2, PX_EYE)
            r(c0 + 0.65, 2.2, c0 + 1.15, 2.6, PX_EYE)
        r(0.1, 3.0, 1.1, 3.4, PX_BLUSH)
        r(5.9, 3.0, 6.9, 3.4, PX_BLUSH)
    else:
        top = 2 if t % 3.2 < 0.15 else 1                     # sbatte le palpebre
        r(1, top, 2, 3, PX_EYE)
        r(5, top, 6, 3, PX_EYE)
    if acc == "helmet":                                      # elmetto da cantiere
        r(0.6, -1.9, 6.4, -0.5, PX_YELLOW)
        r(-0.2, -0.7, 7.2, -0.2, PX_YELLOW)
        r(3.2, -1.9, 3.8, -0.7, "#E0A800")
    elif acc == "sparkles":                                  # scintille che lampeggiano
        for k, (c0, r0) in enumerate(((-2.5, -1), (9, 0.5), (-1.8, 4.5), (9.5, 4))):
            if int(t * 3 + k) % 2:
                r(c0, r0 - 0.4, c0 + 0.4, r0 + 0.8, PX_YELLOW)
                r(c0 - 0.4, r0, c0 + 0.8, r0 + 0.4, PX_YELLOW)
    elif acc == "lock":                                      # lucchetto accanto
        r(9.6, 2.6, 12.2, 5, PX_YELLOW)
        r(10.0, 1.2, 10.4, 2.6, PX_DIM)
        r(11.4, 1.2, 11.8, 2.6, PX_DIM)
        r(10.0, 0.9, 11.8, 1.3, PX_DIM)
        r(10.7, 3.4, 11.1, 4.2, PX_DARK)
    elif acc == "hearts":                                    # cuoricini che salgono
        for k in range(3):
            f = (t * 0.6 + k / 3) % 1
            hx, hy = 8.5 + k * 1.3, 1 - f * 4
            r(hx, hy, hx + 0.4, hy + 0.4, PX_RED)
            r(hx + 0.6, hy, hx + 1.0, hy + 0.4, PX_RED)
            r(hx, hy + 0.4, hx + 1.0, hy + 0.8, PX_RED)
            r(hx + 0.3, hy + 0.8, hx + 0.7, hy + 1.1, PX_RED)
    elif acc == "wrench":                                    # chiave inglese (impostazioni)
        r(8.6, 1.2, 9.2, 4.6, PX_DIM)
        r(8.2, 0.4, 9.6, 1.2, PX_DIM)
        r(8.7, 0.4, 9.1, 0.9, PX_BG)


class PixelButton:
    """Pulsante a pixel sul canvas, allineato a destra su x1; state() imita quello dei widget ttk."""

    def __init__(self, cv, x1, y, text, command, primary=False, b=2):
        self.cv, self.x1, self.y, self.text, self.b = cv, x1, y, text, b
        self.command, self.primary = command, primary
        self.disabled, self.pressed = False, False
        self.tag = f"btn{id(self)}"
        cv.tag_bind(self.tag, "<ButtonPress-1>", self.on_press)
        self.draw()

    @staticmethod
    def width_of(text, b=2):
        return len(text) * 6 * b + 28

    def draw(self):
        cv, b = self.cv, self.b
        cv.delete(self.tag)
        w = self.width_of(self.text, b)
        x0, x1 = self.x1 - w, self.x1
        y0, y1 = self.y, self.y + 7 * b + 20
        fill = PX_PANEL if self.disabled else (PX_OCTO if self.primary else PX_PANEL)
        edge = PX_DIM if self.disabled else PX_EDGE
        d = 3 if self.pressed else 0
        if not self.pressed:
            cv.create_rectangle(x0 + 6, y0 + 6, x1 + 4, y1 + 4, fill=PX_DARK, width=0, tags=(self.tag,))
        pixel_box(cv, x0 + d, y0 + d, x1 + d, y1 + d, fill, edge, (self.tag,))
        pixel_text(cv, x0 + 14 + d, y0 + 10 + d, self.text, b,
                   PX_DIM if self.disabled else PX_TEXT, (self.tag,))
        cv.itemconfigure(self.tag, state="disabled" if self.disabled else "normal")
        self.width = w

    def state(self, spec=None):
        if spec:
            self.disabled = "disabled" in spec
            self.draw()
        return ("disabled",) if self.disabled else ()

    def config(self, text):
        self.text = text
        self.draw()

    def on_press(self, _e):
        # scatta alla pressione: ridisegnando il pulsante, il rilascio non arriverebbe al tag
        if self.disabled or self.pressed:
            return
        self.pressed = True
        self.draw()
        self.cv.after(90, self.release)

    def release(self):
        self.pressed = False
        if self.cv.winfo_exists():
            self.draw()
            self.command()

    def destroy(self):
        self.cv.delete(self.tag)


class PixelWindow:
    """Finestra senza bordi: cornice a pixel, barra del titolo trascinabile, ✕ ed Esc per chiudere."""
    W, H, FOOTER, STARS = 660, 600, 88, True

    def __init__(self, root, title):
        self.win = win = tk.Toplevel(root)
        win.title(f"{pc.APP_NAME} - {title}")
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        x = (win.winfo_screenwidth() - self.W) // 2
        y = (win.winfo_screenheight() - self.H) // 2
        win.geometry(f"{self.W}x{self.H}+{x}+{y}")
        self.cv = cv = tk.Canvas(win, width=self.W, height=self.H, bg=PX_DARK, highlightthickness=0)
        cv.pack()
        self.frame(title)
        cv.tag_bind("titlebar", "<ButtonPress-1>", self.drag_start)
        cv.tag_bind("titlebar", "<B1-Motion>", self.drag_move)
        win.bind("<Escape>", lambda e: self.close())
        win.after(50, lambda: (win.lift(), win.focus_force()))

    def frame(self, title):
        cv, W, H = self.cv, self.W, self.H
        pixel_box(cv, 0, 0, W, H, PX_BG, PX_EDGE, b=4)
        cv.create_rectangle(4, 4, W - 4, 40, fill=PX_PANEL, width=0, tags=("titlebar",))
        cv.create_rectangle(4, 40, W - 4, 44, fill=PX_EDGE, width=0)
        pixel_text(cv, 18, 15, title, 2, PX_YELLOW, ("titlebar",))
        random.seed(7)                                       # stelline fisse in alto
        for k in range(16 if self.STARS else 0):
            sx, sy = random.randrange(16, W - 16), random.randrange(52, 164)
            cv.create_rectangle(sx, sy, sx + 2, sy + 2, fill=PX_DIM if k % 3 else PX_YELLOW, width=0)
        random.seed()
        cv.create_rectangle(4, H - self.FOOTER, W - 4, H - self.FOOTER + 4, fill=PX_EDGE, width=0)
        x = W - 34                                           # pulsante ✕
        pixel_box(cv, x - 4, 10, x + 22, 34, PX_PANEL, PX_EDGE, ("close",), b=2)
        pixel_text(cv, x + 4, 15, "X", 2, PX_TEXT, ("close",))
        cv.tag_bind("close", "<ButtonPress-1>", lambda e: self.close())

    def drag_start(self, e):
        self.drag = (e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y())

    def drag_move(self, e):
        dx, dy = self.drag
        self.win.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")

    def close(self):
        self.win.destroy()

    def checkbox(self, x, y, label, var, tag, fg=PX_TEXT, on_change=None, extra_tags=("page",)):
        cv = self.cv
        tag = f"cb_{tag}"
        cv.delete(tag)
        tags = (tag,) + tuple(extra_tags)
        pixel_box(cv, x, y, x + 16, y + 16, PX_PANEL, PX_EDGE, tags, b=2)
        if var.get():                                        # spunta a pixel
            for c0, r0 in ((4, 8), (6, 10), (8, 8), (10, 6), (12, 4)):
                cv.create_rectangle(x + c0 - 1, y + r0 - 1, x + c0 + 2, y + r0 + 2, fill=PX_GREEN,
                                    width=0, tags=tags)
        cv.create_text(x + 26, y + 8, anchor="w", text=label, fill=fg, font=BODY_FONT, tags=tags)

        def toggle(_e):
            var.set(not var.get())
            self.checkbox(x, y, label, var, tag[3:], fg, on_change, extra_tags)
            if on_change:
                on_change()
        cv.tag_bind(tag, "<ButtonPress-1>", toggle)


# ---- impostazioni ---------------------------------------------------------------------------
class Note:
    """Riga di stato in basso (un testo sul canvas, con l'interfaccia di una Label)."""

    def __init__(self, cv, x, y):
        self.cv = cv
        self.id = cv.create_text(x, y, anchor="w", text="", fill=PX_DIM, font=BODY_FONT)

    def config(self, text="", foreground=PX_DIM):
        self.cv.itemconfigure(self.id, text=text, fill=foreground)

    def cget(self, key):
        return self.cv.itemcget(self.id, key)


class SettingsWindow(PixelWindow):
    W, H, STARS = 740, 660, False

    def __init__(self, root, cfg, on_save, on_wizard):
        self.cfg, self.on_save, self.on_wizard = dict(cfg), on_save, on_wizard
        super().__init__(root, T("{app} - Impostazioni").format(app=pc.APP_NAME))
        self.vars = {}
        for s in pc.SETTINGS:
            v = self.cfg[s.key]
            if s.kind == "bool":
                self.vars[s.key] = tk.BooleanVar(value=v)
            elif s.kind == "choice":
                self.vars[s.key] = tk.StringVar(value=dict(s.opts)[v])
            else:
                self.vars[s.key] = tk.StringVar(value=str(v))
        self.autostart = tk.BooleanVar(value=pc.autostart_on())
        self.tabs = pc.TABS + ("Avvio e file",)
        self.tab = self.tabs[0]
        self.widgets, self.buttons = [], []
        self.note = Note(self.cv, 32, self.H - 46)
        save = PixelButton(self.cv, self.W - 32, self.H - 66, T("SALVA"), self.save, primary=True)
        PixelButton(self.cv, self.W - 48 - save.width, self.H - 66, T("ANNULLA"), self.close)
        self.t0 = time.time()
        self.render()
        self.animate()

    def animate(self):                                       # Hoppy con la chiave inglese nella barra
        if not self.win.winfo_exists():
            return
        self.cv.delete("sprite")
        draw_sprite(self.cv, self.W - 96, 13, 3, time.time() - self.t0, self.char, "wrench")
        self.win.after(120, self.animate)

    # --- schede
    def render(self):
        cv = self.cv
        self.char = dict((name, val) for val, name in pc.BY_KEY["character"].opts)[
            self.vars["character"].get()]
        cv.delete("content")
        for w in self.widgets:
            w.destroy()
        for b in self.buttons:
            b.destroy()
        self.widgets, self.buttons = [], []
        x = 24
        for t in self.tabs:                                  # linguette
            name = TAB_NAMES.get(t, t)                       # t resta la chiave, name si mostra
            w = len(name) * 12 + 24
            on = t == self.tab
            pixel_box(cv, x, 56 if on else 60, x + w, 92, PX_OCTO if on else PX_PANEL,
                      PX_EDGE if on else PX_DIM, ("content", f"tab_{t}"), b=2)
            pixel_text(cv, x + 12, 66 if on else 70, name, 2, PX_TEXT if on else PX_DIM,
                       ("content", f"tab_{t}"))
            cv.tag_bind(f"tab_{t}", "<ButtonPress-1>", lambda e, t=t: self.switch(t))
            x += w + 6
        cv.create_rectangle(4, 92, self.W - 4, 95, fill=PX_EDGE, width=0, tags=("content",))
        if self.tab == "Avvio e file":
            self.files_tab()
        else:
            y = 112
            for s in (s for s in pc.SETTINGS if s.tab == self.tab):
                y = self.row(s, y)

    def switch(self, tab):
        self.tab = tab
        self.render()

    def entry(self, var, x1, y, chars):
        e = tk.Entry(self.cv, textvariable=var, width=chars, bg=PX_PANEL, fg=PX_TEXT,
                     insertbackground=PX_YELLOW, relief="flat", font=BODY_FONT, justify="center",
                     highlightthickness=2, highlightbackground=PX_EDGE, highlightcolor=PX_YELLOW)
        self.cv.create_window(x1, y + 8, anchor="e", window=e, tags=("content",))
        self.widgets.append(e)

    def small_box(self, x, y, tag, symbol, cmd):
        """Quadratino cliccabile con un simbolo a pixel: "minus", "plus", "left" o "right"."""
        cv, tags = self.cv, ("content", tag)
        pixel_box(cv, x, y - 1, x + 20, y + 19, PX_PANEL, PX_EDGE, tags, b=2)
        if symbol in ("minus", "plus"):
            cv.create_rectangle(x + 5, y + 8, x + 15, y + 11, fill=PX_TEXT, width=0, tags=tags)
            if symbol == "plus":
                cv.create_rectangle(x + 8, y + 4, x + 12, y + 15, fill=PX_TEXT, width=0, tags=tags)
        else:                                                # triangolino a gradini
            for k in range(4):
                h = 1 + 2 * k if symbol == "left" else 7 - 2 * k
                cv.create_rectangle(x + 6 + 2 * k, y + 8 - h / 2, x + 8 + 2 * k, y + 10 + h / 2,
                                    fill=PX_YELLOW, width=0, tags=tags)
        cv.tag_bind(tag, "<ButtonPress-1>", lambda e: cmd())

    def row(self, s, y):
        cv, R = self.cv, self.W - 40
        sub = s.label.startswith("...")
        x0 = 64 if sub else 40
        label = (s.label[3:] if sub else s.label) + (T("  (al riavvio)") if s.restart else "")
        var = self.vars[s.key]
        if s.kind == "bool":
            self.checkbox(x0, y, label, var, s.key, extra_tags=("content",))
        else:
            cv.create_text(x0, y + 8, anchor="w", text=label, fill=PX_TEXT, font=BODY_FONT,
                           tags=("content",))
        if s.kind == "int":                                  # [-] numero [+]
            def bump(d, var=var):
                try:
                    var.set(str(max(0, int(var.get()) + d)))
                except ValueError:
                    var.set("0")
            self.small_box(R - 20, y, f"plus_{s.key}", "plus", lambda: bump(1))
            self.entry(var, R - 28, y, 6)
            self.small_box(R - 100, y, f"minus_{s.key}", "minus", lambda: bump(-1))
        elif s.kind == "choice":                             # ◀ valore ▶
            names = [o[1] for o in s.opts]

            def cycle(d, var=var, names=names):
                var.set(names[(names.index(var.get()) + d) % len(names)])
                self.render()
            self.small_box(R - 20, y, f"next_{s.key}", "right", lambda: cycle(1))
            cv.create_text(R - 150, y + 8, text=var.get(), fill=PX_YELLOW, font=BODY_FONT,
                           tags=("content",))
            self.small_box(R - 280, y, f"prev_{s.key}", "left", lambda: cycle(-1))
        elif s.kind == "text":
            self.entry(var, R, y, 26)
        y += 26
        if s.help:
            hx = x0 + (26 if s.kind == "bool" else 0)
            t = cv.create_text(hx, y - 6, anchor="nw", text=s.help, fill=PX_DIM, font=HELP_FONT,
                               width=self.W - hx - 40, tags=("content",))
            y = cv.bbox(t)[3] + 8
        return y

    def files_tab(self):
        cv = self.cv
        self.checkbox(40, 114, T("Avvia Hoppy con Windows"), self.autostart,
                      "autostart", PX_YELLOW, extra_tags=("content",))
        cv.create_text(40, 154, anchor="w", text=T("Apri:"), fill=PX_DIM, font=BODY_FONT, tags=("content",))
        items = ((T("CARTELLA DATI"), lambda: open_file(pc.DATA_DIR)),
                 ("CONFIG.JSON", self.open_config),
                 (T("COMANDI RAPIDI"), self.open_commands),
                 (T("MEMORIA"), lambda: open_file(pc.DATA_DIR / "pet_memory.json")),
                 (T("PROPOSTE"), lambda: open_file(pc.DATA_DIR / "pet_proposals.md")),
                 (T("ISTRUZIONI"), lambda: open_file(pc.README_URL)))
        for k, (label, cmd) in enumerate(items):
            x0, y = (40, 172 + (k % 3) * 50) if k < 3 else (330, 172 + (k % 3) * 50)
            self.buttons.append(PixelButton(cv, x0 + PixelButton.width_of(label), y, label, cmd))
        cv.create_text(40, 340, anchor="w", text=T("Se modifichi config.json a mano, poi premi RICARICA."),
                       fill=PX_DIM, font=BODY_FONT, tags=("content",))
        for x0, label, cmd in ((40, T("RICARICA"), self.reload), (220, T("RIVEDI LA PRESENTAZIONE"), self.wizard)):
            self.buttons.append(PixelButton(cv, x0 + PixelButton.width_of(label), 358, label, cmd))
        cv.create_text(40, 440, anchor="w", text=T("Versione {version}  ·  dati in {path}").format(
                           version=__version__, path=pc.DATA_DIR), fill=PX_DIM,
                       font=HELP_FONT, tags=("content",))

    # --- azioni
    def open_config(self):
        if not pc.CONFIG_PATH.exists():
            pc.save(self.cfg)
        open_file(pc.CONFIG_PATH)

    def open_commands(self):
        path = pc.DATA_DIR / "pet_commands.json"
        if not path.exists():
            pc.DATA_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(COMMANDS_EXAMPLE, ensure_ascii=False, indent=2), encoding="utf-8")
        open_file(path)

    def reload(self):
        new = pc.load()
        new["wizard_done"] = self.cfg.get("wizard_done", True)
        self.on_save(new)
        self.win.destroy()

    def wizard(self):
        self.win.destroy()
        self.on_wizard()

    def collect(self):
        out = dict(self.cfg)
        for s in pc.SETTINGS:
            raw = self.vars[s.key].get()
            if s.kind == "int":
                try:
                    raw = int(str(raw).strip())
                except ValueError:
                    raise ValueError(s.label.lstrip(".")) from None
            elif s.kind == "choice":
                raw = {name: val for val, name in s.opts}[raw]
            elif s.kind == "text":
                raw = raw.strip()
            out[s.key] = raw
        return out

    def save(self):
        try:
            new = self.collect()
        except ValueError as e:
            self.note.config(text=T("Serve un numero in «{name}»").format(name=e), foreground=PX_RED)
            return
        if self.autostart.get() != pc.autostart_on():
            pc.set_autostart(self.autostart.get())
        self.on_save(new)
        self.win.destroy()


# ---- wizard della prima volta ---------------------------------------------------------------
class Wizard(PixelWindow):
    W, H = 660, 600

    def __init__(self, root, cfg, on_done):
        self.cfg, self.on_done = dict(cfg), on_done
        self.character = self.cfg.get("character", "octopus")
        super().__init__(root, pc.APP_NAME)
        cv = self.cv
        self.win.bind("<Return>", lambda e: "disabled" not in self.next_btn.state() and self.next())
        self.next_btn = PixelButton(cv, self.W - 32, self.H - 66, T("AVANTI"), self.next, primary=True)
        self.back_btn = PixelButton(cv, self.W - 48 - self.next_btn.width, self.H - 66,
                                    T("INDIETRO"), self.back)
        self.ok = tk.BooleanVar(value=bool(cfg.get("wizard_done")))
        self.picks = {k: tk.BooleanVar(value=self.cfg[k]) for k in CHOICES}
        self.autostart = tk.BooleanVar(value=pc.autostart_on())
        self.page = 0
        self.t0 = time.time()
        self.show()
        self.animate()

    def animate(self):                                       # chiuso a metà: ricompare al prossimo avvio
        if not self.win.winfo_exists():
            return
        self.cv.delete("sprite")
        draw_sprite(self.cv, 46, 92, 9, time.time() - self.t0, self.character,
                    ACCESSORY[min(self.page, len(ACCESSORY) - 1)])
        self.win.after(90, self.animate)

    def n_pages(self):
        return len(PAGES) + 2

    def show(self):
        cv = self.cv
        cv.delete("page")
        i = self.page
        pixel_text(cv, 172, 88, TITLES[i], 3, PX_YELLOW, ("page",))
        if i < len(PAGES):
            cv.create_text(40, 180, anchor="nw", text=PAGES[i][1].replace("•", "▪"), fill=PX_TEXT,
                           font=BODY_FONT, width=self.W - 80, tags=("page",))
            if i == 1:
                self.checkbox(40, self.H - 132, T("Ho capito: è un progetto hobbistico e lo uso a mio rischio"),
                              self.ok, "accept", PX_YELLOW, self.update_buttons)
        elif i == len(PAGES):
            self.choices_page()
        else:
            self.last_page()
        for k in range(self.n_pages()):                      # avanzamento: quadratini
            x = 32 + k * 20
            col = PX_YELLOW if k == i else (PX_OCTO if k < i else PX_PANEL)
            cv.create_rectangle(x, self.H - 52, x + 12, self.H - 40, fill=col, outline=PX_EDGE,
                                width=1, tags=("page",))
        self.update_buttons()

    def choices_page(self):
        self.cv.create_text(40, 172, anchor="nw", width=self.W - 80, font=BODY_FONT, fill=PX_DIM,
                            tags=("page",), text=T("Quelle che toccano i tuoi file partono spente."))
        y = 198
        for k in CHOICES:
            self.checkbox(40, y, pc.BY_KEY[k].label, self.picks[k], k)
            y += 21
        self.checkbox(40, y + 6, T("Avvia Hoppy con Windows"), self.autostart, "autostart",
                      PX_YELLOW)

    def last_page(self):
        ok = shutil.which("claude") or (pc.Path.home() / ".local/bin/claude.exe").exists()
        text = T("Tasto destro su di me: il menu, con Impostazioni in fondo.\n"
                 "Doppio clic: parliamo.\n\n")
        text += (T("Ho trovato Claude Code: possiamo cominciare.") if ok else
                 T("Attenzione: non trovo Claude Code (il comando claude). Installalo e fai il "
                   "login, altrimenti non posso rispondere alle domande."))
        self.cv.create_text(40, 180, anchor="nw", text=text, width=self.W - 80, font=BODY_FONT,
                            fill=PX_TEXT if ok else PX_RED, tags=("page",))

    def update_buttons(self):
        self.back_btn.state(["!disabled"] if self.page else ["disabled"])
        last = self.page == self.n_pages() - 1
        self.next_btn.config(text=T("FINE") if last else T("AVANTI"))
        self.next_btn.state(["disabled"] if self.page == 1 and not self.ok.get() else ["!disabled"])
        self.back_btn.x1 = self.next_btn.x1 - self.next_btn.width - 16   # sempre accanto
        self.back_btn.draw()

    def back(self):
        self.page = max(0, self.page - 1)
        self.show()

    def next(self):
        if self.page < self.n_pages() - 1:
            self.page += 1
            return self.show()
        for k, var in self.picks.items():
            self.cfg[k] = var.get()
        self.cfg["wizard_done"] = True
        if self.autostart.get() != pc.autostart_on():
            pc.set_autostart(self.autostart.get())
        self.on_done(self.cfg)
        self.win.destroy()
