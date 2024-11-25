# main.py

import discord
from discord.ext import commands
import os
import config
from commands.upload import upload  
from commands.bulkupload import bulkupload  
from commands.clearduplicate import clearduplicate  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def cleanup_jar_files():
    """Delete all JAR files in the bot's directory."""
    jar_files_deleted = 0
    for filename in os.listdir('.'): 
        if filename.endswith('.jar'):
            os.remove(filename)
            jar_files_deleted += 1
            print(f"Deleted JAR file: {filename}") 

    return jar_files_deleted

async def update_status():
    total_threads = sum(len(channel.threads) for channel in bot.get_all_channels() if isinstance(channel, discord.ForumChannel))
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{total_threads} Resources")
    await bot.change_presence(activity=activity)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    

    deleted_count = await cleanup_jar_files()
    print(f"Cleanup complete. Deleted {deleted_count} JAR files.") 
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    await update_status()

@bot.event
async def on_thread_create(thread):
    if isinstance(thread.parent, discord.ForumChannel):
        await update_status()

@bot.event
async def on_thread_delete(thread):
    if isinstance(thread.parent, discord.ForumChannel):
        await update_status()


bot.tree.add_command(upload)
bot.tree.add_command(bulkupload)
bot.tree.add_command(clearduplicate) 

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)