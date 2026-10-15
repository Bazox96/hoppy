"""Lancia tutti i test (ognuno nel suo processo) e riassume. Uscita 1 se qualcosa fallisce.

Ogni test stampa una riga per controllo: "OK ..." se passa, "NO ..."/"ERR ..." se no;
"~~ ..." è solo informativo (controlli che dipendono dai tempi della macchina)."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
env = dict(os.environ, PYTHONIOENCODING="utf-8")   # «», →: anche da una console cp1252
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
failed = []
for test in sorted(here.glob("test_*.py")):
    r = subprocess.run([sys.executable, str(test)], cwd=here, capture_output=True, text=True, env=env,
                       encoding="utf-8", errors="replace", timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    bad = [line for line in out.splitlines()
           if line.startswith(("NO ", "ERR ", "FALLITO", "Traceback", "AssertionError"))]
    oks = sum(1 for line in out.splitlines() if line.startswith("OK "))
    status = "OK" if r.returncode == 0 and not bad else "FALLITO"
    print(f"{status:8} {test.name}  ({oks} controlli ok)")
    if status != "OK":
        failed.append(test.name)
        print("\n".join("    " + line for line in (bad or out.splitlines()[-15:])))
print("\nTutti i test passano." if not failed else f"\nFalliti: {', '.join(failed)}")
sys.exit(1 if failed else 0)
