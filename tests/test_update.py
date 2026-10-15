"""Aggiornamenti: versione su GitHub (finta), domanda nel fumetto, segnali e processo di installazione
(pip e riavvii finti: non installa niente). Nota: accende l'evento Local\\HoppyQuit di questa sessione."""
import io, json, subprocess, time, tkinter as tk, pathlib, tempfile, urllib.error
import _setup  # noqa: F401
from hoppy import pet as cp
from hoppy import update as up
from hoppy import config as pc

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

# ---- versioni e risposta di GitHub ------------------------------------------------
up.__version__ = "0.1.0"
check("0.2.0 è più nuova", up.is_newer("v0.2.0") and up.is_newer("0.1.1"))
check("0.1.0 e 0.0.9 no", not up.is_newer("v0.1.0") and not up.is_newer("v0.0.9"))
check("10 > 9 (non in ordine alfabetico)", up.version_tuple("v0.10.0") > up.version_tuple("v0.9.0"))

def fake_urlopen(body=None, error=None):
    def f(req, timeout):
        if error:
            raise error
        return io.BytesIO(json.dumps(body).encode())
    return f
up.urllib.request.urlopen = fake_urlopen({"tag_name": "v0.2.0"})
check("latest: legge il tag", up.latest() == "v0.2.0")
up.urllib.request.urlopen = fake_urlopen({"tag_name": "rm -rf"})
check("latest: tag strano -> None", up.latest() is None)
up.urllib.request.urlopen = fake_urlopen(error=urllib.error.HTTPError("u", 404, "Not Found", {}, None))
check("latest: repo privato (404) -> None", up.latest() is None)
up.urllib.request.urlopen = fake_urlopen(error=OSError("offline"))
check("latest: niente rete -> None", up.latest() is None)
check("dai sorgenti non risulta installata", not up.installed())

# ---- segnali fra i programmi --------------------------------------------------------
check("modulo finto non gira", not pc.is_running("hoppy.test-nessuno"))
pc.mark_running("hoppy.test-io")
check("mark_running -> is_running", pc.is_running("hoppy.test-io"))
h = pc.quit_event()
check("segnale di uscita spento all'inizio", not pc.quit_requested(h))
pc.request_quit()
check("request_quit -> popup e inline lo vedono", pc.quit_requested(h))

# ---- il processo di aggiornamento (pip e riavvii finti) -------------------------------
tmp = pathlib.Path(tempfile.mkdtemp())
pc.DATA_DIR = tmp
up.RESULT_PATH, up.LOG_PATH = tmp / "update.json", tmp / "update.log"
calls, started = [], []
up.pet_config.wait_for_exit = lambda pid: calls.append(("wait", pid))
up.pet_config.is_running = lambda m: False
class R:
    returncode, stdout, stderr = 0, "Successfully installed hoppy-0.2.0", ""
up.subprocess.run = lambda cmd, **k: (calls.append(cmd), R)[1]
up.subprocess.Popen = lambda cmd, **k: started.append(cmd)
up.run("v0.2.0", 1234, ["hoppy.pet", "hoppy.inline"])
pip = [c for c in calls if isinstance(c, list)]
check("aspetta che la mascotte esca", calls[0] == ("wait", 1234))
check("pip installa lo zip della release",
      pip and pip[0][1:4] == ["-m", "pip", "install"] and pip[0][-1].endswith("/tags/v0.2.0.zip"))
check("riavvia chi girava", [c[-1] for c in started] == ["hoppy.pet", "hoppy.inline"])
res = up.take_result()
check("esito salvato e letto una volta", res == {"tag": "v0.2.0", "ok": True} and up.take_result() is None)
R.returncode = 1
calls.clear(); started.clear()
up.time.sleep = lambda s: None
up.run("v0.2.0", 1, ["hoppy.pet"])
check("pip fallisce: 3 tentativi, riavvia la versione vecchia, esito ko",
      len([c for c in calls if isinstance(c, list)]) == 3 and len(started) == 1
      and up.take_result()["ok"] is False and up.LOG_PATH.exists())

# ---- la mascotte: domanda, no, sì ---------------------------------------------------
cp.PET_PORT = 48794
cp.MEM_PATH, cp.PROPOSALS_PATH, cp.SESSIONS_PATH, cp.CHORES_PATH = tmp / "m", tmp / "p", tmp / "s", tmp / "c"
cp.known_folder = lambda n: tmp
cp.active_app = lambda pid: ""
cp.window_rects = lambda pid: []
cp.cursor_pos = lambda: (700, 600)
cp.pet_watch.mic_users = lambda: []
cp.ask_claude = lambda *a, **k: ("x", None)
cp.STANDUP_HOUR = 99
cp.FEAT_UPDATES = False                          # niente controlli veri durante il test
up.installed = lambda: True
launched = []
up.start = lambda tag, mods, env: launched.append((tag, mods))
quits = []
pc.request_quit = lambda: quits.append(1)
pc.is_running = lambda m: m == "hoppy.popup"
root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)
for m in pet.mons:
    m.win.withdraw()
pet.next_spontaneous = time.time() + 9999
destroyed = []

def run():
    now = time.time()
    pet.bubble = None
    pet.offer_update(now, "v0.1.0")
    check("stessa versione: zitta", pet.bubble is None)
    pet.set_state("idle", now)                   # finestre nascoste: altrimenti "cade" e non è tranquilla
    pet.offer_update(now, "v0.2.0")
    b = pet.bubble
    check("versione nuova: chiede col sì/no", b and b["thumbs"] and b.get("update") == "v0.2.0")
    pet.on_thumb(False)
    check("no: se lo segna", pet.brain.data.get("update_skip") == "v0.2.0" and not launched)
    pet.bubble = None
    pet.offer_update(now, "v0.2.0")
    check("no: non richiede la stessa versione", pet.bubble is None)
    pet.bubble = {"kind": "chat", "full": "altro", "shown": 0, "thumbs": False, "cat": None,
                  "t0": now, "done_t": None}
    pet.offer_update(now, "v0.3.0")
    check("occupata: riprova fra un'ora", pet.bubble["full"] == "altro" and pet.next_update > now + 3000)
    pet.bubble = None
    pet.offer_update(now, "v0.3.0")
    root.destroy_real, root.destroy = root.destroy, lambda: destroyed.append(1)
    pet.on_thumb(True)
    check("sì: parte l'aggiornamento con mascotte e popup",
          launched == [("v0.3.0", ["hoppy.pet", "hoppy.popup"])] and quits == [1])
    root.after(2000, finish)

def finish():
    check("sì: la mascotte si chiude", destroyed == [1])
    print("TUTTO OK" if all(ok) else "FALLITO")
    root.destroy_real()

root.after(1000, run)
root.after(30000, lambda: root.destroy_real() if hasattr(root, "destroy_real") else root.destroy())
root.mainloop()
