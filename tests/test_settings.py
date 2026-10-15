"""Impostazioni e wizard: senza mostrare finestre, dati e avvio automatico in cartelle temporanee."""
import time, tkinter as tk, pathlib, tempfile, json
import _setup  # noqa: F401
from hoppy import config as pc
tmp = pathlib.Path(tempfile.mkdtemp())
pc.DATA_DIR, pc.CONFIG_PATH, pc.STARTUP_DIR = tmp / "data", tmp / "data" / "config.json", tmp / "startup"
pc.set_autostart = lambda on: (_ for _ in ()).throw(AssertionError("autostart toccato"))
class HiddenTop(tk.Toplevel):                # ogni finestra del test resta nascosta
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.withdraw()
    def lift(self, *a): pass
    def focus_force(self): pass
tk.Toplevel = HiddenTop
from hoppy import settings as ps
from hoppy import pet as cp
from hoppy import knowledge as pk
cp.PET_PORT = 48798
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: []; cp.pet_watch.fullscreen_state = lambda: 1
cp.ask_claude = lambda *a, **k: ("x", None)
cp.STANDUP_HOUR = 99

res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("OK  " if cond else "NO  ") + name, extra)

# --- config: default, salvataggio, valori sbagliati
cfg = pc.load()
check("senza config.json: default e wizard da fare", cfg["sleep_s"] == 45 and not cfg["wizard_done"] and not cfg["dev"])
cfg.update(sleep_s=99, dev=True)
pc.save(cfg)
check("salva e rilegge", pc.load()["sleep_s"] == 99 and pc.load()["dev"] is True)
pc.CONFIG_PATH.write_text(json.dumps({"sleep_s": "tanto", "power": "volare", "ram": 3, "boh": 1, "cape": False}), encoding="utf-8")
c2 = pc.load()
check("valori sbagliati -> default, giusti tenuti", c2["sleep_s"] == 45 and c2["power"] == "random" and c2["ram"] is True and c2["cape"] is False and "boh" not in c2)
pc.CONFIG_PATH.write_text("{rotto", encoding="utf-8")
check("config.json rotto -> default", pc.load()["sleep_s"] == 45)
pc.CONFIG_PATH.write_text(json.dumps({"power": "ironman", "portal": "portal", "lecture": "angela"}), encoding="utf-8")
c3 = pc.load()
check("valori delle versioni vecchie convertiti", (c3["power"], c3["portal"], c3["lecture"]) == ("rockets", "ovals", "presenter"))

# --- apply nelle costanti
cfg = pc.defaults(); cfg.update(sleep_s=12, work=True, work_home="~/.prova", recent_days=3, wait_s=7, lecture="presenter")
cp.apply_config(cfg)
check("apply: costanti dei moduli", cp.SLEEP_S == 12 and pk.WORK_ENABLED and pk.WORK_HOME == pathlib.Path.home() / ".prova"
      and cp.pet_chores.RECENT_DAYS == 3 and cp.pet_watch.WAIT_S == 7 and cp.LECTURE == "presenter" and not cp.FEAT_DEV)
check("secondo profilo nelle radici dei progetti", pk.project_roots()[-1] == pathlib.Path.home() / ".prova" / "projects")
cp.apply_config(pc.defaults())
check("senza secondo profilo: una radice sola", len(pk.project_roots()) == 1 and len(pk.Knowledge().roots) == 1)

# --- finestre
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()                         # niente sul tuo schermo
pet.next_spontaneous = pet.next_chore = pet.next_dev_scan = time.time() + 99999
restarts = []
pc.restart_pet = lambda env: restarts.append(1)
destroyed = []
pet.root.after = (lambda f: lambda ms, fn=None, *a: destroyed.append(ms) if fn == root.destroy else f(ms, fn, *a))(root.after)

def run():
    pc.save(pc.defaults())
    saved = []
    w = ps.SettingsWindow(root, pc.load(), saved.append, lambda: None)
    w.vars["sleep_s"].set("abc")
    w.save()
    check("numero sbagliato: non salva e lo dice", not saved and "Serve un numero" in w.note.cget("text"))
    w.vars["sleep_s"].set("60"); w.vars["power"].set("Razzi"); w.vars["errors"].set(False); w.vars["work_label"].set("  ufficio ")
    w.save()
    n = saved[0] if saved else {}
    check("salva: tipi giusti", n.get("sleep_s") == 60 and n.get("power") == "rockets" and n.get("errors") is False and n.get("work_label") == "ufficio")

    done = []
    wz = ps.Wizard(root, pc.load(), done.append)
    wz.next_btn.on_press(None)                # il clic vero sul pulsante AVANTI
    t_end = time.time() + 0.5
    while time.time() < t_end:
        root.update(); time.sleep(0.02)
    check("clic su AVANTI: cambia pagina", wz.page == 1)
    wz.page = 0; wz.show()
    wz.next()
    check("wizard: «Avanti» bloccato finché non accetti", "disabled" in wz.next_btn.state())
    wz.ok.set(True); wz.update_buttons()
    for _ in range(3):
        wz.next()
    check("wizard: pagina delle scelte, le pulizie partono spente", wz.page == 4 and not wz.picks["dev"].get() and not wz.picks["desktop"].get())
    wz.picks["standup"].set(True)
    wz.next(); wz.next()
    check("wizard finito: scelte e wizard_done", done and done[0]["standup"] and done[0]["wizard_done"])

    cfg = pc.load(); cfg.update(meeting=False, cape=False, ram=False)
    pet.on_settings_saved(cfg)
    check("mascotte: applica subito", not cp.MEETING_MODE and not pet.cape_on and not cp.FEAT_RAM and not restarts
          and pc.load()["meeting"] is False and "salvate" in pet.bubble["full"])
    pet.toggle_meeting_mode(None)
    check("menu «Zitta in riunione» scrive config.json", cp.MEETING_MODE and pc.load()["meeting"] is True)
    cfg = pc.load(); cfg.update(work=True)
    pet.on_settings_saved(cfg)
    check("profilo di lavoro cambiato: si riavvia", restarts and destroyed)
    pet.open_settings()
    check("menu Impostazioni apre la finestra", pet.settings_win is not None and pet.settings_win.win.winfo_exists())
    print("TUTTO OK" if all(res) else "FALLITO")
    root.destroy()
root.after(800, run)
root.mainloop()
