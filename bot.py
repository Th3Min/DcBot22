import discord
from discord import app_commands
from discord.ext import commands
import os
import math
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncpg
#    ___________.__    ________     _____  .__        
#    \__    ___/|  |__ \_____  \   /     \ |__| ____  
#      |    |   |  |  \  _(__  <  /  \ /  \|  |/    \ 
#      |    |   |   Y  \/       \/    Y    \  |   |  \
#      |____|   |___|  /______  /\____|__  /__|___|  /
#                    \/       \/         \/        \/ 

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "DEIN_TOKEN_HIER")
DATABASE_URL = os.environ.get("DATABASE_URL")
GUILD_ID     = 1504924690156748931
XP_MIN       = 15
XP_MAX       = 25
COOLDOWN_S   = 20   # Sekunden zwischen XP-Vergaben

LEVEL_COLORS = [
    0x3498db, 0x2ecc71, 0xe67e22, 0xe74c3c,
    0x9b59b6, 0x1abc9c, 0xf1c40f, 0xe91e63
]

MY_GUILD = discord.Object(id=GUILD_ID)

# ─────────────────────────────────────────────
#  KEEP ALIVE  (Railway braucht das nicht,
#  schadet aber auch nicht)
# ─────────────────────────────────────────────
class KeepAlive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), KeepAlive).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ─────────────────────────────────────────────
#  LEVEL / TITEL HELPERS
# ─────────────────────────────────────────────
def get_title(level: int) -> str:
    if level < 10:  return "🟢 Anfänger"
    if level < 20:  return "🔵 Smalltalker"
    if level < 30:  return "🔴 Aggressiv Hängengeblieben"
    return "💀 Ultimativer Blindermann Hater"

def xp_for_level(level: int) -> int:
    return 5 * (level ** 2) + 50 * level + 100

def total_xp_for_level(level: int) -> int:
    return sum(xp_for_level(l) for l in range(level))

def get_level(xp: int) -> int:
    level = 0
    while xp >= total_xp_for_level(level + 1):
        level += 1
    return level

# ─────────────────────────────────────────────
#  BOT SETUP
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
db: asyncpg.Pool = None
voice_join_times: dict = {}  # user_id -> datetime beim Voice-Join

# ─────────────────────────────────────────────
#  ON READY
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    global db
    if not DATABASE_URL:
        print("❌ FEHLER: DATABASE_URL ist nicht gesetzt!", flush=True)
        await bot.close()
        return

    try:
        db = await asyncpg.create_pool(DATABASE_URL)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       TEXT      PRIMARY KEY,
                xp            INTEGER   DEFAULT 0,
                messages      INTEGER   DEFAULT 0,
                last_xp       TIMESTAMP,
                voice_minutes INTEGER   DEFAULT 0
            )
        """)
        # Spalte nachrüsten falls DB schon existiert (ohne voice_minutes)
        await db.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_minutes INTEGER DEFAULT 0
        """)
        count = await db.fetchval("SELECT COUNT(*) FROM users")
        print(f"✅ DB verbunden – {count} User | XP-Cooldown={COOLDOWN_S}s", flush=True)
    except Exception as e:
        print(f"❌ DB Fehler: {e}", flush=True)
        await bot.close()
        return

    try:
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"✅ {len(synced)} Slash Commands synchronisiert!", flush=True)
    except Exception as e:
        print(f"❌ Sync Fehler: {e}", flush=True)

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="/top | XP Bot")
    )
    print(f"✅ Bot bereit als {bot.user}", flush=True)

# ─────────────────────────────────────────────
#  ON MESSAGE
#  Nachrichten:  IMMER zählen (kein Cooldown)
#  XP:           nur alle COOLDOWN_S Sekunden
# ─────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild or db is None:
        return

    uid = str(message.author.id)
    now = datetime.utcnow()

    # 1️⃣  Nutzer anlegen falls noch nicht vorhanden
    await db.execute("""
        INSERT INTO users (user_id, xp, messages, last_xp)
        VALUES ($1, 0, 0, NULL)
        ON CONFLICT (user_id) DO NOTHING
    """, uid)

    # 2️⃣  Nachricht IMMER zählen – komplett unabhängig vom XP-Cooldown
    await db.execute(
        "UPDATE users SET messages = messages + 1 WHERE user_id = $1",
        uid
    )

    # 3️⃣  XP-Cooldown prüfen
    last_xp = await db.fetchval("SELECT last_xp FROM users WHERE user_id = $1", uid)
    cooldown_aktiv = (
        last_xp is not None
        and (now - last_xp).total_seconds() < COOLDOWN_S
    )

    if not cooldown_aktiv:
        # 4️⃣  XP vergeben
        old_xp    = await db.fetchval("SELECT xp FROM users WHERE user_id = $1", uid)
        gained_xp = random.randint(XP_MIN, XP_MAX)
        new_xp    = old_xp + gained_xp
        old_level = get_level(old_xp)
        new_level = get_level(new_xp)

        await db.execute(
            "UPDATE users SET xp = $1, last_xp = $2 WHERE user_id = $3",
            new_xp, now, uid
        )

        # 5️⃣  Level-Up Nachricht
        if new_level > old_level:
            color = LEVEL_COLORS[new_level % len(LEVEL_COLORS)]
            titel_gewechselt = get_title(new_level) != get_title(old_level)

            if titel_gewechselt:
                # Neuer Titel → großes Embed
                embed = discord.Embed(
                    title="🎖️ NEUER TITEL!",
                    description=(
                        f"**{message.author.display_name}** hat einen neuen Titel erreicht! 🎉\n\n"
                        f"**{get_title(new_level)}**\n\n"
                        f"_(Level {new_level} erreicht)_"
                    ),
                    color=color
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.set_footer(text=f"Gesamt-XP: {new_xp:,}")
                await message.channel.send(embed=embed)
            else:
                # Level-Up ohne neuen Titel → kleine Nachricht
                embed = discord.Embed(
                    description=(
                        f"⬆️ **{message.author.display_name}** ist jetzt **Level {new_level}**! "
                        f"({get_title(new_level)})"
                    ),
                    color=color
                )
                await message.channel.send(embed=embed)

    await bot.process_commands(message)


# Text-Commands die mit ! getippt werden einfach ignorieren
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return


# ─────────────────────────────────────────────
#  ON VOICE STATE UPDATE
#  Trackt wie lange jemand im Voice war
# ─────────────────────────────────────────────
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot or db is None:
        return

    uid = str(member.id)
    now = datetime.utcnow()

    # Jemand joint einen Voice Channel (vorher keiner, jetzt einer)
    if before.channel is None and after.channel is not None:
        voice_join_times[uid] = now

    # Jemand verlässt einen Voice Channel (vorher einer, jetzt keiner)
    elif before.channel is not None and after.channel is None:
        if uid in voice_join_times:
            minutes = int((now - voice_join_times.pop(uid)).total_seconds() / 60)
            if minutes > 0:
                await db.execute("""
                    INSERT INTO users (user_id, xp, messages, last_xp, voice_minutes)
                    VALUES ($1, 0, 0, NULL, $2)
                    ON CONFLICT (user_id) DO UPDATE
                        SET voice_minutes = users.voice_minutes + $2
                """, uid, minutes)

# ─────────────────────────────────────────────
#  SLASH COMMAND: /rang
# ─────────────────────────────────────────────
@bot.tree.command(name="rang", description="Zeigt dein Level, Titel und XP an", guild=MY_GUILD)
@app_commands.describe(mitglied="Anderes Mitglied anzeigen (optional)")
async def rang(interaction: discord.Interaction, mitglied: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    member = mitglied or interaction.user
    uid    = str(member.id)

    user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", uid)
    if not user:
        user = {"xp": 0, "messages": 0}

    level      = get_level(user["xp"])
    current_xp = user["xp"] - total_xp_for_level(level)
    needed_xp  = xp_for_level(level)
    progress   = min(current_xp / needed_xp, 1.0)
    filled     = int(20 * progress)
    bar        = "█" * filled + "░" * (20 - filled)

    all_users = await db.fetch("SELECT user_id FROM users ORDER BY xp DESC")
    rank_pos  = next((i + 1 for i, u in enumerate(all_users) if u["user_id"] == uid), "?")

    color = LEVEL_COLORS[level % len(LEVEL_COLORS)]
    embed = discord.Embed(color=color)
    embed.set_author(
        name=f"{member.display_name} – Rang #{rank_pos}",
        icon_url=member.display_avatar.url
    )
    embed.add_field(name="🏆 Level",       value=f"**{level}**",             inline=True)
    embed.add_field(name="🎖️ Titel",       value=f"**{get_title(level)}**",  inline=True)
    embed.add_field(name="⚡ Gesamt-XP",   value=f"**{user['xp']:,}**",      inline=True)
    voice_min = user["voice_minutes"] if user.get("voice_minutes") is not None else 0
    stunden   = voice_min // 60
    minuten   = voice_min % 60
    voice_str = f"{stunden}h {minuten}m" if stunden > 0 else f"{minuten}m"
    embed.add_field(name="💬 Nachrichten", value=f"**{user['messages']:,}**", inline=True)
    embed.add_field(name="🎙️ Voice-Zeit",  value=f"**{voice_str}**",          inline=True)
    embed.add_field(
        name=f"Fortschritt  {current_xp:,} / {needed_xp:,} XP",
        value=f"`{bar}` {progress * 100:.1f}%",
        inline=False
    )
    embed.set_footer(text=f"Noch {needed_xp - current_xp:,} XP bis Level {level + 1}")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────
#  SLASH COMMAND: /top
# ─────────────────────────────────────────────
@bot.tree.command(name="top", description="Zeigt die Top-10 Rangliste", guild=MY_GUILD)
@app_commands.describe(seite="Seite der Rangliste (Standard: 1)")
async def top(interaction: discord.Interaction, seite: int = 1):
    await interaction.response.defer(ephemeral=True)
    all_users = await db.fetch("SELECT * FROM users ORDER BY xp DESC")

    per_page = 10
    start    = (seite - 1) * per_page
    page     = all_users[start:start + per_page]
    total_p  = math.ceil(len(all_users) / per_page) or 1

    if not page:
        await interaction.followup.send("Keine Daten auf dieser Seite.", ephemeral=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, udata in enumerate(page):
        pos    = start + i + 1
        icon   = medals[pos - 1] if pos <= 3 else f"`#{pos}`"
        member = interaction.guild.get_member(int(udata["user_id"]))
        name   = member.display_name if member else f"User {udata['user_id'][:6]}"
        level  = get_level(udata["xp"])
        lines.append(f"{icon} **{name}** — {get_title(level)} · Lvl {level} · {udata['xp']:,} XP")

    embed = discord.Embed(
        title="🏆 XP Rangliste",
        description="\n".join(lines),
        color=0xf1c40f
    )
    embed.set_footer(text=f"Seite {seite}/{total_p}  •  /top <seite>")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────
#  SLASH COMMAND: /xpinfo
# ─────────────────────────────────────────────
@bot.tree.command(name="xpinfo", description="Erklärt das XP-System und alle Titel", guild=MY_GUILD)
async def xpinfo(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="ℹ️ XP-System",
        color=0x3498db,
        description=(
            f"**XP pro Nachricht:** {XP_MIN}–{XP_MAX} (zufällig)\n"
            f"**XP-Cooldown:** {COOLDOWN_S} Sekunden\n"
            f"**Nachrichten:** werden immer gezählt (kein Cooldown)\n\n"
            "**Titel:**\n"
            "🟢 Level 1–9 → Anfänger\n"
            "🔵 Level 10–19 → Smalltalker\n"
            "🔴 Level 20–29 → Aggressiv Hängengeblieben\n"
            "💀 Level 30+ → Ultimativer Blindermann Hater\n\n"
            "**Commands:**\n"
            "`/rang [@mitglied]` – Dein Rang\n"
            "`/top [seite]` – Rangliste\n"
            "`/voicetop [seite]` – Voice-Zeit Rangliste\n"
            "`/msgtop [seite]` – Nachrichten Rangliste\n"
            "`/xpinfo` – Diese Info\n\n"
            "**Voice-Tracking:**\n"
            "Zeit im Voice Channel wird in `/rang` angezeigt (kein XP)"
        )
    )
    await interaction.followup.send(embed=embed, ephemeral=True)



# ─────────────────────────────────────────────
#  SLASH COMMAND: /voicetop
# ─────────────────────────────────────────────
@bot.tree.command(name="voicetop", description="Top-10 nach Voice-Zeit", guild=MY_GUILD)
@app_commands.describe(seite="Seite der Rangliste (Standard: 1)")
async def voicetop(interaction: discord.Interaction, seite: int = 1):
    await interaction.response.defer(ephemeral=True)
    all_users = await db.fetch("SELECT * FROM users ORDER BY voice_minutes DESC")

    per_page = 10
    start    = (seite - 1) * per_page
    page     = all_users[start:start + per_page]
    total_p  = math.ceil(len(all_users) / per_page) or 1

    if not page:
        await interaction.followup.send("Keine Daten auf dieser Seite.", ephemeral=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, udata in enumerate(page):
        pos    = start + i + 1
        icon   = medals[pos - 1] if pos <= 3 else f"`#{pos}`"
        member = interaction.guild.get_member(int(udata["user_id"]))
        name   = member.display_name if member else f"User {udata['user_id'][:6]}"
        vm     = udata["voice_minutes"] or 0
        h, m   = vm // 60, vm % 60
        zeit   = f"{h}h {m}m" if h > 0 else f"{m}m"
        lines.append(f"{icon} **{name}** — 🎙️ {zeit}")

    embed = discord.Embed(
        title="🎙️ Voice-Zeit Rangliste",
        description="\n".join(lines),
        color=0x9b59b6
    )
    embed.set_footer(text=f"Seite {seite}/{total_p}  •  /voicetop <seite>")
    await interaction.followup.send(embed=embed, ephemeral=True)


# ─────────────────────────────────────────────
#  SLASH COMMAND: /msgtop
# ─────────────────────────────────────────────
@bot.tree.command(name="msgtop", description="Top-10 nach Nachrichten", guild=MY_GUILD)
@app_commands.describe(seite="Seite der Rangliste (Standard: 1)")
async def msgtop(interaction: discord.Interaction, seite: int = 1):
    await interaction.response.defer(ephemeral=True)
    all_users = await db.fetch("SELECT * FROM users ORDER BY messages DESC")

    per_page = 10
    start    = (seite - 1) * per_page
    page     = all_users[start:start + per_page]
    total_p  = math.ceil(len(all_users) / per_page) or 1

    if not page:
        await interaction.followup.send("Keine Daten auf dieser Seite.", ephemeral=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, udata in enumerate(page):
        pos    = start + i + 1
        icon   = medals[pos - 1] if pos <= 3 else f"`#{pos}`"
        member = interaction.guild.get_member(int(udata["user_id"]))
        name   = member.display_name if member else f"User {udata['user_id'][:6]}"
        lines.append(f"{icon} **{name}** — 💬 {udata['messages']:,} Nachrichten")

    embed = discord.Embed(
        title="💬 Nachrichten Rangliste",
        description="\n".join(lines),
        color=0x2ecc71
    )
    embed.set_footer(text=f"Seite {seite}/{total_p}  •  /msgtop <seite>")
    await interaction.followup.send(embed=embed, ephemeral=True)

bot.run(BOT_TOKEN)
