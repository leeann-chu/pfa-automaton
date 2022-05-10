from discord.ext import commands
from datetime import datetime, timedelta

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class OnMyWatch(FileSystemEventHandler):
    def __init__(self):
        self.observer = Observer()
        self.last_modified = datetime.now()

    def run(self):
        event_handler = OnMyWatch()
        self.observer.schedule(event_handler, "../../pfaa/pfaa_server/logs/", recursive = False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

    def on_modified(self, event):
        if datetime.now() - self.last_modified < timedelta(seconds=1):
            return
        else:
            self.last_modified = datetime.now()
            if not event.is_directory and event.src_path.endswith("latest.log"):
                def readlastline(f):
                    f.seek(-2,2)
                    while f.read(1) != b"\n":
                        f.seek(-2, 1)
                    return f.read().decode("utf-8") 

                with open('../../pfaa/pfaa_server/logs/latest.log', 'rb') as f:
                    print(readlastline(f))

class watchlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("watchlog is Ready")

    # Commands
    @commands.command()
    async def watch(self, ctx):
        watch = OnMyWatch()
        watch.run()

async def setup(bot): #Note to future me, must make this async and add_cog await
    await bot.add_cog(watchlog(bot))