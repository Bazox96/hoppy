"""Traduzioni inglesi: testo italiano (come scritto nel codice) -> testo inglese."""

EN = {
    # ---- mascotte (pet.py)
    'Hoppy, un polipetto viola':
        'Hoppy, a little purple octopus',
    'un granchietto arancione':
        'a little orange crab',
    "Sei {who}, la mascotte che vive sul desktop di {user} e gli porta Claude a portata di clic. Parli in prima persona, in italiano, con tono caldo, curioso e un po' giocoso. Sei breve: una o due frasi, mai elenchi. Non inventare fatti personali sull'utente: usa solo quello che trovi in COSA RICORDO, PROGETTI, DIARIO, MEMORIE e CONVERSAZIONI PASSATE. Non dare consigli medici o finanziari seri.":
        "You are {who}, the mascot who lives on {user}'s desktop and brings Claude within a click's reach. You speak in the first person, in English, with a warm, curious and slightly playful tone. You are brief: one or two sentences, never lists. Don't make up personal facts about the user: use only what you find in WHAT I REMEMBER, PROJECTS, DIARY, MEMORIES and PAST CONVERSATIONS. Don't give serious medical or financial advice.",
    "Se l'utente ti chiede di aprire o avviare Claude (Claude Code) su uno dei suoi progetti, rispondi in breve e aggiungi come ultimissima riga '#AVVIA: <nome del progetto, scritto esattamente come in uno degli elenchi dei suoi progetti, personali o di lavoro>'. Altrimenti non aggiungerla mai. Se ti chiede di usare una delle sue SKILL (anche scrivendo /nome), aggiungi come ultimissima riga '#SKILL: <nome della skill> <argomenti, es. il codice del ticket>' (con #AVVIA solo se nomina anche un progetto).":
        "If the user asks you to open or start Claude (Claude Code) on one of their projects, answer briefly and add as the very last line '#AVVIA: <project name, written exactly as in one of the lists of their projects, personal or work>'. Otherwise never add it. If they ask you to use one of their SKILLS (even by writing /name), add as the very last line '#SKILL: <skill name> <arguments, e.g. the ticket code>' (with #AVVIA only if they also name a project).",
    "Se l'utente ti dice qualcosa che vale la pena ricordare (il suo nome, una preferenza, un progetto, un gusto), aggiungi come ultimissima riga '#RICORDA: <fatto in poche parole>'. Se ti dice come si chiama, usa '#NOME: <nome>'. Altrimenti non aggiungere nulla.":
        "If the user tells you something worth remembering (their name, a preference, a project, a taste), add as the very last line '#RICORDA: <the fact in a few words>'. If they tell you their name, use '#NOME: <name>'. Otherwise don't add anything.",
    "Adesso è {now}. Se l'utente ti chiede di ricordargli qualcosa a un'ora o in un giorno precisi, aggiungi come ultima riga '#PROMEMORIA: AAAA-MM-GG HH:MM | <cosa ricordare>'. Se chiede un timer o un pomodoro (pomodoro = 25 minuti), aggiungi '#TIMER: <minuti> | <etichetta>'. Se chiede di lanciare uno dei suoi COMANDI RAPIDI, aggiungi '#COMANDO: <nome esatto del comando>' (glielo farai confermare). Altrimenti niente.":
        "It is now {now}. If the user asks you to remind them of something at a specific time or day, add as the last line '#PROMEMORIA: YYYY-MM-DD HH:MM | <what to remember>'. If they ask for a timer or a pomodoro (pomodoro = 25 minutes), add '#TIMER: <minutes> | <label>'. If they ask to run one of their QUICK COMMANDS, add '#COMANDO: <exact command name>' (you'll have them confirm it). Otherwise nothing.",
    "Sei uno sviluppatore esperto e paziente. Spiega in italiano l'errore che ti viene incollato: **Causa** in una o due frasi, poi **Come risolvere** in due-quattro punti con '- '. Niente premesse, niente codice lungo.":
        "You are an experienced, patient developer. Explain in English the error that is pasted to you: **Cause** in one or two sentences, then **How to fix it** in two to four points with '- '. No preamble, no long code.",
    "Sei un collega esperto e paziente. Ti arriva la foto della finestra su cui l'utente sta lavorando. Spiega in italiano cosa sta succedendo: **Cosa vedo** in una o due frasi, poi, se c'è un errore o un problema, **Cosa fare** in due-quattro punti con '- '. Niente premesse.":
        "You are an experienced, patient colleague. You receive a picture of the window the user is working on. Explain in English what is going on: **What I see** in one or two sentences, then, if there's an error or a problem, **What to do** in two to four points with '- '. No preamble.",
    "Sei un revisore di codice Python conciso. Ti viene dato il sorgente di una mascotte da desktop in tkinter. Proponi 3 migliorie CONCRETE e piccole (bug, chiarezza, piccole feature), ognuna come '- [ ] titolo: una riga di spiegazione'. Solo la lista, niente altro.":
        "You are a concise Python code reviewer. You are given the source of a desktop mascot in tkinter. Suggest 3 CONCRETE, small improvements (bugs, clarity, small features), each as '- [ ] title: one line of explanation'. Write them in English. Only the list, nothing else.",
    "Scrivi il diario di una mascotte da desktop: una o due frasi in italiano, in prima persona (io = la mascotte), su di cosa abbiamo parlato e cosa ho capito dell'utente. Niente elenchi, niente saluti.":
        "Write the diary of a desktop mascot: one or two sentences in English, in the first person (I = the mascot, 'Tu' = the mascot, 'Utente' = the user), about what we talked about and what I learned about the user. No lists, no greetings.",
    'SORGENTE:\n':
        'SOURCE:\n',
    'CHIACCHIERATA:\n':
        'CHAT:\n',
    'ERRORE COPIATO:\n':
        'COPIED ERROR:\n',
    'COMANDI RAPIDI: ':
        'QUICK COMMANDS: ',
    'PROMEMORIA ATTIVI: ':
        'ACTIVE REMINDERS: ',
    'SKILL DI CLAUDE CODE: ':
        'CLAUDE CODE SKILLS: ',
    'COSA RICORDO: {ctx} Sei {mood}.\n':
        'WHAT I REMEMBER: {ctx} You are {mood}.\n',
    'CONVERSAZIONE FINORA (Tu = la mascotte):\n':
        'CONVERSATION SO FAR (Tu = you, the mascot; Utente = the user):\n',
    "Rispondi all'ultimo messaggio dell'utente, in carattere, tenendo conto di quanto vi siete già detti. ":
        "Reply to the user's last message, in character, in English, taking into account what you've already said to each other. ",
    'PROGETTI: ':
        'PROJECTS: ',
    'DIARIO DELLE VOSTRE CHIACCHIERATE:\n':
        'DIARY OF YOUR CHATS:\n',
    'MEMORIE DI CLAUDE CODE PERTINENTI:\n':
        'RELEVANT CLAUDE CODE MEMORIES:\n',
    'CONVERSAZIONI PASSATE PERTINENTI:\n':
        'RELEVANT PAST CONVERSATIONS:\n',
    "È {part} (ore {hour}). L'utente sta lavorando da circa {wm} minuti senza pause. Programma in primo piano: {app}. COSA RICORDO: {ctx}\n":
        "It's {part} ({hour} o'clock). The user has been working for about {wm} minutes without a break. Program in the foreground: {app}. WHAT I REMEMBER: {ctx}\n",
    'sconosciuto':
        'unknown',
    'Proponi tu, spontaneamente,':
        'Offer, on your own initiative,',
    'Ti ha chiesto':
        'They asked you for',
    'UN consiglio breve e gentile adatto a questo momento, in una frase.':
        'ONE short, kind piece of advice suited to this moment, in one sentence, in English.',
    'qualcuno':
        'someone',
    'mattina':
        'morning',
    'pomeriggio':
        'afternoon',
    'sera':
        'evening',
    'notte fonda':
        'late at night',
    'Programma: {app}. ':
        'Program: {app}. ',
    'Cosa sta succedendo qui?':
        "What's going on here?",
    'Cosa sta succedendo?':
        "What's going on?",
    'Errore':
        'Error',
    'Casuale':
        'Random',
    'Ragnatela':
        'Web',
    'Razzi':
        'Rockets',
    'Telecinesi':
        'Telekinesis',
    "CLI 'claude' non trovata":
        "'claude' CLI not found",
    'giù di morale':
        'feeling down',
    'tranquilla':
        'calm',
    'di buon umore':
        'in a good mood',
    'euforica':
        'euphoric',
    "L'utente si chiama {name}.":
        "The user's name is {name}.",
    'So queste cose: ':
        'I know these things: ',
    'Consigli graditi in passato: ':
        'Advice they liked in the past: ',
    'Non so ancora nulla di lei.':
        "I don't know anything about them yet.",
    'Domanda: «{q}»':
        'Question: «{q}»',
    '   ·   ho letto {ctx_len} caratteri':
        '   ·   I read {ctx_len} characters',
    'Incolla al cursore':
        'Paste at cursor',
    'Copia':
        'Copy',
    'Chiudi':
        'Close',
    'Mmm, fammi pensare':
        'Hmm, let me think',
    'Copiato':
        'Copied',
    'Le novità di questa versione':
        "What's new in this version",
    'In sospeso':
        'Pending',
    'Non ho trovato niente di ieri da raccontare.':
        "I didn't find anything from yesterday to tell.",
    'Non sono riuscita a capirlo: ':
        "I couldn't figure it out: ",
    'Buongiorno! Il tuo standup di oggi':
        'Good morning! Your standup for today',
    'Il tuo standup':
        'Your standup',
    'Non trovo un buon nascondiglio... giochiamo dopo?':
        "I can't find a good hiding spot... play later?",
    'Ci lavoro…':
        'On it…',
    'Ops, non ci sono riuscito':
        "Oops, I couldn't do it",
    'Fatto!':
        'Done!',
    'Ho dimenticato tutto. Piacere, come ti chiami?':
        "I forgot everything. Nice to meet you, what's your name?",
    'Sul desktop ci sono {n} file sparsi ({names}). Li metto in {months} cartelle per mese, da {first} a {last}?':
        'There are {n} loose files on the desktop ({names}). Shall I put them in {months} folders by month, from {first} to {last}?',
    'Ci sono {n} cartelle di build di progetti fermi da 2 mesi: {size} da liberare ({names}...). Le elimino? Si rigenerano con npm install / mvn.':
        'There are {n} build folders from projects untouched for 2 months: {size} to free up ({names}...). Shall I delete them? npm install / mvn will rebuild them.',
    'Nella cache di Maven (.m2) ci sono {n} versioni di librerie non usate da 6 mesi: {size}. Le elimino? Se servono, Maven le riscarica.':
        "The Maven cache (.m2) has {n} library versions unused for 6 months: {size}. Shall I delete them? If they're needed, Maven will download them again.",
    'Ho trovato {n} file non usati da 6 mesi fra Desktop e Download ({size}: {names}). Li sposto nelle cartelle «Da rivedere»?':
        'I found {n} files unused for 6 months in Desktop and Downloads ({size}: {names}). Shall I move them to the «Da rivedere» (to review) folders?',
    'Desktop e Download sono in ordine! Ora cerco build vecchie nei progetti: ci metto un paio di minuti, poi ti dico.':
        "Desktop and Downloads are tidy! Now I'm looking for old builds in your projects: it'll take a couple of minutes, then I'll let you know.",
    'Ho controllato: è tutto in ordine!':
        'I checked: everything is tidy!',
    "Va bene, lascio tutto com'è.":
        "Okay, I'll leave everything as it is.",
    'Faccio spazio…':
        'Making room…',
    "Ci penso io, ci vorrà un po'.":
        "Leave it to me, it'll take a while.",
    'Fatto! Ho spostato {n} file.':
        'Done! I moved {n} files.',
    ' {failed} non li ho potuti toccare (forse sono aperti).':
        " I couldn't touch {failed} of them (maybe they're open).",
    ' Se cambi idea: menu > Annulla pulizie.':
        ' If you change your mind: menu > Undo cleanup.',
    'Non ho pulizie da annullare.':
        'I have no cleanup to undo.',
    "Rimesso a posto: {back} file tornati dov'erano (pulizie del {t}).":
        'Put back: {back} files returned where they were (cleanup of {t}).',
    ' {failed} non li ho trovati più.':
        " I couldn't find {failed} of them anymore.",
    'Fatto! Ho liberato {size}.':
        'Done! I freed up {size}.',
    ' {failed} cartelle non sono riuscita a toglierle (file in uso?).':
        " I couldn't remove {failed} folders (files in use?).",
    "Controllo se c'è una versione nuova...":
        'Checking for a new version...',
    'Non riesco a controllare adesso: riprova più tardi.':
        "I can't check right now: try again later.",
    "Sono già all'ultima versione ({version}).":
        "I'm already on the latest version ({version}).",
    'È uscita la versione {version}! La trovi su github.com/{repo}':
        "Version {version} is out! You'll find it at github.com/{repo}",
    'È uscita la versione {version}! La installo? Mi chiudo un attimo e torno da sola.':
        "Version {version} is out! Shall I install it? I'll close for a moment and come right back.",
    'Va bene, te lo richiedo alla prossima versione.':
        "Okay, I'll ask again with the next version.",
    'Mi aggiorno! Torno fra un minuto.':
        'Updating! Back in a minute.',
    'il PC è acceso da {hours} ore':
        'the PC has been on for {hours} hours',
    'la memoria impegnata è al {pct:.0f}%':
        'committed memory is at {pct:.0f}%',
    'la memoria del kernel è a {gb:.1f} GB':
        'kernel memory is at {gb:.1f} GB',
    'Attenzione: ':
        'Heads up: ',
    ' e ':
        ' and ',
    '. Un riavvio libera la memoria: ':
        '. A restart frees the memory: ',
    'riavvia appena puoi!':
        'restart as soon as you can!',
    'a fine giornata riavviamo?':
        'shall we restart at the end of the day?',
    'PC acceso da {hours:.1f} ore. Memoria impegnata {commit:.0f} su {limit:.0f} GB ({pct:.0f}%), memoria del kernel {kernel:.1f} GB. Io questo mese ho speso {spent} di credito.':
        "PC on for {hours:.1f} hours. Committed memory {commit:.0f} of {limit:.0f} GB ({pct:.0f}%), kernel memory {kernel:.1f} GB. This month I've spent {spent} of credit.",
    'Mi riavvio per le nuove impostazioni...':
        'Restarting for the new settings...',
    'Impostazioni salvate!':
        'Settings saved!',
    'Fine call! Ultima della giornata?':
        "Call's over! Last one of the day?",
    "Fine call! Com'è andata?":
        "Call's over! How did it go?",
    '«{name}» ha finito!':
        '«{name}» is done!',
    '«{name}» forse aspetta un tuo permesso.':
        '«{name}» may be waiting for your permission.',
    'Hai copiato un errore: te lo spiego sulla lavagna?':
        'You copied an error: shall I explain it on the blackboard?',
    'Non vedo nessuna finestra: clicca su quella che ti interessa e richiedimelo.':
        "I can't see any window: click on the one you're interested in and ask me again.",
    'Non ho ancora visto niente di copiato (le password e i testi privati non li guardo).':
        "I haven't seen anything copied yet (I don't look at passwords and private text).",
    'Appunti recenti (doppio clic = copia, Esc = chiudi)':
        'Recent clipboard (double click = copy, Esc = close)',
    'Copiato!':
        'Copied!',
    ' (era per le {time:%H:%M})':
        ' (it was for {time:%H:%M})',
    'Promemoria!':
        'Reminder!',
    ': tempo scaduto!':
        ": time's up!",
    '\n(Non ho capito per quando è il promemoria.)':
        "\n(I didn't understand when the reminder is for.)",
    '\n(Non ho capito quanti minuti.)':
        "\n(I didn't understand how many minutes.)",
    '\n(Non conosco il comando «{val}».)':
        "\n(I don't know the command «{val}».)",
    'Ok, non lancio niente.':
        "Okay, I won't run anything.",
    'Lanciato «{name}»!':
        'Launched «{name}»!',
    'Non sono riuscita a lanciare «{name}» (cartella sbagliata?).':
        "I couldn't launch «{name}» (wrong folder?).",
    'Buongiorno{name}!':
        'Good morning{name}!',
    'È venerdì sera: buon weekend in arrivo!':
        "It's Friday evening: have a great weekend!",
    'Palla! Lanciala (trascinala e lasciala andare) e io la rincorro.':
        "Ball! Throw it (drag it and let go) and I'll chase it.",
    'Non ci sono finestre dietro cui nascondermi!':
        'There are no windows to hide behind!',
    'Nascondino! Conta fino a dieci... poi trovami e cliccami!':
        'Hide and seek! Count to ten... then find me and click me!',
    'Non mi hai trovata! Ho vinto io!':
        "You didn't find me! I win!",
    'Mi hai trovata in {secs} secondi! Bravo!':
        'You found me in {secs} seconds! Well done!',
    'Ho un certo languorino... un biscotto?':
        "I'm feeling a bit peckish... a cookie?",
    'Mi daresti qualcosa da sgranocchiare?':
        'Could you give me something to nibble on?',
    "Mi sento un po' sola quassù.":
        'I feel a bit lonely up here.',
    'Ci sei ancora? Mi mancavi.':
        'Are you still there? I missed you.',
    'Ciao{name}! Tutto bene?':
        'Hi{name}! All good?',
    'Sto facendo due passi sui bordi.':
        "I'm taking a little stroll along the edges.",
    'Se ti serve una mano, doppio clic su di me.':
        'If you need a hand, double-click on me.',
    'Come procede {p}?':
        "How's {p} going?",
    'Se vuoi ti apro Claude su {p}: chiedimelo!':
        'If you like, I can open Claude on {p}: just ask!',
    'Scusa, mi si è annodata la lingua. Riprova!':
        'Sorry, I got tongue-tied. Try again!',
    'Mmm, non mi viene in mente nulla di furbo adesso.':
        'Hmm, nothing clever comes to mind right now.',
    'Ci penso io!':
        'Leave it to me!',
    '{clean}\nLancio «{name}»? ({command})':
        '{clean}\nShall I run «{name}»? ({command})',
    'Rifletto su come potrei migliorarmi...':
        'Thinking about how I could improve myself...',
    'Non sono riuscita a farmi venire idee, pazienza.':
        "I couldn't come up with any ideas, oh well.",
    'Ho scritto qualche idea in pet_proposals.md, decidi tu!':
        'I wrote a few ideas in pet_proposals.md, you decide!',
    'Avevo delle idee ma non riesco a salvarle.':
        "I had some ideas but I can't save them.",
    'Grazie, me lo segno!':
        "Thanks, I'll make a note of it!",
    'Ok, cambio registro.':
        "Okay, I'll change my tune.",
    'Parliamo! (Invio = manda, Esc = chiudi)':
        "Let's talk! (Enter = send, Esc = close)",
    '\n(Non trovo la skill «{sname}».)':
        "\n(I can't find the skill «{sname}».)",
    '\n(Non trovo il progetto «{name}».)':
        "\n(I can't find the project «{name}».)",
    '\n(Non sono riuscita ad aprire Claude Code.)':
        "\n(I couldn't open Claude Code.)",
    'Sì':
        'Yes',
    'Utile':
        'Useful',
    'Eccomi! Ora sono la versione {version}.':
        "Here I am! I'm now version {version}.",
    'Non sono riuscita ad aggiornarmi: i dettagli sono in update.log, nella cartella dei dati.':
        "I couldn't update myself: the details are in update.log, in the data folder.",
    'Scintille':
        'Sparks',
    'Ovali':
        'Ovals',
    'PC: {hours:.0f} h · mem {pct:.0f}% · ':
        'PC: {hours:.0f} h · mem {pct:.0f}% · ',
    'PC e spesa: ':
        'PC and spending: ',
    'sì':
        'yes',
    'no':
        'no',
    'Parla con me':
        'Talk to me',
    'Dammi un consiglio':
        'Give me some advice',
    'Standup di oggi':
        "Today's standup",
    'Dai da mangiare':
        'Feed me',
    'Basta palla':
        'Enough ball',
    'Gioca a palla':
        'Play ball',
    'Nascondino':
        'Hide and seek',
    'Appunti recenti':
        'Recent clipboard',
    'Spiegami lo schermo':
        'Explain my screen',
    'Segui il mouse: ':
        'Follow the mouse: ',
    'Portale: ':
        'Portal: ',
    'Mantello: ':
        'Cape: ',
    'Potere: ':
        'Power: ',
    'Zitta in riunione: ':
        'Quiet in meetings: ',
    'Fai le pulizie':
        'Do the cleanup',
    'Annulla pulizie':
        'Undo cleanup',
    'Proponi miglioramenti':
        'Suggest improvements',
    'Impostazioni…':
        'Settings…',
    'Cerca aggiornamenti':
        'Check for updates',
    'Dimentica tutto':
        'Forget everything',
    'Esci':
        'Quit',
    # ---- Impostazioni e presentazione (settings.py, config.py)
    'Haiku (veloce, costa poco)':
        'Haiku (fast, cheap)',
    'Opus (il più bravo)':
        'Opus (the smartest)',
    'Personaggio':
        'Character',
    'Hoppy, il polipetto':
        'Hoppy, the little octopus',
    'Il granchietto':
        'The little crab',
    'Mantello da supereroe':
        'Superhero cape',
    'Super potere per salire':
        'Superpower for climbing',
    'Stile del portale':
        'Portal style',
    'Anello di scintille':
        'Ring of sparks',
    'Ovali turchese e magenta':
        'Turquoise and magenta ovals',
    'Avvia anche popup e inline insieme a Hoppy':
        'Also start popup and inline with Hoppy',
    'Ctrl+Shift+Spazio e ;;...;; funzionano solo se girano.':
        "Ctrl+Shift+Space and ;;...;; only work while they're running.",
    'Si addormenta dopo (secondi senza mouse)':
        'Falls asleep after (seconds without mouse)',
    'Le viene fame dopo (minuti)':
        'Gets hungry after (minutes)',
    "Durante le call si mette zitta nell'angolo":
        'Goes quiet in the corner during calls',
    "Riconosce la call dal microfono in uso o da un'app a schermo intero.":
        'Spots a call from the microphone being in use or a full-screen app.',
    'Saluti e reazioni (buongiorno, fine call, venerdì sera)':
        'Greetings and reactions (good morning, end of call, Friday evening)',
    'Chi spiega le risposte':
        'Who explains the answers',
    'A caso':
        'Random',
    'Il professore alla lavagna':
        'The professor at the blackboard',
    'Il divulgatore nello studio':
        'The TV presenter in the studio',
    'Musichetta nello studio del divulgatore':
        "Little tune in the TV presenter's studio",
    'Mai mentre il microfono è in uso.':
        'Never while the microphone is in use.',
    'Avvisa quando una sessione di Claude Code finisce':
        'Tell me when a Claude Code session ends',
    'Anche quando sembra aspettare un tuo permesso.':
        'Also when it seems to be waiting for your permission.',
    '...e quando un comando è fermo da (secondi)':
        '...and when a command has been stuck for (seconds)',
    'Offre di spiegare gli errori che copi':
        'Offer to explain errors you copy',
    "L'errore va a Claude solo se rispondi di sì.":
        'The error goes to Claude only if you say yes.',
    'Cronologia degli appunti (solo in RAM)':
        'Clipboard history (RAM only)',
    'Ultimi 20 testi copiati, senza password né token.':
        'Last 20 copied texts, no passwords or tokens.',
    'Guardiano della RAM e delle ore di accensione':
        'RAM and uptime watchdog',
    '...avvisa dopo (ore di accensione)':
        '...warn after (hours of uptime)',
    '...o con la memoria impegnata oltre il (%)':
        '...or with committed memory above (%)',
    'Standup del mattino sulla lavagna':
        'Morning standup on the blackboard',
    'Dalle tue sessioni di Claude Code e dai commit di ieri; una chiamata a Claude al giorno.':
        "From yesterday's Claude Code sessions and commits; one call to Claude a day.",
    '...dopo le ore':
        '...after (hour)',
    'Consigli spontanei (pause, ore piccole)':
        'Unprompted tips (breaks, late nights)',
    '...al massimo al giorno':
        '...at most per day',
    'Avvisa quando esce una nuova versione di Hoppy':
        'Tell me when a new version of Hoppy is out',
    'Una richiesta al giorno a GitHub; installa solo se rispondi di sì.':
        'One request a day to GitHub; installs only if you say yes.',
    'Propone di riordinare il desktop in cartelle per mese':
        'Offer to tidy the desktop into monthly folders',
    'Sposta, non cancella; si può annullare dal menu.':
        "Moves, doesn't delete; can be undone from the menu.",
    '...lasciando stare i file usati negli ultimi (giorni)':
        '...leaving alone files used in the last (days)',
    'Propone di spostare i file vecchi in «Da rivedere»':
        'Offer to move old files to «Da rivedere» (to review)',
    'Desktop e Download; si può annullare dal menu.':
        'Desktop and Downloads; can be undone from the menu.',
    '...vecchi = non usati da (giorni)':
        '...old = not used for (days)',
    'Propone di ELIMINARE le build dei progetti fermi':
        'Offer to DELETE builds of idle projects',
    'node_modules, target, build... dei progetti di Claude Code. Non si può annullare (si rigenerano con npm install / mvn).':
        "node_modules, target, build... of your Claude Code projects. Can't be undone (they come back with npm install / mvn).",
    '...progetti fermi da (giorni)':
        '...projects idle for (days)',
    'Propone di ELIMINARE le versioni vecchie della cache Maven':
        'Offer to DELETE old versions from the Maven cache',
    'Maven le riscarica se servono.':
        'Maven downloads them again if needed.',
    '...non usate da (giorni)':
        '...not used for (days)',
    'Modello della mascotte':
        "Mascot's model",
    'Modello di ;;...;; e ;;...??':
        'Model for ;;...;; and ;;...??',
    "Vale dal prossimo avvio dell'inline.":
        'Takes effect the next time inline starts.',
    'Modello del popup (Ctrl+Shift+Spazio)':
        'Popup model (Ctrl+Shift+Space)',
    'Vale dal prossimo avvio del popup.':
        'Takes effect the next time the popup starts.',
    'Ho un secondo profilo di Claude Code (es. per il lavoro)':
        'I have a second Claude Code profile (e.g. for work)',
    'Una seconda cartella di configurazione (CLAUDE_CONFIG_DIR).':
        'A second config folder (CLAUDE_CONFIG_DIR).',
    '...cartella del profilo':
        '...profile folder',
    '...come lo chiamo':
        '...what I call it',
    '...comando che lo avvia (vuoto = claude)':
        '...command that starts it (empty = claude)',
    '...leggi anche le sue memorie':
        '...read its memories too',
    'I pezzi pertinenti vanno a Claude dal tuo account personale.':
        'The relevant bits go to Claude from your personal account.',
    'Ciao!':
        'Hi!',
    'Sono {app}: una mascotte che vive sul tuo desktop e ti porta Claude a portata di clic.\n\nCammina sulla barra delle applicazioni e sui bordi delle finestre, ti segue col mouse, si addormenta se la lasci sola, e ogni tanto ha fame.\n\nIn questa breve presentazione ti dico cosa so fare, cosa mando a Claude e cosa vuoi attivare. Puoi cambiare tutto in seguito: tasto destro su di me > Impostazioni.':
        "I'm {app}: a mascot that lives on your desktop and puts Claude one click away.\n\nI walk along the taskbar and the edges of windows, follow your mouse, fall asleep if you leave me alone, and get hungry now and then.\n\nIn this short intro I'll tell you what I can do, what I send to Claude and what you want to turn on. You can change everything later: right-click me > Settings.",
    'Un progetto hobbistico':
        'A hobby project',
    'Questo è un progetto amatoriale, fatto per divertimento.\n\n• Non è un prodotto di Anthropic e non è affiliato ad Anthropic.\n• Può contenere errori: non ha garanzie di nessun tipo.\n• Alcune funzioni (le pulizie, i comandi rapidi) spostano o eliminano file, o lanciano comandi: lo fanno solo dopo il tuo sì, ma controlla sempre cosa ti propongo.\n\nLo usi a tuo rischio. Se trovi un problema, segnalalo: mi aiuti a migliorare.':
        "This is a hobby project, made for fun.\n\n• It's not an Anthropic product and it's not affiliated with Anthropic.\n• It may contain bugs: no warranties of any kind.\n• Some features (cleanup, quick commands) move or delete files, or run commands: they only do it after you say yes, but always check what I suggest.\n\nUse it at your own risk. If you find a problem, report it: you'll help me get better.",
    'Cosa so fare':
        'What I can do',
    '• Doppio clic su di me: chiacchieriamo. Ricordo il tuo nome e i tuoi progetti, apro Claude Code su un progetto, imposto promemoria e timer.\n• Scrivi ;;domanda?? in qualunque programma: ti spiego la risposta su una lavagna. Con ;;istruzione;; trasformo il testo al posto tuo.\n• Ctrl+Shift+Spazio: un popup per chiedere al volo.\n• Ti avviso quando una sessione di Claude Code finisce o aspetta un permesso.\n• Se copi un errore, posso spiegartelo.\n• Standup del mattino, cronologia degli appunti, riordino del desktop, pulizia delle build vecchie.\n• E poi giochi: palla, nascondino, carezze, biscotti.':
        "• Double-click me: let's chat. I remember your name and your projects, open Claude Code on a project, set reminders and timers.\n• Type ;;question?? in any program: I'll explain the answer on a blackboard. With ;;instruction;; I transform the text for you.\n• Ctrl+Shift+Space: a popup for quick questions.\n• I let you know when a Claude Code session ends or is waiting for permission.\n• If you copy an error, I can explain it.\n• Morning standup, clipboard history, desktop tidying, cleanup of old builds.\n• And games: ball, hide and seek, pats, cookies.",
    'Cosa mando a Claude':
        'What I send to Claude',
    "Uso il tuo Claude Code (claude -p), col tuo account: niente chiavi da configurare.\n\n• A Claude va solo quello che serve alla domanda: il testo che scrivi o selezioni, e pochi pezzi pertinenti delle memorie dei tuoi progetti.\n• Le chiacchierate e la memoria restano in locale, in un file che puoi leggere.\n• La cronologia degli appunti resta solo in RAM e salta password e token.\n\nOgni chiamata consuma credito del tuo abbonamento (per gli usi headless c'è un credito mensile separato). Quanto spendo lo vedi nel mio menu.":
        "I use your Claude Code (claude -p), with your account: no keys to set up.\n\n• Claude only gets what the question needs: the text you type or select, and a few relevant bits of your projects' memories.\n• Chats and memory stay local, in a file you can read.\n• Clipboard history stays in RAM only and skips passwords and tokens.\n\nEvery call uses credit from your subscription (headless use has a separate monthly credit). You can see how much I spend in my menu.",
    'CIAO!':
        'HI!',
    'UN PROGETTO HOBBISTICO':
        'A HOBBY PROJECT',
    'COSA SO FARE':
        'WHAT I CAN DO',
    'COSA MANDO A CLAUDE':
        'WHAT I SEND TO CLAUDE',
    'COSA ATTIVO?':
        'WHAT SHOULD I TURN ON?',
    'TUTTO PRONTO!':
        'ALL SET!',
    'AVANTI':
        'NEXT',
    'INDIETRO':
        'BACK',
    'FINE':
        'DONE',
    'Ho capito: è un progetto hobbistico e lo uso a mio rischio':
        "Got it: it's a hobby project and I use it at my own risk",
    'Quelle che toccano i tuoi file partono spente.':
        'The ones that touch your files start off.',
    'Tasto destro su di me: il menu, con Impostazioni in fondo.\nDoppio clic: parliamo.\n\n':
        "Right-click me: the menu, with Settings at the bottom.\nDouble-click: let's talk.\n\n",
    'Ho trovato Claude Code: possiamo cominciare.':
        'I found Claude Code: we can get started.',
    'Attenzione: non trovo Claude Code (il comando claude). Installalo e fai il login, altrimenti non posso rispondere alle domande.':
        "Heads up: I can't find Claude Code (the claude command). Install it and log in, otherwise I can't answer questions.",
    '{app} - Impostazioni':
        '{app} - Settings',
    'Mascotte':
        'Mascot',
    'Avvisi':
        'Alerts',
    'Pulizie':
        'Cleanup',
    'Avvio e file':
        'Startup and files',
    'SALVA':
        'SAVE',
    'ANNULLA':
        'CANCEL',
    '  (al riavvio)':
        '  (on restart)',
    'Avvia Hoppy con Windows':
        'Start Hoppy with Windows',
    'Apri:':
        'Open:',
    'CARTELLA DATI':
        'DATA FOLDER',
    'COMANDI RAPIDI':
        'QUICK COMMANDS',
    'MEMORIA':
        'MEMORY',
    'PROPOSTE':
        'PROPOSALS',
    'ISTRUZIONI':
        'INSTRUCTIONS',
    'Se modifichi config.json a mano, poi premi RICARICA.':
        'If you edit config.json by hand, then press RELOAD.',
    'RICARICA':
        'RELOAD',
    'RIVEDI LA PRESENTAZIONE':
        'REPLAY THE INTRO',
    'Versione {version}  ·  dati in {path}':
        'Version {version}  ·  data in {path}',
    'Serve un numero in «{name}»':
        '«{name}» needs a number',
    # ---- inline e popup (inline.py, popup.py)
    "Sei un assistente integrato in un campo di testo su Windows. L'utente ti invia un'ISTRUZIONE. Rispondi SOLO con il testo risultante, pronto per essere inserito dove si trova il cursore: niente preamboli, spiegazioni, virgolette o markdown. Mantieni la lingua dell'istruzione. Sii conciso.":
        'You are an assistant built into a text field on Windows. The user sends you an INSTRUCTION. Reply ONLY with the resulting text, ready to be inserted where the cursor is: no preamble, explanations, quotes or markdown. Keep the language of the instruction. Be concise.',
    "Sei un assistente integrato nel desktop di Windows. Ricevi il CONTENUTO del documento o della pagina che l'utente ha aperto e una sua DOMANDA. Rispondi alla domanda basandoti sul contenuto, in modo chiaro e ordinato, nella lingua della domanda. Puoi usare paragrafi ed elenchi puntati semplici; niente tabelle markdown. Se il contenuto è vuoto o non pertinente, dillo in una riga.":
        'You are an assistant built into the Windows desktop. You receive the CONTENT of the document or page the user has open and their QUESTION. Answer the question based on the content, clearly and tidily, in the language of the question. You may use paragraphs and simple bullet lists; no markdown tables. If the content is empty or not relevant, say so in one line.',
    'ISTRUZIONE:':
        'INSTRUCTION:',
    'CONTENUTO DEL DOCUMENTO:':
        'DOCUMENT CONTENT:',
    'DOMANDA:':
        'QUESTION:',
    "Eseguibile 'claude' non trovato nel PATH.":
        "'claude' executable not found in PATH.",
    'Nessuna risposta entro {secs}s.':
        'No answer within {secs}s.',
    'Mi hai chiesto: «{q}»':
        'You asked me: “{q}”',
    '   ·   ho letto {context_len} caratteri':
        '   ·   I read {context_len} characters',
    'Sto leggendo la pagina':
        'Reading the page',
    'Ci sto lavorando':
        'Working on it',
    'Non ci sono riuscito: ':
        "I couldn't do it: ",
    'Hook non attivo':
        'Hook not active',
    "Sei un assistente integrato in un popup di sistema su Windows. L'utente ti dà un'ISTRUZIONE e, se presente, un TESTO SELEZIONATO. Rispondi SOLO con il testo risultante, pronto per essere incollato al posto della selezione: niente preamboli, spiegazioni, virgolette o markdown. Se non c'è testo selezionato, rispondi all'istruzione nel modo più conciso possibile. Mantieni la lingua del testo selezionato, o dell'istruzione se non c'è selezione.":
        'You are an assistant built into a system popup on Windows. The user gives you an INSTRUCTION and, if present, a SELECTED TEXT. Reply ONLY with the resulting text, ready to be pasted in place of the selection: no preamble, explanations, quotes or markdown. If there is no selected text, answer the instruction as concisely as possible. Keep the language of the selected text, or of the instruction if there is no selection.',
    'TESTO SELEZIONATO:':
        'SELECTED TEXT:',
    'Sostituisci':
        'Replace',
    'Inserisci':
        'Insert',
    'Selezione: {n} caratteri':
        'Selection: {n} characters',
    'Nessuna selezione':
        'No selection',
    'Attendo Claude…':
        'Waiting for Claude…',
    'Errore: ':
        'Error: ',
    "Impossibile registrare la hotkey (errore {data}). Un'altra istanza è già in esecuzione?":
        "Couldn't register the hotkey (error {data}). Is another instance already running?",
    # ---- progetti, standup, pulizie, novità (knowledge.py, work.py, chores.py, changelog.py)
    '**Parlo anche inglese**: scegli la lingua in Impostazioni > Mascotte > Lingua / Language.':
        '**I speak English too**: pick the language in Settings > Mascot > Lingua / Language.',
    'I suoi progetti: ':
        'Their projects: ',
    'il profilo {label}':
        'the {label} profile',
    'I suoi progetti di {label} (si aprono con {launcher}): ':
        'Their {label} projects (opened with {launcher}): ',
    'Ultimamente ci lavora su: ':
        'Lately working on: ',
    'Su di lui: ':
        'About them: ',
    'una sessione':
        'a session',
    'personale':
        'personal',
    '{name}: {dirty} file modificati e non committati da {days} giorni':
        '{name}: {dirty} modified files not committed for {days} days',
    '{name}: {ahead} commit su {branch} non ancora pushati':
        '{name}: {ahead} commits on {branch} not pushed yet',
    'Ultimo giorno lavorativo: {since:%A %d/%m}.':
        'Last working day: {since:%A %d/%m}.',
    'Sessioni Claude Code su {name} ({n} richieste): ':
        'Claude Code sessions on {name} ({n} requests): ',
    'Commit su {name}: ':
        'Commits on {name}: ',
    "Scrivi lo standup del mattino di uno sviluppatore, in italiano, dai dati sotto. Tre sezioni brevi con titolo in grassetto (**Ieri**, **Oggi**, **Blocchi**): elenchi puntati con '- ', al massimo 5 punti per sezione, frasi corte in prima persona. In **Oggi** proponi il seguito naturale del lavoro di ieri. In **Blocchi** scrivi 'Nessuno' se non emerge nulla. Niente premesse né saluti.":
        "Write a developer's morning standup, in English, from the data below. Three short sections with a bold title (**Yesterday**, **Today**, **Blockers**): bullet lists with '- ', at most 5 points per section, short sentences in the first person. In **Today** suggest the natural next step from yesterday's work. In **Blockers** write 'None' if nothing comes up. No preamble, no greetings.",
    '{usd:.2f} $ · {calls} chiamate':
        '${usd:.2f} · {calls} calls',
    'pochi KB':
        'a few KB',
    '**Versione {v}**':
        '**Version {v}**',
    '**Spiegami lo schermo**: dal menu, o scrivendo in chat «cosa succede?», Hoppy fotografa la finestra su cui stavi lavorando e Claude ti spiega cosa vede.':
        "**Explain my screen**: from the menu, or by typing “what's going on?” in chat, Hoppy snaps the window you were working on and Claude explains what it sees.",
    'Dopo ogni aggiornamento Hoppy ti racconta le novità sulla lavagna.':
        "After every update Hoppy tells you what's new on the blackboard.",
    '**Cerca aggiornamenti**: dal menu, o scrivendo in chat «aggiornati».':
        '**Check for updates**: from the menu, or by typing “update” in chat.',
    'Apre le skill di Claude Code dalla chat («apri /nome-skill»).':
        'Opens Claude Code skills from chat (“open /skill-name”).',
    'Avvia da sola popup e inline; un solo collegamento di avvio automatico.':
        'Starts popup and inline by itself; just one autostart shortcut.',
    'Si aggiorna da sola quando esce una versione nuova.':
        'Updates itself when a new version comes out.',
    'Prima versione.':
        'First version.',
    '**Scegli il profilo di Claude**: in Impostazioni > Claude puoi far rispondere Hoppy col secondo profilo (es. l\'account aziendale).':
        '**Choose the Claude profile**: in Settings > Claude you can have Hoppy answer with your second profile (e.g. your work account).',
    'Se Claude non risponde, Hoppy ti dice perché e annota l\'errore in errors.log.':
        "If Claude doesn't answer, Hoppy tells you why and writes the error to errors.log.",
    'Funziona anche con Claude Code installato da npm.':
        'Also works with Claude Code installed from npm.',
    "**Segui il mouse: no** ora vuol dire che Hoppy ti lascia lavorare: se hai più schermi, va su uno diverso da quello dove c'è il cursore.":
        "**Follow the mouse: no** now means Hoppy lets you work: if you have more than one screen, it moves to one other than the one with your cursor.",
    'Le risposte di Hoppy usano il profilo':
        "Hoppy's answers use the profile",
    'Scegli il secondo profilo se usi Claude Code solo lì (es. account aziendale).':
        'Pick the second profile if that is the only one you use Claude Code with (e.g. a work account).',
    'personale (~/.claude)':
        'personal (~/.claude)',
    'secondo profilo (sotto)':
        'second profile (below)',
    'Non trovo Claude Code. Installalo (claude.ai/install) e riprova.':
        "I can't find Claude Code. Install it (claude.ai/install) and try again.",
    "Claude non ha il login su questo profilo. Apri un terminale, scrivi claude e fai /login, oppure scegli l'altro profilo in Impostazioni > Claude.":
        'Claude is not logged in on this profile. Open a terminal, type claude and run /login, or pick the other profile in Settings > Claude.',
    'Ho finito il credito di Claude o ho raggiunto un limite. Riprova più tardi.':
        "I'm out of Claude credit or hit a limit. Try again later.",
    "Claude non ha risposto in tempo: forse la rete è lenta o c'è un proxy.":
        "Claude didn't answer in time: maybe the network is slow or there's a proxy.",
    'Scusa, mi si è annodata la lingua. Riprova! (Il motivo è in errors.log, nella cartella di Hoppy.)':
        "Sorry, I got tongue-tied. Try again! (The reason is in errors.log, in Hoppy's folder.)",
}
