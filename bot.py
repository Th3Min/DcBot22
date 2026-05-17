import discord
from discord import app_commands
from discord.ext import commands
import os
import math
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import psycopg2
from psycopg2.extras import RealDictCursor

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "DEIN_TOKEN_HIER")
DATABASE_URL = os.environ.get("DATABASE_URL")
GUILD_ID   = 1504924690156748931
XP_MIN     = 15
XP_MAX     = 25
COOLDOWN_S = 20

LEVEL_COLORS = [
    0x3498db, 0x2ecc71, 0xe67e22, 0xe74c3c,
    0x9b59b6, 0x1abc9c, 0xf1c40f, 0xe91e63
]

MY_GUILD = discord.Object(id=GUILD_ID)

# ─────────────────────────────────────────────
#  KEEP ALIVE
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
    server = HTTPServer(("0.0.0.0", port), KeepAlive)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
_conn = None

def get_conn():
    global _conn
    try:
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(DATABASE_URL)
        _conn.isolation_level
    except Exception:
        _conn = psycopg2.connect(DATABASE_URL)
    return _conn

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    last_xp TIMESTAMP
                )
            """)
        conn.commit()

def get_user(user_id: str) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO users (user_id, xp, messages, last_xp) VALUES (%s, 0, 0, NULL)", (user_id,))
                conn.commit()
                return {"user_id": user_id, "xp": 0, "messages": 0, "last_xp": None}
            return dict(row)

def update_user(user_id: str, xp: int, messages: int, last_xp):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET xp = %s, messages = %s, last_xp = %s WHERE user_id = %s
            """, (xp, messages, last_xp, user_id))
        conn.commit()

def get_all_users():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users ORDER BY xp DESC")
            return [dict(r) for r in cur.fetchall()]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_title(level: int) -> str:
    if level < 10:
        return "🟢 Anfänger"
    elif level < 20:
        return "🔵 Smalltalker"
    elif level < 30:
        return "🔴 Aggressiv Hängengeblieben"
    else:
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
#  BOT
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    init_db()
    print(f"Bot eingeloggt als {bot.user}", flush=True)
    try:
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"✅ {len(synced)} Slash Commands synchronisiert!", flush=True)
    except Exception as e:
        print(f"❌ Sync Fehler: {e}", flush=True)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/top | XP Bot"
        )
    )

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    uid  = str(message.author.id)
    user = get_user(uid)
    now  = datetime.utcnow()

    new_msgs = user["messages"] + 1
    on_cooldown = False

    if user["last_xp"]:
        last = user["last_xp"]
        if isinstance(last, str):
            last = datetime.fromisoformat(last)
        if (now - last).total_seconds() < COOLDOWN_S:
            on_cooldown = True

    if on_cooldown:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET messages = %s WHERE user_id = %s", (new_msgs, uid))
            conn.commit()
        await bot.process_commands(message)
        return

    gained_xp = random.randint(XP_MIN, XP_MAX)
    old_level  = get_level(user["xp"])
    new_xp     = user["xp"] + gained_xp
    new_level  = get_level(new_xp)

    update_user(uid, new_xp, new_msgs, now)

    if new_level > old_level and get_title(new_level) != get_title(old_level):
        color = LEVEL_COLORS[new_level % len(LEVEL_COLORS)]
        title = get_title(new_level)
        embed = discord.Embed(
            title="🎖️ NEUER TITEL!",
            description=(
                f"**{message.author.display_name}** hat einen neuen Titel erreicht! 🎉\n\n"
                f"**{title}**\n\n"
                f"_(Level {new_level} erreicht)_"
            ),
            color=color
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=f"Gesamt-XP: {new_xp:,}")
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

# ─────────────────────────────────────────────
#  SLASH COMMANDS
# ─────────────────────────────────────────────
@bot.tree.command(name="rang", description="Zeigt dein Level, Titel und XP an", guild=MY_GUILD)
@app_commands.describe(mitglied="Anderes Mitglied anzeigen (optional)")
async def rang(interaction: discord.Interaction, mitglied: discord.Member = None):
    member = mitglied or interaction.user
    uid    = str(member.id)
    user   = get_user(uid)

    level      = get_level(user["xp"])
    current_xp = user["xp"] - total_xp_for_level(level)
    needed_xp  = xp_for_level(level)
    progress   = min(current_xp / needed_xp, 1.0)
    bar_len    = 20
    filled     = int(bar_len * progress)
    bar        = "█" * filled + "░" * (bar_len - filled)

    all_users = get_all_users()
    rank_pos  = next((i + 1 for i, u in enumerate(all_users) if u["user_id"] == uid), "?")

    color = LEVEL_COLORS[level % len(LEVEL_COLORS)]
    embed = discord.Embed(color=color)
    embed.set_author(name=f"{member.display_name} – Rang #{rank_pos}", icon_url=member.display_avatar.url)
    embed.add_field(name="🏆 Level",       value=f"**{level}**",             inline=True)
    embed.add_field(name="🎖️ Titel",       value=f"**{get_title(level)}**",  inline=True)
    embed.add_field(name="⚡ Gesamt-XP",   value=f"**{user['xp']:,}**",      inline=True)
    embed.add_field(name="💬 Nachrichten", value=f"**{user['messages']:,}**", inline=True)
    embed.add_field(
        name=f"Fortschritt  {current_xp:,} / {needed_xp:,} XP",
        value=f"`{bar}` {progress*100:.1f}%",
        inline=False
    )
    embed.set_footer(text=f"Noch {needed_xp - current_xp:,} XP bis Level {level+1}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="top", description="Zeigt die Top-10 Rangliste", guild=MY_GUILD)
@app_commands.describe(seite="Seite der Rangliste (Standard: 1)")
async def top(interaction: discord.Interaction, seite: int = 1):
    all_users = get_all_users()

    per_page = 10
    start    = (seite - 1) * per_page
    page     = all_users[start:start + per_page]
    total_p  = math.ceil(len(all_users) / per_page) or 1

    if not page:
        await interaction.response.send_message("Keine Daten auf dieser Seite.", ephemeral=True)
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
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="xpinfo", description="Erklärt das XP-System und alle Titel", guild=MY_GUILD)
async def xpinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ XP-System",
        color=0x3498db,
        description=(
            f"**XP pro Nachricht:** {XP_MIN}–{XP_MAX} (zufällig)\n"
            f"**Cooldown:** {COOLDOWN_S} Sekunden\n\n"
            "**Titel:**\n"
            "🟢 Level 1–9 → Anfänger\n"
            "🔵 Level 10–19 → Smalltalker\n"
            "🔴 Level 20–29 → Aggressiv Hängengeblieben\n"
            "💀 Level 30+ → Ultimativer Blindermann Hater\n\n"
            "**Commands:**\n"
            "`/rang [@mitglied]` – Dein Rang\n"
            "`/top [seite]` – Rangliste\n"
            "`/xpinfo` – Diese Info"
        )
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(BOT_TOKEN)
