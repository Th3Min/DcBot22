import discord
from discord.ext import commands
import json
import os
import math
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
#  CONFIG – hier anpassen
# ─────────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "DEIN_TOKEN_HIER")
PREFIX      = "!"
XP_MIN      = 15          # Minimum XP pro Nachricht
XP_MAX      = 25          # Maximum XP pro Nachricht
COOLDOWN_S  = 60          # Sekunden zwischen XP-Vergabe (Anti-Spam)
DATA_FILE   = "data.json"

# Farben für Level-Up Embeds
LEVEL_COLORS = [
    0x3498db, 0x2ecc71, 0xe67e22, 0xe74c3c,
    0x9b59b6, 0x1abc9c, 0xf1c40f, 0xe91e63
]

# Titel je nach Level-Range
def get_title(level: int) -> str:
    if level < 10:
        return "🟢 Anfänger"
    elif level < 20:
        return "🔵 Smalltalker"
    elif level < 30:
        return "🔴 Aggressiv Hängengeblieben"
    else:
        return "💀 Ultimativer Blindermann Hater"

# ─────────────────────────────────────────────
#  XP-FORMEL  (Level N braucht N*100 XP)
# ─────────────────────────────────────────────
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
#  JSON-DATEN
# ─────────────────────────────────────────────
def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(data: dict, user_id: str) -> dict:
    if user_id not in data:
        data[user_id] = {"xp": 0, "messages": 0, "last_xp": None}
    return data[user_id]

# ─────────────────────────────────────────────
#  BOT-SETUP
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅  {bot.user} ist online!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{PREFIX}top | XP Bot"
        )
    )

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    data    = load_data()
    uid     = str(message.author.id)
    user    = get_user(data, uid)
    now     = datetime.utcnow()

    # Cooldown-Check
    if user["last_xp"]:
        last = datetime.fromisoformat(user["last_xp"])
        if (now - last).total_seconds() < COOLDOWN_S:
            await bot.process_commands(message)
            return

    # XP vergeben
    gained_xp      = random.randint(XP_MIN, XP_MAX)
    old_level      = get_level(user["xp"])
    user["xp"]    += gained_xp
    user["messages"] += 1
    user["last_xp"] = now.isoformat()
    new_level      = get_level(user["xp"])
    save_data(data)

    # Level-Up?
    if new_level > old_level:
        color  = LEVEL_COLORS[new_level % len(LEVEL_COLORS)]
        needed = xp_for_level(new_level)
        title  = get_title(new_level)
        embed  = discord.Embed(
            title="⚡ LEVEL UP!",
            description=(
                f"**{message.author.display_name}** hat Level **{new_level}** erreicht! 🎉\n"
                f"Neuer Titel: **{title}**\n\n"
                f"Weiter so – das nächste Level braucht noch **{needed} XP**."
            ),
            color=color
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=f"Gesamt-XP: {user['xp']:,}")
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

# ─────────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────────
@bot.command(name="rank", aliases=["level", "xp"])
async def rank(ctx, member: discord.Member = None):
    """Zeigt dein aktuelles Level und XP an."""
    member = member or ctx.author
    data   = load_data()
    uid    = str(member.id)
    user   = get_user(data, uid)

    level      = get_level(user["xp"])
    current_xp = user["xp"] - total_xp_for_level(level)
    needed_xp  = xp_for_level(level)
    progress   = min(current_xp / needed_xp, 1.0)
    bar_len    = 20
    filled     = int(bar_len * progress)
    bar        = "█" * filled + "░" * (bar_len - filled)

    # Rang ermitteln
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("xp", 0), reverse=True)
    rank_pos     = next((i + 1 for i, (uid2, _) in enumerate(sorted_users) if uid2 == uid), "?")

    color = LEVEL_COLORS[level % len(LEVEL_COLORS)]
    embed = discord.Embed(color=color)
    embed.set_author(name=f"{member.display_name} – Rang #{rank_pos}", icon_url=member.display_avatar.url)
    embed.add_field(name="🏆 Level",        value=f"**{level}**",                    inline=True)
    embed.add_field(name="🎖️ Titel",        value=f"**{get_title(level)}**",         inline=True)
    embed.add_field(name="⚡ Gesamt-XP",    value=f"**{user['xp']:,}**",             inline=True)
    embed.add_field(name="💬 Nachrichten",  value=f"**{user['messages']:,}**",       inline=True)
    embed.add_field(
        name=f"Fortschritt  {current_xp:,} / {needed_xp:,} XP",
        value=f"`{bar}` {progress*100:.1f}%",
        inline=False
    )
    embed.set_footer(text=f"Noch {needed_xp - current_xp:,} XP bis Level {level+1}")
    await ctx.send(embed=embed)


@bot.command(name="top", aliases=["lb", "leaderboard"])
async def top(ctx, seite: int = 1):
    """Zeigt die Top-10 Rangliste."""
    data         = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("xp", 0), reverse=True)

    per_page = 10
    start    = (seite - 1) * per_page
    page     = sorted_users[start:start + per_page]
    total_p  = math.ceil(len(sorted_users) / per_page)

    if not page:
        await ctx.send("Keine Daten auf dieser Seite.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, (uid, udata) in enumerate(page):
        pos    = start + i + 1
        icon   = medals[pos - 1] if pos <= 3 else f"`#{pos}`"
        member = ctx.guild.get_member(int(uid))
        name   = member.display_name if member else f"User {uid[:6]}"
        level  = get_level(udata.get("xp", 0))
        lines.append(f"{icon} **{name}** — {get_title(level)} · Lvl {level} · {udata.get('xp',0):,} XP")

    embed = discord.Embed(
        title="🏆 XP Rangliste",
        description="\n".join(lines),
        color=0xf1c40f
    )
    embed.set_footer(text=f"Seite {seite}/{total_p}  •  {PREFIX}top <seite>")
    await ctx.send(embed=embed)


@bot.command(name="xpinfo")
async def xpinfo(ctx):
    """Erklärt das XP-System."""
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
            "**Level-Formel:**\n"
            "`XP für Level N = 5·N² + 50·N + 100`\n\n"
            "**Beispiele:**\n"
            f"Level 5 → {total_xp_for_level(5):,} XP gesamt\n"
            f"Level 10 → {total_xp_for_level(10):,} XP gesamt\n"
            f"Level 20 → {total_xp_for_level(20):,} XP gesamt\n\n"
            f"**Commands:**\n"
            f"`{PREFIX}rank [@user]` – Dein Rang\n"
            f"`{PREFIX}top [seite]` – Rangliste\n"
            f"`{PREFIX}xpinfo` – Diese Info"
        )
    )
    await ctx.send(embed=embed)


# ─────────────────────────────────────────────
#  START
# ─────────────────────────────────────────────
bot.run(BOT_TOKEN)
