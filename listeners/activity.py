import discord
from discord.ext import commands

class ThreadCounter:
    def __init__(self):
        self.count = 0

    async def initialize(self, bot):
        self.count = 0
        for guild in bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.ForumChannel):
                    self.count += len(channel.threads)
                    archived_threads = [thread async for thread in channel.archived_threads(limit=None)]
                    self.count += len(archived_threads)

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

thread_counter = ThreadCounter()

async def update_status(bot: commands.Bot):
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{thread_counter.count} Resources")
    await bot.change_presence(activity=activity)

async def handle_thread_create(thread: discord.Thread, bot: commands.Bot):
    if isinstance(thread.parent, discord.ForumChannel):
        thread_counter.increment()
        await update_status(bot)

async def handle_thread_delete(thread: discord.Thread, bot: commands.Bot):
    if isinstance(thread.parent, discord.ForumChannel):
        thread_counter.decrement()
        await update_status(bot)

async def setup_thread_counter(bot: commands.Bot):
    await thread_counter.initialize(bot)
    await update_status(bot)
