"""Novità dopo un aggiornamento: quali versioni raccontare e il testo per la lavagna."""
import _setup  # noqa: F401
from hoppy import __version__
from hoppy import changelog as ch

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

check("la versione attuale ha le sue novità in cima", ch.CHANGES[0][0] == __version__)
check("in ordine dalla più recente", [v for v, _ in ch.CHANGES]
      == sorted((v for v, _ in ch.CHANGES), key=ch._tuple, reverse=True))
check("da 0.1.1 a 0.1.3: due versioni", [v for v, _ in ch.since("0.1.1", "0.1.3")] == ["0.1.3", "0.1.2"])
check("stessa versione: niente", ch.since("0.1.3", "0.1.3") == [])
check("versione vista più nuova: niente", ch.since("9.0.0", "0.1.3") == [])
check("installata da zero: niente", ch.to_show(None, False) == [])
check("aggiornata da una versione che non la segnava: solo l'ultima",
      [v for v, _ in ch.to_show(None, True)] == [__version__])
check("già vista: niente", ch.to_show(__version__, True) == [])
t = ch.text(ch.since("0.1.1", "0.1.3"))
check("testo: titoli e punti", t.startswith("**Versione 0.1.3**\n- ") and "**Versione 0.1.2**" in t)
check("grassetti chiusi", all(items and "".join(items).count("**") % 2 == 0 for _, items in ch.CHANGES))
print("TUTTO OK" if all(ok) else "FALLITO")
