import discord
from discord.ext import commands
from discord import app_commands
import os
import json

from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "✅ Bot läuft!"


def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
aufgabenlisten = {}

# 🔁 Beim Start Daten laden, falls vorhanden
def lade_aufgaben():
    global aufgabenlisten
    if os.path.exists("aufgaben.json"):
        with open("aufgaben.json", "r", encoding="utf-8") as f:
            aufgabenlisten = json.load(f)
        print("📂 Aufgaben aus Datei geladen.")
    else:
        print("📂 Keine vorhandene Aufgaben-Datei gefunden.")

lade_aufgaben()

# JSON einlesen beim Start
if os.path.exists("aufgaben.json"):
    with open("aufgaben.json", "r", encoding="utf-8") as f:
        aufgabenlisten = json.load(f)
        print("📂 Aufgaben aus aufgaben.json geladen.")


# Speichern der JSON
def speichere_aufgaben():
    with open("aufgaben.json", "w", encoding="utf-8") as f:
        json.dump(aufgabenlisten, f, indent=4, ensure_ascii=False)
        print("💾 Aufgaben gespeichert.")


emoji_zahlen = {
    "1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5,
    "6️⃣": 6, "7️⃣": 7, "8️⃣": 8, "9️⃣": 9, "🔟": 10
}


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands synchronisiert")
        print(f"✅ Bot ist online als {bot.user}")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Commands: {e}")


@bot.tree.command(name="backup_erstellen", description="Sichert die Listen als JSON-Datei.")
async def backup_erstellen(interaction: discord.Interaction):
    speichere_aufgaben()
    try:
        await interaction.user.send(file=discord.File("aufgaben.json"))
        await interaction.response.send_message("✅ Backup wurde dir per DM geschickt.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Ich konnte dir keine DM schicken. Prüfe deine Privatsphäre-Einstellungen.", ephemeral=True)


@bot.tree.command(name="liste_erstellen", description="Erstelle eine neue Aufgabenliste")
@app_commands.describe(name="Name der Liste")
async def liste_erstellen(interaction: discord.Interaction, name: str):
    if name in aufgabenlisten:
        await interaction.response.send_message("❗Diese Liste existiert schon.", ephemeral=True)
    else:
        aufgabenlisten[name] = {"tasks": []}
        speichere_aufgaben()
        await interaction.response.send_message(f"✅ Liste '{name}' wurde erstellt.", ephemeral=True)


@bot.tree.command(name="liste_hinzufuegen", description="Füge eine Aufgabe zu einer Liste hinzu")
@app_commands.describe(name="Name der Liste", aufgabe="Die Aufgabe, die hinzugefügt werden soll")
async def liste_hinzufuegen(interaction: discord.Interaction, name: str, aufgabe: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message("❗Diese Liste existiert nicht.", ephemeral=True)
        return
    if len(aufgabenlisten[name]["tasks"]) >= 10:
        await interaction.response.send_message("❗Maximal 10 Aufgaben pro Liste erlaubt.", ephemeral=True)
        return
    aufgabenlisten[name]["tasks"].append({"text": aufgabe, "done": False})
    speichere_aufgaben()
    await interaction.response.send_message(f"✅ Aufgabe hinzugefügt: {aufgabe}", ephemeral=True)


@bot.tree.command(name="liste_posten", description="Poste eine Liste im aktuellen Channel")
@app_commands.describe(name="Name der Liste")
async def liste_posten(interaction: discord.Interaction, name: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message("❗Diese Liste existiert nicht.", ephemeral=True)
        return
    liste = aufgabenlisten[name]
    description = ""
    for i, task in enumerate(liste["tasks"]):
        status = "✅" if task["done"] else "❌"
        zeile = f"{i+1}. {task['text']} {status}"
        if task.get("done") and "by" in task and task["by"]:
            zeile += f" (Erledigt von: {', '.join(task['by'])})"
        description += zeile + "\n"
    embed = discord.Embed(title=name, description=description or "Noch keine Aufgaben", color=0x00ff00)
    msg = await interaction.channel.send(embed=embed)
    for i in range(len(liste["tasks"])):
        emoji = list(emoji_zahlen.keys())[i]
        await msg.add_reaction(emoji)
    await interaction.response.send_message("📋 Liste gepostet.", ephemeral=True)


@bot.tree.command(name="liste_loeschen", description="Lösche eine vorhandene Aufgabenliste")
@app_commands.describe(name="Name der zu löschenden Liste")
async def liste_loeschen(interaction: discord.Interaction, name: str):
    if name not in aufgabenlisten:
        await interaction.response.send_message("❗Diese Liste existiert nicht.", ephemeral=True)
        return
    del aufgabenlisten[name]
    speichere_aufgaben()
    await interaction.response.send_message(f"🗑️ Liste '{name}' wurde gelöscht.", ephemeral=True)


@bot.tree.command(name="listen_anzeigen", description="Zeige alle gespeicherten Listen an")
async def listen_anzeigen(interaction: discord.Interaction):
    if not aufgabenlisten:
        await interaction.response.send_message("📋 Keine Listen gespeichert.", ephemeral=True)
        return
    description = ""
    for name, liste in aufgabenlisten.items():
        anzahl_aufgaben = len(liste["tasks"])
        erledigte_aufgaben = sum(1 for task in liste["tasks"] if task["done"])
        description += f"📋 **{name}** ({erledigte_aufgaben}/{anzahl_aufgaben} erledigt)\n"
        for i, task in enumerate(liste["tasks"][:3]):
            status = "✅" if task["done"] else "❌"
            description += f"  {i+1}. {task['text']} {status}\n"
        if len(liste["tasks"]) > 3:
            description += f"  ... und {len(liste['tasks']) - 3} weitere\n"
        description += "\n"
    embed = discord.Embed(title="📋 Alle gespeicherten Listen", description=description, color=0x0099ff)
    await interaction.response.send_message(embed=embed, ephemeral=True)


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
    if "by" not in task:
        task["by"] = []
    if member.display_name in task["by"]:
        return
    task["by"].append(member.display_name)
    task["done"] = True
    speichere_aufgaben()

    new_description = ""
    for i, t in enumerate(liste["tasks"]):
        status = "✅" if t["done"] else "❌"
        zeile = f"{i+1}. {t['text']} {status}"
        if t.get("done") and "by" in t and t["by"]:
            zeile += f" (Erledigt von: {', '.join(t['by'])})"
        new_description += zeile + "\n"
    new_embed = discord.Embed(title=title, description=new_description, color=0x00ff00)
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
    if "by" not in task or member.display_name not in task["by"]:
        return
    task["by"].remove(member.display_name)
    if not task["by"]:
        task["done"] = False
    speichere_aufgaben()

    new_description = ""
    for i, t in enumerate(liste["tasks"]):
        status = "✅" if t["done"] else "❌"
        zeile = f"{i+1}. {t['text']} {status}"
        if t.get("done") and "by" in t and t["by"]:
            zeile += f" (Erledigt von: {', '.join(t['by'])})"
        new_description += zeile + "\n"
    new_embed = discord.Embed(title=title, description=new_description, color=0x00ff00)
    try:
        await message.edit(embed=new_embed)
    except discord.HTTPException as e:
        print(f"⚠️ Konnte Nachricht nicht aktualisieren: {e}")


keep_alive()
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
