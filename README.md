# Hoppy

*English · [Italiano](README.it.md)*

Hoppy is a pixel-art little octopus that lives on your Windows desktop and brings
[Claude Code](https://claude.com/claude-code) one click away: you can chat with it, it
explains what you are reading, it tells you when a Claude Code session is done and, if
you want, it helps you keep your desktop and disk tidy.

> **Unofficial hobby project.** Hoppy is not an Anthropic product and is not affiliated
> with Anthropic. It is made for fun, may contain bugs and comes with no warranty (see
> [LICENSE](LICENSE)). Use it at your own risk.

**The user interface is in Italian.**

## What's inside

Three programs, independent but meant to work together:

| Command | What it does |
|---|---|
| `hoppy` | The mascot: walks on the taskbar and on window edges, follows you, chats, notifies, plays. |
| `hoppy-inline` | In any program, type `;;instruction;;` and the text is replaced by Claude's answer; with `;;question??` Claude reads the open document and Hoppy explains the answer on a blackboard. |
| `hoppy-popup` | `Ctrl+Shift+Space` on selected text opens a popup to ask Claude and paste the answer in place. |

### The mascot

- **Lives on your desktop:** walks on the taskbar and on window edges, climbs with super
  powers (web, rockets, telekinesis), moves between screens through portals, floats next
  to the cursor, falls asleep, gets hungry (right click > *Dai da mangiare*), and likes
  being petted by rubbing the cursor over it.
- **Character:** Hoppy the octopus, or the little crab (from the Settings).
- **Chats:** double click. It remembers your name and what you tell it, knows the Claude
  Code projects on your PC, opens Claude Code on a project, sets reminders and timers, and
  runs your quick commands (always after you say yes).
- **Explains:** `hoppy-inline` questions are explained on a blackboard wearing a professor
  wig, or by a TV presenter in a studio with statues and a little tune (Bach's Air on the
  G String, synthesized; never while the microphone is in use).
- **Notifies:** when a Claude Code session finishes or seems to be waiting for your
  permission; offers to explain errors you copy; keeps an eye on RAM and uptime; goes
  quiet in a corner during calls.
- **Helps with work:** morning standup (from yesterday's Claude Code sessions and
  commits), forgotten changes and unpushed commits, clipboard history.
- **Cleanup (off by default):** proposes to sort the desktop into monthly folders, to move
  old files into a «Da rivedere» folder (undoable), and to delete build folders of idle
  projects and old Maven cache versions (not undoable). It only moves or deletes after you
  say yes.
- **Games:** ball and hide-and-seek.

## Requirements

- Windows 10 or 11 (it uses Windows APIs: it does not run on macOS or Linux).
- Python 3.10 or newer, with tkinter (included in the python.org installer).
- [Claude Code](https://claude.com/claude-code) installed and logged in (`claude` must
  work from a terminal). Hoppy uses no API keys: it goes through the `claude -p` CLI with
  your own account.

**Costs:** every call to Claude uses your plan's credit. Headless use of Claude Code
(`claude -p`) may have its own rules and credits: check your plan's current terms. Hoppy
uses Haiku by default and shows in its menu how much it spent this month.

## Installation

With [pipx](https://pipx.pypa.io/) (recommended):

```powershell
pipx install git+https://github.com/Bazox96/hoppy
hoppy
```

On first launch a short tour explains what it does and asks what to turn on, including
starting with Windows. `hoppy` also starts `hoppy-popup` and `hoppy-inline` (you can turn
this off in the Settings); they can still be launched on their own.

From source:

```powershell
git clone https://github.com/Bazox96/hoppy
cd hoppy
pip install -e .
pythonw -m hoppy.pet
```

## Updates

Once a day Hoppy checks GitHub for a new release. If there is one, it asks you in its
speech bubble; answer 👍 and it closes the mascot, popup and inline, installs the new
version with pip (no git needed) and starts them again. 👎 skips that version. To check
right away, write *aggiornati* in the chat or use *Cerca aggiornamenti* in the menu. The
outcome is written to `%APPDATA%\Hoppy\update.log`; you can turn the check off in the
Settings (*Avvisi* tab).

To update by hand: `pipx install --force git+https://github.com/Bazox96/hoppy`.
After an automatic update `pipx list` may still show the old version number: it is only
pipx's bookkeeping. If you run Hoppy from source, it only tells you a new version is out.

## Usage

- **Right click on Hoppy:** the menu (chat, advice, standup, games, cleanup, Settings…).
- **Double click:** chat.
- **Drag it** with the left button and drop it.
- **Impostazioni…** (Settings, at the bottom of the menu): every feature can be turned on
  or off, with thresholds and timings; the *Avvio e file* tab opens the data folder,
  `config.json`, the quick commands and the memory.

### Quick commands

In `%APPDATA%\Hoppy\pet_commands.json` (from Settings > *Comandi rapidi*):

```json
[
  {"nome": "docker", "descrizione": "avvia Docker Desktop",
   "comando": "& 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'", "cartella": "~"}
]
```

In the chat: «esegui il comando docker» → Hoppy asks for confirmation and runs it in a new
PowerShell window. (The keys are Italian: `nome` = name, `descrizione` = description,
`comando` = command, `cartella` = working folder.)

### Second Claude Code profile

If you use a second Claude Code configuration (e.g. for work, with its own
`CLAUDE_CONFIG_DIR`), set it in Settings > *Claude*: Hoppy will know its projects and open
them with that profile.

## Data and privacy

- Everything is stored locally in `%APPDATA%\Hoppy`: `config.json`, the memory
  (`pet_memory.json`, human readable), the chats (`pet_sessions/`), quick commands, the
  cleanup log. *Dimentica tutto* (forget everything) in the menu deletes memory and chats.
- **Only what is needed goes to Claude:** the text you type or select, the open document
  for `;;…??` questions, the errors you ask to explain, and a few relevant snippets from
  your Claude Code project memories. Hoppy does not read credentials, `settings.json` or
  `CLAUDE.md`.
- **`hoppy-inline` uses a global keyboard hook**, so technically it works like a
  keylogger: it keeps in memory only the last few characters needed to spot the markers,
  saves nothing to disk and sends to Claude only the text between the markers. Some
  antivirus software may flag it.
- The **clipboard history** stays in RAM only and skips passwords, tokens and text that
  password managers mark as private.
- The mascot listens on a **local port** (`127.0.0.1:48761`) to receive questions from
  `hoppy-inline`. It is not reachable from other computers; programs on your PC can only
  make it show an explanation.
- The **update check** is one anonymous request a day to the GitHub API
  (`api.github.com/repos/Bazox96/hoppy/releases/latest`); it can be turned off.

## Uninstall

1. Settings > *Avvio e file*: turn off autostart (or delete the «Hoppy» shortcut in
   `shell:startup`).
2. `pipx uninstall hoppy`
3. To delete your data too: remove `%APPDATA%\Hoppy`.

## Known limitations

- Windows only, Italian user interface only.
- Meeting mode detects calls from the microphone in use or a full-screen app: screen
  sharing with the microphone off is not detected.
- In `hoppy-inline`, accented letters typed with dead keys are not captured.
- Screens are read at startup: if you plug in a new one, restart Hoppy.

## Development

```powershell
pip install -e .
python tests/run_all.py
```

Tests run with hidden windows and temporary data and folders.

To publish a release: bump `__version__` in `hoppy/__init__.py`, commit, then
`gh release create vX.Y.Z --generate-notes`. The tag must match the version.

## License

[MIT](LICENSE).
