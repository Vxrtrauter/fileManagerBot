import discord
from discord.ext import commands
import os
import config
from commands.upload import upload  
from commands.bulkupload import bulkupload  
from commands.clearduplicate import clearduplicate  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents) 

async def cleanup_jar_files():
    jar_files_deleted = 0
    for filename in os.listdir('.'): 
        if filename.endswith('.jar'):
            os.remove(filename)
            jar_files_deleted += 1
            print(f"Deleted JAR file: {filename}") 
# this function will clean all jarfiles in the bots directory on startup. this may be removed in the future as i'm probably gonna update bulkupload.py to deleting the files automatically. 
    return jar_files_deleted

async def update_status():
    total_threads = sum(len(channel.threads) for channel in bot.get_all_channels() if isinstance(channel, discord.ForumChannel))
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{total_threads} Resources")
    await bot.change_presence(activity=activity) # this is the bot's activity and it counts the total threads on the server

@bot.event
async def on_ready():
    print(f'{bot.user} connected to discord')
    

    deleted_count = await cleanup_jar_files()
    print(f"files have been cleaned. {deleted_count} jarfiles removed. ") 
    
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

# register the commands
bot.tree.add_command(upload)
bot.tree.add_command(bulkupload)
bot.tree.add_command(clearduplicate) 

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)