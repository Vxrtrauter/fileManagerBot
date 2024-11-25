import discord
from discord import app_commands
import config

async def check_existing_threads(channel):
    existing_threads = {}
    threads = channel.threads

    for thread in threads:
        if thread.name not in existing_threads:
            existing_threads[thread.name] = []
        existing_threads[thread.name].append(thread)

    return existing_threads

async def has_required_role(member: discord.Member) -> bool:
    return any(role.id == config.REQUIRED_ROLE_ID for role in member.roles)

@app_commands.command(name="clearduplicate", description="Delete duplicate forum posts, keeping one.")
async def clearduplicate(interaction: discord.Interaction, channel: discord.ForumChannel):
    await interaction.response.defer(thinking=True) 


    if not await has_required_role(interaction.user):
        await interaction.followup.send("You do not have permission to execute this command.")
        return

    if not isinstance(channel, discord.ForumChannel):
        await interaction.followup.send("The selected channel is not a forum channel.")
        return

    existing_threads = await check_existing_threads(channel)
    
    deleted_count = 0
    
    for thread_name, threads in existing_threads.items():

        if len(threads) > 1:
 
            for thread_to_delete in threads[1:]:
                try:
                    await thread_to_delete.delete(reason="Duplicate thread deleted.")
                    deleted_count += 1 
                except Exception as e:
                    await interaction.followup.send(f"Failed to delete thread {thread_name}: {str(e)}")

    await interaction.followup.send(f"Duplicate threads have been cleared. Total deleted: {deleted_count}.")
