from discord.ext import commands, tasks
from datetime import datetime, timedelta

from os import path
import time

class watchlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_checked = datetime.now()
        
    def cog_unload(self):
        self.watchlog_task.cancel()

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("watchlog is on standby")

    # Loop
    @tasks.loop(seconds=3)
    async def watchlog_task(self):
        modTimesinceEpoc = path.getmtime("../../pfaa/pfaa_server/logs/latest.log")
        modificationTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modTimesinceEpoc))
        date_time_obj = datetime.strptime(modificationTime, '%Y-%m-%d %H:%M:%S')

        if (self.last_checked - date_time_obj < timedelta(seconds=0)):
            self.last_checked = datetime.now()

            def readlastline(f):
                f.seek(-2,2)
                while f.read(1) != b"\n":
                    f.seek(-2, 1)
                return f.read().decode("utf-8") 

            with open('../../pfaa/pfaa_server/logs/latest.log', 'rb') as f:
                message = readlastline(f)
                try: message = message.split("INFO]:",1)[1]
                except Exception:
                    try: message = message.split("]:",1)[1]
                    except Exception: pass
                #Ignore messages with these words
                substrings = ["Rcon:", "Rcon connection", "weather", "UUID"]

                for sub in substrings:
                    if sub in message:
                        return

                if "left the game" in message:
                    message = "<:leave:974544401298763786>" + message

                if "joined the game" in message:
                    message = "<:join:974544401319723008>" + message
                
                await self.bot.get_channel(972937495476052009).send(message)

    @commands.is_owner()
    @commands.command()
    async def watch(self, ctx, enabled):
        if enabled == "start":
            if not self.watchlog_task.is_running():
                print("Beginning watch")
                self.watchlog_task.start()
        elif enabled == "stop":
            if self.watchlog_task.is_running():
                print("Ending watch")
                self.watchlog_task.cancel()
                await ctx.send("No longer watching log")

async def setup(bot): #Note to future me, this must be async and add_cog await
    await bot.add_cog(watchlog(bot))
