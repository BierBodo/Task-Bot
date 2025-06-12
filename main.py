import discord
from discord.ext import commands
from discord import app_commands
import os
import json  # NEU
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot läuft!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ✅ Bot-Intents aktivieren
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATEI = "aufgabenlisten.json"  # NEU

# Lade JSON falls vorhanden (oder leeres Dict)
if os.path.exists(DATEI):  # NEU
    with open(DATEI, "r", encoding="utf-8") as f:  # NEU
        aufgabenlisten = json.load(f)  # NEU
else:  # NEU
    aufgabenlisten = {}  # NEU


# Hilfsfunktion zum Speichern
def save_aufgabenlisten():  # NEU
    with open(DATEI, "w", encoding="utf-8") as f:  # NEU
        json.dump(aufgabenlisten, f, ensure_ascii=False, indent=4)  # NEU

# 1️⃣–🔟
emoji_zahlen = {
    "1️⃣": 1,
    "2️⃣": 2,
    "3️⃣": 3,
    "4️⃣": 4,
    "5️⃣": 5,
    "6️⃣": 6,
    "7️⃣": 7,
    "8️⃣": 8,
    "9️⃣": 9,
    "🔟": 10
}

# ✅ Bot online
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands synchronisiert")
        print(f"✅ Bot ist online als {bot.user}")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Commands: {e}")

# 📋 /liste_erstellen
@bot.tree.command(name="liste_erstellen",
                  description="Erstelle eine neue Aufgabenliste")
@app_commands.describe(name="Name der Liste")
async def liste_erstellen(interaction: discord.Interaction, name: str):
    if name in aufgabenlisten:
        await interaction.response.send_message(
            "❗Diese Liste existiert schon.", ephemeral=True)
    else:
        aufgabenlisten[name] = {"tasks": []}
        save_aufgabenlisten()  # NEU
        await interaction.response.send_message(
            f"✅ Liste '{name}' wurde erstellt.", ephemeral=True)

# ➕ /liste_hinzufuegen
@bot.tree.command(name="liste_hinzufuegen",
                  description="Füge eine Aufgabe zu einer Liste hinzu")
@app_commands.describe(name="Name der Liste",
                       aufgabe="Die Aufgabe, die hinzugefügt werden soll")
async def liste_hinzufuegen(interaction: discord.Interaction, name: str,
                            aufgabe: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message(
            "❗Diese Liste existiert nicht.", ephemeral=True)
        return
    if len(aufgabenlisten[name]["tasks"]) >= 10:
        await interaction.response.send_message(
            "❗Maximal 10 Aufgaben pro Liste erlaubt.", ephemeral=True)
        return
    aufgabenlisten[name]["tasks"].append({"text": aufgabe, "done": False})
    save_aufgabenlisten()  # NEU
    await interaction.response.send_message(
        f"✅ Aufgabe hinzugefügt: {aufgabe}", ephemeral=True)

# 📤 /liste_posten
@bot.tree.command(name="liste_posten",
                  description="Poste eine Liste im aktuellen Channel")
@app_commands.describe(name="Name der Liste")
async def liste_posten(interaction: discord.Interaction, name: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message(
            "❗Diese Liste existiert nicht.", ephemeral=True)
        return
    liste = aufgabenlisten[name]
    description = ""
    for i, task in enumerate(liste["tasks"]):
        status = "✅" if task["done"] else "❌"
        zeile = f"{i+1}. {task['text']} {status}"
        if task.get("done") and "by" in task and task["by"]:
            if len(task["by"]) == 1:
                zeile += f" (Erledigt von: {task['by'][0]})"
            else:
                zeile += f" (Erledigt von: {', '.join(task['by'])})"
        description += zeile + "\n"
    embed = discord.Embed(title=name,
                          description=description or "Noch keine Aufgaben",
                          color=0x00ff00)
    msg = await interaction.channel.send(embed=embed)
    for i in range(len(liste["tasks"])):
        emoji = list(emoji_zahlen.keys())[i]
        await msg.add_reaction(emoji)
    await interaction.response.send_message("📋 Liste gepostet.",
                                            ephemeral=True)

# ❌ /liste_loeschen
@bot.tree.command(name="liste_loeschen",
                  description="Lösche eine vorhandene Aufgabenliste")
@app_commands.describe(name="Name der zu löschenden Liste")
async def liste_loeschen(interaction: discord.Interaction, name: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message(
            "❗Diese Liste existiert nicht.", ephemeral=True)
        return

    del aufgabenlisten[name]
    save_aufgabenlisten()  # NEU
    await interaction.response.send_message(
        f"🗑️ Liste '{name}' wurde gelöscht.", ephemeral=True)

# 📝 /listen_anzeigen
@bot.tree.command(name="listen_anzeigen",
                  description="Zeige alle gespeicherten Listen an")
async def listen_anzeigen(interaction: discord.Interaction):
    if not aufgabenlisten:
        await interaction.response.send_message("📋 Keine Listen gespeichert.",
                                                ephemeral=True)
        return

    description = ""
    for name, liste in aufgabenlisten.items():
        anzahl_aufgaben = len(liste["tasks"])
        erledigte_aufgaben = sum(1 for task in liste["tasks"] if task["done"])
        description += f"📋 **{name}** ({erledigte_aufgaben}/{anzahl_aufgaben} erledigt)\n"

        # Zeige die ersten 3 Aufgaben als Vorschau
        for i, task in enumerate(liste["tasks"][:3]):
            status = "✅" if task["done"] else "❌"
            description += f"  {i+1}. {task['text']} {status}\n"

        if len(liste["tasks"]) > 3:
            description += f"  ... und {len(liste['tasks']) - 3} weitere\n"
        description += "\n"

    embed = discord.Embed(title="📋 Alle gespeicherten Listen",
                          description=description,
                          color=0x0099ff)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 🔄 Reaktionen auswerten
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title

    if title not in aufgabenlisten:
        return

    emoji = str(payload.emoji)
    if emoji not in emoji_zahlen:
        return

    index = emoji_zahlen[emoji] - 1
    liste = aufgabenlisten[title]

    if index >= len(liste["tasks"]):
        return

    task = liste["tasks"][index]

    # Initialisiere Liste der Personen, falls nicht vorhanden
    if "by" not in task:
        task["by"] = []

    # Prüfe, ob Person bereits abgehakt hat
    if member.display_name in task["by"]:
        return  # Person hat bereits abgehakt

    # Person zur Liste hinzufügen
    task["by"].append(member.display_name)
    task["done"] = True  # Aufgabe als erledigt markieren

    save_aufgabenlisten()  # NEU

    # Embed aktualisieren
    new_description = ""
    for i, t in enumerate(liste["tasks"]):
        status = "✅" if t["done"] else "❌"
        zeile = f"{i+1}. {t['text']} {status}"
        if t.get("done") and "by" in t and t["by"]:
            if len(t["by"]) == 1:
                zeile += f" (Erledigt von: {t['by'][0]})"
            else:
                zeile += f" (Erledigt von: {', '.join(t['by'])})"
        new_description += zeile + "\n"

    new_embed = discord.Embed(title=title,
                              description=new_description,
                              color=0x00ff00)
    await message.edit(embed=new_embed)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title

    if title not in aufgabenlisten:
        return

    emoji = str(payload.emoji)
    if emoji not in emoji_zahlen:
        return

    index = emoji_zahlen[emoji] - 1
    liste = aufgabenlisten[title]

    if index >= len(liste["tasks"]):
        return

    task = liste["tasks"][index]

    # Prüfe ob Person in der Liste ist
    if "by" not in task or member.display_name not in task["by"]:
        return  # Person hat nicht abgehakt

    # Person aus der Liste entfernen
    task["by"].remove(member.display_name)

    # Wenn niemand mehr abgehakt hat, Aufgabe als nicht erledigt markieren
    if not task["by"]:
        task["done"] = False

    save_aufgabenlisten()  # NEU

    # Embed aktualisieren
    new_description = ""
    for i, t in enumerate(liste["tasks"]):
        status = "✅" if t["done"] else "❌"
        zeile = f"{i+1}. {t['text']} {status}"
        if t.get("done") and "by" in t and t["by"]:
            if len(t["by"]) == 1:
                zeile += f" (Erledigt von: {t['by'][0]})"
            else:
                zeile += f" (Erledigt von: {', '.join(t['by'])})"
        new_description += zeile + "\n"

    new_embed = discord.Embed(title=title,
                              description=new_description,
                              color=0x00ff00)
    await message.edit(embed=new_embed)


keep_alive()

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
