"""Come Hoppy lancia claude: claude.cmd di npm senza cmd.exe, profilo scelto (cartella e blocco
"env" di settings.json), errore vero in errors.log e motivo comprensibile nel fumetto."""
import json
import pathlib
import shutil
import tempfile
import _setup  # noqa: F401
from hoppy import cli, config, pet

ok = []
def check(name, cond):
    ok.append(bool(cond)); print(("OK  " if cond else "ERR ") + name)

T = pathlib.Path(tempfile.mkdtemp())

# --- claude.cmd di npm: si lancia quello che lancerebbe
npm = T / "npm"
(npm / "node_modules/@anthropic-ai/claude-code/bin").mkdir(parents=True)
(npm / "node_modules/@anthropic-ai/claude-code/bin/claude.exe").write_bytes(b"")
(npm / "claude.cmd").write_text('@ECHO off\r\n"%dp0%\\node_modules\\@anthropic-ai\\claude-code\\bin\\claude.exe"   %*\r\n')
check("claude.cmd → claude.exe del pacchetto",
      cli._npm_target(npm / "claude.cmd") == [str(npm / "node_modules/@anthropic-ai/claude-code/bin/claude.exe")])
(npm / "node_modules/@anthropic-ai/claude-code/cli.js").write_text("")
(npm / "node.exe").write_bytes(b"")
(npm / "old.cmd").write_text('"%_prog%"  "%dp0%\\node_modules\\@anthropic-ai\\claude-code\\cli.js" %*\r\n')
check("claude.cmd vecchio → node + cli.js",
      cli._npm_target(npm / "old.cmd") == [str(npm / "node.exe"), str(npm / "node_modules/@anthropic-ai/claude-code/cli.js")])
real_which, real_home = shutil.which, pathlib.Path.home
shutil.which = lambda n: str(npm / "claude.cmd") if n == "claude" else real_which(n)
pathlib.Path.home = classmethod(lambda c: T)          # niente ~/.local/bin/claude.exe
check("command() non passa da cmd.exe", cli.command()[0].endswith("claude.exe"))
shutil.which, pathlib.Path.home = real_which, real_home

# --- profilo
cfg = config.load()
check("di default il profilo personale", cfg["ask_profile"] == "personal")
work = T / "work"
work.mkdir()
(work / "settings.json").write_text(json.dumps({"env": {"CLAUDE_CODE_USE_BEDROCK": "1", "X_NUM": 3,
                                                        "X_BOOL": True}, "hooks": {"a": 1}}))
cfg.update(ask_profile="work", work_home=str(work))
e = cli.env(cfg)
check("secondo profilo: CLAUDE_CONFIG_DIR", e.get("CLAUDE_CONFIG_DIR") == str(work))
check("secondo profilo: blocco env di settings.json",
      e.get("CLAUDE_CODE_USE_BEDROCK") == "1" and e.get("X_NUM") == "3" and "X_BOOL" not in e)
check("personale: niente CLAUDE_CONFIG_DIR verso un'altra cartella",
      cli.env(dict(cfg, ask_profile="personal")).get("CLAUDE_CONFIG_DIR") in (None, *[
          v for k, v in cli._user_env(names=("CLAUDE_CONFIG_DIR",)).items()]))

# --- motivi comprensibili
check("login", "login" in cli.friendly("Not logged in · Please run /login"))
check("credito", "credito" in cli.friendly("Credit balance is too low"))
check("tempo", "tempo" in cli.friendly("Command timed out after 90 seconds"))
check("altro: rimanda a errors.log", "errors.log" in cli.friendly("boh"))

# --- chiamata vera con un profilo senza login: errore annotato e motivo giusto
empty = T / "empty"
empty.mkdir()
config.save(dict(config.load(), ask_profile="work", work_home=str(empty)))
if cli.command():
    text, err = pet.ask_claude("ciao", "Rispondi in una parola.", timeout=60)
    log = (config.DATA_DIR / "errors.log").read_text(encoding="utf-8") if (config.DATA_DIR / "errors.log").exists() else ""
    check("profilo senza login: errore" + (f" ({err})" if err else ""), text is None and err)
    check("errore in errors.log", "[mascotte]" in log)
    check("fumetto: " + cli.friendly(err), "login" in cli.friendly(err))
else:
    print("~~ claude non installato: salto la chiamata vera")
print("TUTTO OK" if all(ok) else "FALLITO")
