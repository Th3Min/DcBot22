import asyncio
import discord
from discord import app_commands
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "DEIN_TOKEN_HIER")
GUILD_ID  = 1504924690156748931

async def sync():
    client = discord.Client(intents=discord.Intents.default())
    tree = app_commands.CommandTree(client)

    @tree.command(name="rang", description="Zeigt dein Level, Titel und XP an", guild=discord.Object(id=GUILD_ID))
    async def rang(interaction): pass

    @tree.command(name="top", description="Zeigt die Top-10 Rangliste", guild=discord.Object(id=GUILD_ID))
    async def top(interaction): pass

    @tree.command(name="xpinfo", description="Erklärt das XP-System und alle Titel", guild=discord.Object(id=GUILD_ID))
    async def xpinfo(interaction): pass

    await client.login(BOT_TOKEN)
    synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ {len(synced)} Commands registriert!")
    await client.close()

asyncio.run(sync())
