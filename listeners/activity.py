import discord
from discord.ext import commands

async def update_status(bot: commands.Bot):
    """update thread count on action"""
    total_threads = 0
    for channel in bot.get_all_channels():
        if isinstance(channel, discord.ForumChannel):
            active_threads = len(channel.threads)
            archived_threads = 0
            async for thread in channel.archived_threads(limit=None):
                archived_threads += 1
            total_threads += active_threads + archived_threads

    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{total_threads} Resources")
    await bot.change_presence(activity=activity)

async def handle_thread_create(thread: discord.Thread, bot: commands.Bot):
    """update activity on thread create"""
    if isinstance(thread.parent, discord.ForumChannel):
        await update_status(bot)

async def handle_thread_delete(thread: discord.Thread, bot: commands.Bot):
    """update activity on thread delete"""
    if isinstance(thread.parent, discord.ForumChannel):
        await update_status(bot)
