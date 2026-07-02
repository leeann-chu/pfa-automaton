# Original work Copyright (c) 2022 Ray Nieport

from discord.ext import commands, tasks
from os import path, getenv

BLOCKED_PHRASES = [
    "ThreadedAnvilChunkStorage",
    "minecraft:entity.experience_orb.pickup",
    "Generating keypair",
    "[net.minecraft.server.MinecraftServer/]",
    "Saving chunks for level"
]

class watchlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_path = getenv('MC_LOG_PATH', '/logs/latest.log')
        self.channel_id = int(getenv('DISCORD_CHANNEL_ID'))
        self.position_file = getenv('POSITION_FILE', '/logs/watchrat_position')
        self.last_size = self._load_position()

    def cog_unload(self):
        self.watchlog_task.cancel()

    def _load_position(self):
        try:
            with open(self.position_file, 'r') as f:
                return int(f.read().strip())
        except:
            # If file doesn't exist or can't be read, start from end of current log
            if path.exists(self.log_path):
                return path.getsize(self.log_path)
            return 0

    def _save_position(self, position):
        try:
            with open(self.position_file, 'w') as f:
                f.write(str(position))
        except Exception as e:
            print(f"Failed to save position: {e}")

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("watchrat is on standby")

    # Loop
    @tasks.loop(seconds=3)
    async def watchlog_task(self):
        # Check if log file exists yet (server may still be starting)
        if not path.exists(self.log_path):
            self.last_size = 0
            return

        current_size = path.getsize(self.log_path)

        # Log file was reset (server restarted)
        if current_size < self.last_size:
            print("Log file reset detected, starting from beginning")
            self.last_size = 0
            self._save_position(0)
            return  # skip this tick, pick up fresh next time

        # File hasn't changed
        if current_size == self.last_size:
            return

        with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(self.last_size)
            new_lines = f.readlines()

        self.last_size = current_size
        self._save_position(current_size)

        # Only process messages from the Minecraft server itself
        for line in new_lines:
            if any(phrase.lower() in message.lower() for phrase in BLOCKED_PHRASES):
                continue

            try: message = line.split("INFO]:", 1)[1]
            except Exception:
                try: message = line.split("]:", 1)[1]
                except Exception:
                    message = line

            message = message.strip()

            if not message:
                continue

            # Clean up RCON messages and replace bot's Discord ID with name
            if "[Rcon]" in message:
                message = message.replace("[Rcon]", "").strip()
                message = message.replace("254365116672245760", "elf")

            # Escape Discord markdown characters
            message = message.replace("_", "\\_").replace("*", "\\*")

            if "left the game" in message:
                message = "<:leave:974544401298763786>" + message

            if "joined the game" in message:
                message = "<:join:974544401319723008>" + message

            await self.bot.get_channel(self.channel_id).send(message)

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
                await ctx.send("Watchrat is no longer watching log")

async def setup(bot):
    await bot.add_cog(watchlog(bot))