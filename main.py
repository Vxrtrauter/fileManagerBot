import discord
from discord.ext import commands
import os
import config
from commands.upload import upload  
from commands.bulkupload import bulkupload  
from commands.clearduplicate import clearduplicate  
from commands.closeposts import closeposts
from listeners.activity import update_status, handle_thread_create, handle_thread_delete, ThreadCounter, setup_thread_counter

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  
bot = commands.Bot(command_prefix='?', intents=intents) 

thread_counter = ThreadCounter()

async def cleanup_jar_files():
    jar_files_deleted = 0
    for filename in os.listdir('.'): 
        if filename.endswith('.jar'):
            os.remove(filename)
            jar_files_deleted += 1
            print(f"Deleted JAR file: {filename}") 
    return jar_files_deleted

@bot.event
async def on_ready():
    print(f'{bot.user} connected to discord')
    
    deleted_count = await cleanup_jar_files()
    print(f"files have been cleaned. {deleted_count} jarfiles removed.")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    await setup_thread_counter(bot)  
    await update_status(bot) 

@bot.event
async def on_thread_create(thread):
    await handle_thread_create(thread, bot)  

@bot.event
async def on_thread_delete(thread):
    await handle_thread_delete(thread, bot)

bot.tree.add_command(upload)
bot.tree.add_command(bulkupload)
bot.tree.add_command(clearduplicate) 
bot.tree.add_command(closeposts)

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
