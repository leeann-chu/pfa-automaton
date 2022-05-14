import discord
import traceback
from discord.ext import commands
import os, time
from rcon import rcon
from os import getenv
from dotenv import load_dotenv
import random

intents = discord.Intents.all() 
intents.members = True 

emoji_list = [":face_with_spiral_eyes:", ":japanese_goblin:", ":pleading_face:", 
":confounded:", ":weary:", "<:splat:860541072102916136>", "<:jeb:518667017868410910>",
"<:kirby:561033037521879069>", "<:doggo:399389492508622848>", "<:troll_moderate:839717983429460008>"]

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="p!", description="My prefix is p!", status=discord.Status.dnd, activity=discord.Activity(
            type=discord.ActivityType.listening, name="Crickets"), intents=intents)
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
bot.remove_command('help')

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
            
            if resp:
                if "/help" not in resp:
                    await ctx.send(f'`{resp}`')
                    print (f'{resp}')
            return True

    except: 
        resp = 'Connection from the bot to the server failed.'
        traceback.print_exc()
        #await ctx.send(resp)
        return False

#* Ping
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")
##

#* Ping
@bot.command()
async def help(ctx):
    p = ctx.prefix
    await check(ctx)
    embed = discord.Embed(
        title="Help Menu",
        description=
        f"""__Commands__
        `{p}help` ➙ Brings up this menu
        `{p}say <message>` ➙ Send a message to the server
        `{p}list` ➙ Lists the players online
        `{p}wc` ➙ Clears the weather

        `{p}start` ➙ Starts the server
        `{p}stop` ➙ Stops the server
        `{p}check` ➙ Checks if the server is online
        
        """
    )
    await ctx.send(embed=embed)             
##

#* Some commands
@bot.command()
async def say(ctx, *, inp: str):
    await send_rcon("say", inp, ctx)

@say.error
async def say_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'inp':
            await ctx.send("You forgot to give me a message to send!")

@bot.command(aliases=["list"])
async def _list(ctx):
    await send_rcon("list", None, ctx)

@bot.command(aliases=["wc"])
async def weather_clear(ctx):
    await send_rcon("weather clear", None, ctx)

@bot.command()
async def start(ctx):
    server_on = await check(ctx, False)
    if not server_on:
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="over Promenade of Progress"))
        await ctx.send("Starting server...")
        os.system('./lunch_server.sh')
        time.sleep(250)
        await check(ctx)
    else: 
        await ctx.send(f"Server is already online! {random.choice(emoji_list)}")

@bot.command()
async def stop(ctx):
    server_on = await check(ctx, False)
    if server_on:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.listening, name="Crickets"))
        await send_rcon("stop", None, ctx)
        time.sleep(10)
        await check(ctx)
    else: 
        await ctx.send(f"Server is already dead! {random.choice(emoji_list)}")
##

@bot.command(aliases=["c", "status"])
async def check(ctx, verbose=True):
    statusBool = await send_rcon("ping", None, ctx)
    status = ":white_check_mark: **Server is Online**" if statusBool else ":octagonal_sign: **Server is Offline**"
    if statusBool:
        await bot.get_command("watch")(ctx, "start")
    else:
        await bot.get_command("watch")(ctx, "stop")
    if verbose:
        await ctx.send(status)
    return statusBool

@bot.command()
async def update(ctx):
    status = await check(ctx)
    if status:
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="over Promenade of Progress"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.listening, name="Crickets"))
bot.run(TOKEN)