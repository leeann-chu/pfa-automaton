# Original work Copyright (c) 2022 Ray Nieport

import json

from discord.ext import commands, tasks
from os import path, getenv

MAX_CATCHUP_BYTES = 64 * 1024  # cap how much backlog we replay after a restart

class watchlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_path = getenv('MC_LOG_PATH', '/logs/latest.log')
        self.channel_id = int(getenv('DISCORD_CHANNEL_ID'))
        self.position_file = getenv('POSITION_FILE', '/logs/watchrat_position')
        self.blocked_phrases_file = getenv(
            'BLOCKED_PHRASES_FILE',
            '/home/watchrat/watchrat/blocked_phrases.json'
        )
        self.last_size = self._load_position()
        self.blocked_phrases = self._load_blocked_phrases()

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

    def _load_blocked_phrases(self):
        try:
            with open(self.blocked_phrases_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Failed to load blocked phrases: {e}")
            return []

    def _save_blocked_phrases(self):
        try:
            with open(self.blocked_phrases_file, 'w') as f:
                json.dump(self.blocked_phrases, f, indent=4)
        except Exception as e:
            print(f"Failed to save blocked phrases: {e}")

    def _get_current_size(self):
        """Returns current log size, or None if the log doesn't exist yet."""
        if not path.exists(self.log_path):
            self.last_size = 0
            return None
        return path.getsize(self.log_path)

    async def _handle_reset(self, current_size):
        """
        Detects a shrunk log file (server restart) and resets tracking.
        Returns True if a reset was handled (caller should bail out this tick).
        """
        if current_size >= self.last_size:
            return False

        await self.bot.get_channel(self.channel_id).send("Log file reset detected, starting from beginning")
        self.last_size = 0
        self._save_position(0)
        return True

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("watchrat is on standby")

    # Runs once before the loop's iteration 
    async def before_watchlog_task(self):
        current_size = self._get_current_size()
        if current_size is None:
            return

        gap = current_size - self.last_size

        if gap > MAX_CATCHUP_BYTES:
            await self.bot.get_channel(self.channel_id).send(
                f"Log backlog too large ({gap} bytes), skipping ahead"
            )
            self.last_size = current_size - MAX_CATCHUP_BYTES
            self._save_position(self.last_size)
        elif gap < 0:
            await self._handle_reset(current_size)

    # Loop
    @tasks.loop(seconds=3)
    async def watchlog_task(self):
        current_size = self._get_current_size()
        if current_size is None:
            return

        if await self._handle_reset(current_size):
            return  # skip this tick, pick up fresh next time

        if current_size == self.last_size:
            return

        with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(self.last_size)
            new_lines = f.readlines()

        self.last_size = current_size
        self._save_position(current_size)

        # Only process messages from the Minecraft server itself
        for line in new_lines:
            try: message = line.split("INFO]:", 1)[1]
            except Exception:
                try: message = line.split("]:", 1)[1]
                except Exception:
                    message = line

            message = message.strip()

            if not message:
                continue

            if any(phrase.lower() in message.lower() for phrase in self.blocked_phrases):
                continue

            if ": Gave " in message and " to " in message:
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
            
    watchlog_task.before_loop(before_watchlog_task)

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

    @commands.command()
    async def block(self, ctx, *, phrase):
        if phrase.lower() in (p.lower() for p in self.blocked_phrases):
            await ctx.send(f"'{phrase}' is already blocked.")
            return

        self.blocked_phrases.append(phrase)
        self._save_blocked_phrases()
        await ctx.send(f"Added '{phrase}' to blocked phrases.")

async def setup(bot):
    await bot.add_cog(watchlog(bot))