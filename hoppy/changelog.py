"""Novità di ogni versione: la mascotte le mostra sulla lavagna la prima volta che parte dopo
un aggiornamento. Ogni release aggiunge qui la sua voce in cima (lo controlla un test)."""
from . import __version__

CHANGES = (
    ("0.1.3", ("**Spiegami lo schermo**: dal menu, o scrivendo in chat «cosa succede?», Hoppy "
               "fotografa la finestra su cui stavi lavorando e Claude ti spiega cosa vede.",
               "Dopo ogni aggiornamento Hoppy ti racconta le novità sulla lavagna.")),
    ("0.1.2", ("**Cerca aggiornamenti**: dal menu, o scrivendo in chat «aggiornati».",)),
    ("0.1.1", ("Apre le skill di Claude Code dalla chat («apri /nome-skill»).",
               "Avvia da sola popup e inline; un solo collegamento di avvio automatico.",
               "Si aggiorna da sola quando esce una versione nuova.")),
    ("0.1.0", ("Prima versione.",)),
)


def _tuple(v):
    return tuple(int(x) for x in v.split("."))


def since(old, new=__version__):
    """Voci delle versioni dopo old fino a new comprese, dalla più recente."""
    return [(v, items) for v, items in CHANGES if _tuple(old) < _tuple(v) <= _tuple(new)]


def to_show(seen, updated):
    """Cosa raccontare all'avvio: le novità dopo l'ultima versione vista. Chi arriva da una
    versione che non la segnava (fino alla 0.1.2) vede solo quelle dell'ultima; chi installa
    da zero niente."""
    if seen:
        return since(seen)
    return list(CHANGES[:1]) if updated else []


def text(entries):
    """Testo per la lavagna (**grassetto** come gesso calcato)."""
    return "\n\n".join(f"**Versione {v}**\n" + "\n".join("- " + i for i in items)
                       for v, items in entries)
