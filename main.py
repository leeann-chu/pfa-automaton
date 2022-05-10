import discord
import traceback
from discord.ext import commands
import os
from rcon import rcon
from os import getenv
from dotenv import load_dotenv

intents = discord.Intents.all() 
intents.members = True 

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="p!", description="My prefix is p!", activity=discord.Activity(
    type=discord.ActivityType.watching, name="so much suffering"), intents=intents)
        self.initial_extensions = ['cogs.watchlog']

    async def setup_hook(self) -> None:
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self):
        await super().close()

    async def on_ready(self):
        print(f"Welcome {bot.user}")
        print("------------------------------")

bot = MyBot()

if __name__ == "__main__":
    # Get environment variables
    load_dotenv()
    TOKEN = getenv('DISCORD_TOKEN')
    USER_ROLE = getenv('DISCORD_USER_ROLE')
    MOD_ROLE = getenv('DISCORD_MOD_ROLE')
    ADMIN_ROLE = getenv('DISCORD_ADMIN_ROLE')
    IP = getenv('MINECRAFT_IP')
    PASS = getenv('MINECRAFT_PASS')
    PORT = getenv('RCON_PORT')
    BOT_LEVEL = getenv('BOT_LEVEL')
    if PORT == None: PORT = 25575
    else: PORT = int(PORT)
    if BOT_LEVEL == None: BOT_LEVEL = 1
    else: BOT_LEVEL = int(BOT_LEVEL) 

# Send command via rcon and print response
async def send_rcon(cmd, args, ctx):
    try:
        with rcon(IP, PASS, PORT) as mcr:
            if args:
                resp = mcr.command(f"{cmd} <{ctx.message.author.name}> {args}")
            else:
                resp = mcr.command(cmd)
    except: 
        resp = 'Connection from the bot to the server failed.'
        traceback.print_exc()

    if resp:
        await ctx.send(resp)
        print (f'{resp}')

#* Ping
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")
##

#* Some commands
@bot.command()
async def say(ctx, *, inp: str):
    await send_rcon("say", inp, ctx)
    # /say hello

@bot.command()
async def list(ctx):
    await send_rcon("list", None, ctx)

@bot.command(aliases=["wc"])
async def weather_clear(ctx):
    await send_rcon("weather clear", None, ctx)

@bot.command()
async def start(ctx):
    await ctx.send("Starting server...")
    os.system('./lunch_server.sh')

@bot.command()
async def stop(ctx):
    await ctx.send("Stopping server...")
    await send_rcon(stop, None, ctx)
##

bot.run(TOKEN)