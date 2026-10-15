"""Verifica la logica di carattere/memoria/consigli senza spendere credito (ask_claude finto)."""
import time, tkinter as tk
import _setup  # noqa: F401
from hoppy import pet as cp

# memoria e proposte in una cartella temporanea
import pathlib, tempfile
tmp = pathlib.Path(tempfile.mkdtemp())
cp.MEM_PATH = tmp / "pet_memory.json"
cp.PROPOSALS_PATH = tmp / "pet_proposals.md"
cp.SESSIONS_PATH = tmp / "pet_sessions"

# ---- Brain: memoria, nome, fatti, feedback, umore, parse_tags ----
b = cp.Brain()
b.set_name("Ada"); b.remember("preferisce Python"); b.remember("preferisce Python")  # no dup
b.feedback("pausa", True); b.feedback("pausa", True); b.feedback("riposo", False)
assert b.name == "Ada", b.name
assert b.data["facts"] == ["preferisce Python"], b.data["facts"]
assert b.liked("pausa") == 2 and b.liked("riposo") == -1
m0 = b.mood; b.bump_mood(0.5); assert b.mood > m0
b.save()
b2 = cp.Brain()                                  # ricaricata da file
assert b2.name == "Ada" and b2.data["facts"] == ["preferisce Python"]
clean, name, facts = cp.Brain.parse_tags("Ciao!\nChe bello.\n#NOME: Luca\n#RICORDA: ama il caffè")
assert clean == "Ciao!\nChe bello." and name == "Luca" and facts == ["ama il caffè"], (clean, name, facts)
b2.forget_all(); assert b2.name == "" and not cp.MEM_PATH.exists()
print("Brain OK")

# ---- Pet con ask_claude finto: chat, consiglio con pollici, proposte ----
calls = []
def fake_ask(prompt, system, timeout=90):
    calls.append((prompt, system))
    if "SORGENTE" in prompt:
        return "- [ ] titolo: fai X\n- [ ] titolo2: fai Y", None
    if "consiglio" in prompt.lower() or "ti ha chiesto" in prompt.lower() or "proponi tu" in prompt.lower():
        return "Fai due passi e bevi un sorso d'acqua.", None
    return "Ciao, che piacere!\n#NOME: Gino\n#RICORDA: lavora a un sito", None
cp.ask_claude = fake_ask
cp.active_app = lambda pid: "idea64"
cp.cursor_pos = lambda: (600, 500)

root = tk.Tk(); root.withdraw()
pet = cp.Pet(root)

def drain(n=40):
    for _ in range(n):
        while not pet.think_q.empty():
            pet.on_thought(time.time(), *pet.think_q.get_nowait())
        root.update(); time.sleep(0.03)

# chat
pet.send_talk("ciao come stai")
drain()
assert pet.bubble and "piacere" in pet.bubble["full"], pet.bubble
assert pet.brain.name == "Gino" and any("sito" in f for f in pet.brain.data["facts"])
print("chat OK:", repr(pet.bubble["full"][:30]))

# consiglio + pollice su
pet.bubble = None
pet.give_advice(time.time(), spontaneous=False)
drain()
assert pet.bubble and pet.bubble["thumbs"] and pet.bubble["cat"], pet.bubble
cat = pet.bubble["cat"]
pet.bubble["shown"] = len(pet.bubble["full"])      # mostrato tutto
pet.on_thumb(True)
assert pet.brain.liked(cat) == 1, pet.brain.data
print("consiglio+feedback OK:", repr(pet.bubble["full"]))

# richiesta "cosa faccio adesso" -> consiglio
pet.bubble = None
pet.send_talk("cosa faccio adesso?")
drain()
assert pet.bubble and pet.bubble["thumbs"], pet.bubble
print("richiesta consiglio OK")

# proposte di codice -> file
pet.bubble = None
pet.propose_improvements(time.time(), auto=False)
drain()
assert cp.PROPOSALS_PATH.exists() and "fai X" in cp.PROPOSALS_PATH.read_text(encoding="utf-8")
print("proposte OK ->", cp.PROPOSALS_PATH.read_text(encoding='utf-8').strip().splitlines()[-2:])

# working_min e break-gap
now = time.time()
pet.work_since = now - 3600; pet.last_move = now
assert 59 <= pet.working_min(now) <= 61, pet.working_min(now)
pet.last_move = now - cp.BREAK_GAP_S - 10
assert pet.working_min(now) == 0
print("pause OK")
root.destroy()
print("TUTTO OK")
