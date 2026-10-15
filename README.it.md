# Hoppy

*[English](README.md) · Italiano*

Hoppy è un polipetto in pixel art che vive sul desktop di Windows e ti porta
[Claude Code](https://claude.com/claude-code) a portata di clic: ci chiacchieri, ti
spiega quello che stai leggendo, ti avvisa quando una sessione di Claude Code ha finito
e, se vuoi, ti aiuta a tenere in ordine desktop e disco.

> **Progetto hobbistico, non ufficiale.** Hoppy non è un prodotto di Anthropic e non è
> affiliato ad Anthropic. È fatto per divertimento, può contenere errori e viene fornito
> senza garanzie (vedi [LICENSE](LICENSE)). Lo usi a tuo rischio.

L'interfaccia è in italiano.

## Cosa c'è dentro

Tre programmi, indipendenti ma pensati per lavorare insieme:

| Comando | Cosa fa |
|---|---|
| `hoppy` | La mascotte: cammina sulla barra delle applicazioni e sui bordi delle finestre, ti segue, chiacchiera, avvisa, gioca. |
| `hoppy-inline` | In qualunque programma scrivi `;;istruzione;;` e il testo viene sostituito dalla risposta di Claude; con `;;domanda??` Claude legge il documento aperto e Hoppy ti spiega la risposta su una lavagna. |
| `hoppy-popup` | `Ctrl+Shift+Spazio` sul testo selezionato apre un popup per chiedere a Claude e incollare la risposta al suo posto. |

### La mascotte

- **Vive sul desktop:** cammina sulla barra delle applicazioni e sui bordi delle finestre,
  sale coi super poteri (ragnatela, razzi, telecinesi), passa da uno schermo all'altro coi
  portali, fluttua accanto al cursore, si addormenta, ha fame (tasto destro > *Dai da
  mangiare*), si fa accarezzare strofinandoci sopra il cursore.
- **Personaggio:** Hoppy il polipetto, oppure il granchietto (dalle Impostazioni).
- **Chiacchiera:** doppio clic. Ricorda il tuo nome e le cose che le dici, conosce i
  progetti di Claude Code sul tuo PC, apre Claude Code su un progetto, imposta promemoria
  e timer, lancia i tuoi comandi rapidi (sempre dopo un tuo sì).
- **Spiega:** le domande di `hoppy-inline` le spiega alla lavagna con la parrucca da
  professore, oppure da divulgatore in uno studio con le statue e una musichetta (l'Aria
  sulla quarta corda di Bach, sintetizzata; mai mentre il microfono è in uso).
- **Avvisa:** quando una sessione di Claude Code finisce o sembra aspettare un tuo
  permesso; se copi un errore ti propone di spiegarlo; tiene d'occhio RAM e ore di
  accensione; in call si mette zitta in un angolo.
- **Aiuta col lavoro:** standup del mattino (dalle tue sessioni di Claude Code e dai
  commit di ieri), modifiche dimenticate e commit non pushati, cronologia degli appunti.
- **Pulizie (spente di default):** propone di riordinare il desktop in cartelle per mese,
  di spostare i file vecchi in «Da rivedere» (si può annullare) e di eliminare le build
  dei progetti fermi e le versioni vecchie della cache Maven (non si può annullare).
  Sposta o cancella solo dopo il tuo sì.
- **Giochi:** palla e nascondino.

## Requisiti

- Windows 10 o 11 (usa API di Windows: non funziona su macOS o Linux).
- Python 3.10 o più recente, con tkinter (incluso nell'installer di python.org).
- [Claude Code](https://claude.com/claude-code) installato e con il login fatto
  (`claude` deve funzionare dal terminale). Hoppy non usa chiavi API: passa dalla CLI
  `claude -p` col tuo account.

**Costi:** ogni chiamata a Claude consuma credito del tuo abbonamento. L'uso headless di
Claude Code (`claude -p`) può avere regole e crediti suoi: controlla le condizioni attuali
del tuo piano. Hoppy usa Haiku di default e ti mostra nel menu quanto ha speso nel mese.

## Installazione

Con [pipx](https://pipx.pypa.io/) (consigliato):

```powershell
pipx install git+https://github.com/Bazox96/hoppy
hoppy
```

Al primo avvio una breve presentazione spiega cosa fa e ti chiede cosa attivare,
compreso l'avvio automatico con Windows. `hoppy` avvia anche `hoppy-popup` e `hoppy-inline`
(si può spegnere dalle Impostazioni); si possono comunque lanciare anche da soli.

Dai sorgenti:

```powershell
git clone https://github.com/Bazox96/hoppy
cd hoppy
pip install -e .
pythonw -m hoppy.pet
```

## Aggiornamenti

Una volta al giorno Hoppy controlla su GitHub se è uscita una versione nuova. Se c'è, te lo
chiede nel fumetto: rispondi 👍 e lei chiude mascotte, popup e inline, installa la nuova
versione con pip (non serve git) e li riapre. Il 👎 salta quella versione. Per controllare
subito scrivile *aggiornati* in chat o usa *Cerca aggiornamenti* nel menu. L'esito finisce
in `%APPDATA%\Hoppy\update.log`; il controllo si spegne dalle Impostazioni (scheda
*Avvisi*).

Per aggiornare a mano: `pipx install --force git+https://github.com/Bazox96/hoppy`.
Dopo un aggiornamento automatico `pipx list` potrebbe mostrare ancora il numero vecchio:
è solo il registro di pipx. Se usi Hoppy dai sorgenti, ti avvisa soltanto che è uscita.

## Uso

- **Tasto destro su Hoppy:** il menu (chiacchiera, consigli, standup, giochi, pulizie,
  Impostazioni…).
- **Doppio clic:** chiacchierate.
- **Trascinala** col tasto sinistro e lasciala cadere.
- **Impostazioni…** (in fondo al menu): ogni funzione si accende e si spegne, con soglie e
  tempi; la scheda *Avvio e file* apre la cartella dei dati, `config.json`, i comandi
  rapidi e la memoria.

### Comandi rapidi

In `%APPDATA%\Hoppy\pet_commands.json` (dalle Impostazioni > *Comandi rapidi*):

```json
[
  {"nome": "docker", "descrizione": "avvia Docker Desktop",
   "comando": "& 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'", "cartella": "~"}
]
```

In chat: «esegui il comando docker» → Hoppy chiede conferma e lo lancia in una nuova finestra PowerShell.

### Secondo profilo di Claude Code

Se usi una seconda configurazione di Claude Code (es. per il lavoro, con una sua
`CLAUDE_CONFIG_DIR`), indicala nelle Impostazioni > *Claude*: Hoppy ne conosce i progetti
e li apre con quel profilo.

## Dati e privacy

- Tutto sta in locale in `%APPDATA%\Hoppy`: `config.json`, la memoria (`pet_memory.json`,
  leggibile), le chiacchierate (`pet_sessions/`), i comandi rapidi, il registro delle
  pulizie. *Dimentica tutto* nel menu cancella memoria e chiacchierate.
- **A Claude va solo quello che serve:** il testo che scrivi o selezioni, il documento
  aperto nelle domande `;;…??`, gli errori che chiedi di spiegare, e pochi pezzi pertinenti
  delle memorie dei tuoi progetti di Claude Code. Hoppy non legge credenziali,
  `settings.json` né `CLAUDE.md`.
- **`hoppy-inline` usa un hook globale della tastiera**, quindi tecnicamente funziona come
  un keylogger: tiene in memoria solo gli ultimi caratteri che servono a riconoscere i
  marcatori, non salva niente su disco e manda a Claude solo il testo tra i marcatori.
  Alcuni antivirus potrebbero segnalarlo.
- La **cronologia degli appunti** resta solo in RAM e salta password, token e i testi che
  i password manager segnano come privati.
- La mascotte ascolta su una **porta locale** (`127.0.0.1:48761`) per ricevere le domande
  da `hoppy-inline`. Non è raggiungibile da altri computer; i programmi sul tuo PC possono
  solo farle mostrare una spiegazione.
- Il **controllo degli aggiornamenti** è una richiesta anonima al giorno all'API di GitHub
  (`api.github.com/repos/Bazox96/hoppy/releases/latest`); si può spegnere.

## Disinstallazione

1. Impostazioni > *Avvio e file*: togli l'avvio automatico (o cancella il collegamento
   «Hoppy» in `shell:startup`).
2. `pipx uninstall hoppy`
3. Se vuoi cancellare anche i dati: elimina `%APPDATA%\Hoppy`.

## Limiti noti

- Solo Windows, interfaccia solo in italiano.
- La modalità riunione riconosce le call dal microfono in uso o da un'app a schermo intero:
  una condivisione dello schermo a microfono spento non la vede.
- In `hoppy-inline` le lettere accentate ottenute coi tasti morti non vengono catturate.
- Gli schermi vengono letti all'avvio: se ne colleghi uno nuovo, riavvia Hoppy.

## Sviluppo

```powershell
pip install -e .
python tests/run_all.py
```

I test girano con le finestre nascoste e con dati e cartelle temporanei.

Per pubblicare una versione: alza `__version__` in `hoppy/__init__.py`, fai il commit, poi
`gh release create vX.Y.Z --generate-notes`. Il tag deve corrispondere alla versione.

## Licenza

[MIT](LICENSE).
