"""Spiegami lo schermo: foto di una finestra in PNG e domanda a Claude con l'immagine
(finestra di prova fuori dallo schermo, claude finto: non manda niente)."""
import base64, ctypes, json, struct, subprocess, time, tkinter as tk
import _setup  # noqa: F401
from hoppy import pet as cp
from hoppy import screen

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

ctypes.windll.shcore.SetProcessDpiAwareness(2)
root = tk.Tk()
root.geometry("400x200-4000-4000")            # fuori dallo schermo: non si vede
tk.Label(root, text="Errore 404", bg="white").pack(expand=True, fill="both")
root.update(); time.sleep(0.3); root.update()
shot = screen.capture(ctypes.windll.user32.GetParent(root.winfo_id()))
root.destroy()
check("foto: è un PNG", shot and shot.startswith(b"\x89PNG\r\n\x1a\n"))
w, h = struct.unpack(">II", shot[16:24])
check("foto: misure della finestra", 300 <= w <= 500 and 150 <= h <= 300)
check("niente finestra: niente foto", screen.capture(None) is None and screen.capture(12345) is None)
big = screen.png(4, 2, bytes(range(32)))
check("png: intestazione 4x2", struct.unpack(">II", big[16:24]) == (4, 2))

sent = {}
def fake_run(cmd, input, **k):
    sent.update(cmd=cmd, input=input)
    out = '{"type":"system"}\n{"type":"result","result":"Vedo un errore 404.","total_cost_usd":0.001}\n'
    return subprocess.CompletedProcess(cmd, 0, out, "")
cp.shutil.which = lambda name: __file__       # un file che esiste, al posto di claude
cp.subprocess.run = fake_run
text, err = cp.ask_claude("Cosa succede?", "sistema", image=shot)
check("risposta letta dall'ultima riga", (text, err) == ("Vedo un errore 404.", None))
cmd = sent["cmd"]
check("comando in stream-json", cmd[cmd.index("--input-format") + 1] == "stream-json"
      and cmd[cmd.index("--output-format") + 1] == "stream-json" and "--verbose" in cmd)
msg = json.loads(sent["input"])["message"]["content"]
check("immagine e domanda nel messaggio",
      base64.b64decode(msg[0]["source"]["data"]) == shot and msg[1]["text"] == "Cosa succede?")
cp.subprocess.run = lambda cmd, input, **k: subprocess.CompletedProcess(
    cmd, 0, '{"result":"Ciao","total_cost_usd":0}', "")
check("senza immagine: come prima", cp.ask_claude("ciao", "s") == ("Ciao", None))
print("TUTTO OK" if all(ok) else "FALLITO")
