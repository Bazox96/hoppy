"""hoppy avvia popup e inline; una sola copia per programma; un solo collegamento di avvio
(cartella Esecuzione automatica finta, Popen finto: non avvia e non crea niente di vero)."""
import pathlib, tempfile
import _setup  # noqa: F401
from hoppy import config as pc

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

check("prima copia: parte", pc.mark_running("hoppy.test-unica"))
check("seconda copia dello stesso programma: esce", not pc.mark_running("hoppy.test-unica"))
check("resta segnato come in esecuzione", pc.is_running("hoppy.test-unica"))

started = []
pc.subprocess.Popen = lambda cmd, **k: started.append(cmd)
pc.is_running = lambda m: m == "hoppy.popup"          # il popup gira già
pc.start_companions({})
check("avvia solo l'inline (il popup gira già)", [c[-1] for c in started] == ["hoppy.inline"])

tmp = pathlib.Path(tempfile.mkdtemp())
pc.STARTUP_DIR = tmp
for name in ("Hoppy", "Hoppy Popup", "Hoppy Inline"):     # come li lasciava la 0.1.0
    (tmp / f"{name}.lnk").write_text("")
check("avvio automatico: conta il collegamento della mascotte", pc.autostart_on())
pc.drop_old_shortcuts()
check("all'avvio spariscono i vecchi collegamenti di popup e inline",
      sorted(p.name for p in tmp.iterdir()) == ["Hoppy.lnk"])
pc.set_autostart(False)
check("avvio automatico spento: nessun collegamento", not any(tmp.iterdir()) and not pc.autostart_on())
check("un solo collegamento da creare", [n for n, _ in pc.PROGRAMS[:1]] == ["Hoppy"])
check("impostazione accesa di default", pc.defaults()["companions"] is True)
print("TUTTO OK" if all(ok) else "FALLITO")
