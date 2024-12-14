import discord
from discord import app_commands
import config

async def check_existing_threads(channel: discord.ForumChannel):
    """
    Collect all threads (active and public archived) and group them by name.
    """
    existing_threads = {}

    # Get active threads
    active_threads = channel.threads

    # Fetch public archived threads
    public_archived = []
    async for thread in channel.archived_threads():  # Call the method here
        public_archived.append(thread)

    # Combine active and archived threads
    all_threads = active_threads + public_archived

    # Group threads by name
    for thread in all_threads:
        if thread.name not in existing_threads:
            existing_threads[thread.name] = []
        existing_threads[thread.name].append(thread)

    return existing_threads

async def has_required_role(member: discord.Member) -> bool:
    """
    Check if the member has the required role.
    """
    return any(role.id == config.REQUIRED_ROLE_ID for role in member.roles)

@app_commands.command(name="clearduplicate", description="Delete duplicate forum posts, keeping one.")
async def clearduplicate(interaction: discord.Interaction, channel: discord.ForumChannel):
    """
    Deletes duplicate threads in a specified forum channel, keeping one copy of each.
    """
    await interaction.response.defer(thinking=True)


    if not await has_required_role(interaction.user):
        await interaction.followup.send("You do not have permission to execute this command.")
        return


    if not isinstance(channel, discord.ForumChannel):
        await interaction.followup.send("The selected channel is not a forum channel.")
        return


    existing_threads = await check_existing_threads(channel)
    deleted_active = 0
    deleted_archived = 0

    for thread_name, threads in existing_threads.items():
        if len(threads) > 1:

            for thread_to_delete in threads[1:]:
                try:
                    await thread_to_delete.delete(reason="Duplicate thread deleted.")
                    if thread_to_delete.archived:
                        deleted_archived += 1
                    else:
                        deleted_active += 1
                    print(f"Deleted duplicate {'archived' if thread_to_delete.archived else 'active'} thread: {thread_to_delete.name}")
                except Exception as e:
                    print(f"Failed to delete thread {thread_to_delete.name}: {str(e)}")

    total_deleted = deleted_active + deleted_archived
    await interaction.followup.send(f"Duplicate threads have been cleared. Total deleted: {total_deleted} (Active: {deleted_active}, Archived: {deleted_archived}).")


def setup(bot):
    bot.tree.add_command(clearduplicate)
