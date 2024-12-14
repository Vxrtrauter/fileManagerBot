import discord
from discord import app_commands

@app_commands.command(name="closeposts", description="Close all posts in a forum channel")
@app_commands.describe(channel="forum channel where you want to close all posts.")
async def closeposts(interaction: discord.Interaction, channel: discord.ForumChannel):
    """Close all threads in the specified forum channel."""
    if not interaction.user.guild_permissions.manage_threads:
        await interaction.response.send_message("You do not have permission to close threads.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    closed_threads = 0
    failed_threads = 0

    for thread in channel.threads:
        try:
            await thread.edit(locked=True, archived=True)
            closed_threads += 1
            print(f"Closed thread: {thread.name} (ID: {thread.id})") 
        except Exception as e:
            failed_threads += 1
            print(f"Failed to close thread {thread.name} (ID: {thread.id}): {e}")

    await interaction.followup.send(
        f"Closed {closed_threads} threads in {channel.name}. {failed_threads} failed."
    )
