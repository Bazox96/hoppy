"""Comune a tutti i test: il pacchetto dal repo, dati/config/collegamenti in una cartella
temporanea, finestre della mascotte nascoste, microfono e schermo intero simulati."""
import ctypes
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from hoppy import config  # noqa: E402

TMP = pathlib.Path(tempfile.mkdtemp())
config.DATA_DIR, config.CONFIG_PATH, config.STARTUP_DIR = TMP, TMP / "config.json", TMP / "startup"

from hoppy import pet, watch  # noqa: E402  (dopo: i percorsi dei dati partono da DATA_DIR)

_init = pet.Monitor.__init__


def _hidden_init(self, *a, **k):
    _init(self, *a, **k)
    self.win.withdraw()                      # niente sullo schermo di chi lancia i test


pet.Monitor.__init__ = _hidden_init
watch.mic_users = lambda: []                 # una call vera non deve cambiare i risultati
watch.fullscreen_state = lambda: 1
pet.STANDUP_HOUR = 99                        # niente standup automatico in mezzo ai test
