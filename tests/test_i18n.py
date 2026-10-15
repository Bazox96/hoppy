"""Traduzioni: ogni T("...") del codice ha la sua voce in en.py, con gli stessi segnaposto,
e T() riceve sempre un testo fisso (non un f-string, che non si può tradurre).
Lanciato a mano con dei file come argomenti, elenca anche le stringhe italiane rimaste fuori."""
import ast, os, pathlib, re, runpy, string, sys
import _setup  # noqa: F401
from hoppy.en import EN
from hoppy import i18n

if os.environ.get("HOPPY_EN_FILE"):          # traduzioni ancora fuori da en.py (mentre si lavora)
    EN = {**EN, **runpy.run_path(os.environ["HOPPY_EN_FILE"])["EN"]}

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

PKG = pathlib.Path(__file__).resolve().parents[1] / "hoppy"
FILES = [PKG / f for f in sys.argv[1:]] or sorted(PKG.glob("*.py"))
ITALIAN = re.compile(r"[àèéìòù]|\b(il|che|non|della|sono|per|una|con|gli|anche|questo|ancora)\b", re.I)


def fields(s):
    return sorted(f for _, f, _, _ in string.Formatter().parse(s) if f is not None)


keys, bad, leftovers = set(), [], []
for path in FILES:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    in_t, docs = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "T":
            a = n.args[0] if n.args else None
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                keys.add(a.value)
                in_t.add(id(a))
            else:
                bad.append(f"{path.name}:{n.lineno}")
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            docs.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if (isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in in_t
                and id(n) not in docs and ITALIAN.search(n.value)):
            leftovers.append(f"{path.name}:{n.lineno}: {n.value[:70]!r}")

missing = sorted(k for k in keys if k not in EN)
check("T() riceve sempre un testo fisso" + (": " + ", ".join(bad) if bad else ""), not bad)
check(f"ogni testo ha la traduzione ({len(missing)} mancanti)", not missing)
for k in missing[:30]:
    print("    manca:", repr(k[:90]))
wrong = [k for k in keys & EN.keys() if fields(k) != fields(EN[k])]
check("stessi segnaposto {..} in italiano e inglese", not wrong)
for k in wrong[:10]:
    print("    segnaposto diversi:", repr(k[:90]))
i18n.LANG = "en"
check("in inglese T() traduce", not EN or i18n.T(next(iter(EN))) == EN[next(iter(EN))])
i18n.LANG = "it"
check("in italiano T() lascia il testo com'è", i18n.T("Ciao") == "Ciao")
if sys.argv[1:]:                             # a mano: cosa resta da guardare
    print(f"\nStringhe con parole italiane fuori da T() ({len(leftovers)}), da controllare:")
    print("\n".join(leftovers))
print("TUTTO OK" if all(ok) else "FALLITO")
