import discord
from discord import app_commands
import aiohttp
import os
import config

async def get_gofile_server():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.gofile.io/servers') as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == 'ok' and data['data']['servers']:
                        return data['data']['servers'][0]['name']
    except Exception as e:
        print(f"Error getting GoFile server: {str(e)}")
    return None


async def upload_to_gofile(file_path):
    server = await get_gofile_server()
    if not server:
        return None

    url = f"https://{server}.gofile.io/uploadFile"
    
    try:
        with open(file_path, 'rb') as file:
            data = aiohttp.FormData()
            data.add_field('file', file, filename=file.name)
            data.add_field('token', config.GOFILE_API_KEY)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result['status'] == 'ok':
                            return result['data']['downloadPage']
    except Exception as e:
        print(f"Error uploading to GoFile: {str(e)}")
    return None

async def has_required_role(member: discord.Member) -> bool:
    return any(role.id == config.REQUIRED_ROLE_ID for role in member.roles)

@app_commands.command(name="upload", description="upload a file to GoFile and create a forum thread")
@app_commands.choices(category=[
    app_commands.Choice(name="plugin", value="plugin"),
    app_commands.Choice(name="client", value="client"),
    app_commands.Choice(name="mod", value="mod"),
    app_commands.Choice(name="resourcepack", value="resourcepack"),
    app_commands.Choice(name="client_mods", value="client_mods"),
    app_commands.Choice(name="plugin_src", value="plugin_src"),
    app_commands.Choice(name="client_src", value="client_src"),
    app_commands.Choice(name="other_mc_stuff", value="other_mc_stuff")
])
async def upload(interaction: discord.Interaction, category: app_commands.Choice[str], file: discord.Attachment):
    await interaction.response.defer()

    if not await has_required_role(interaction.user):
        await interaction.followup.send("You do not have permission to execute this command.")
        return

    file_path = f"{file.filename}"
    await file.save(file_path)

    try:
        gofile_url = await upload_to_gofile(file_path)

        forum_channel_id = config.CHANNELS.get(category.value)
        if not forum_channel_id:
            raise ValueError(f"Invalid category: {category.value}")

        forum_channel = interaction.guild.get_channel(forum_channel_id)
        if not forum_channel:
            raise ValueError(f"could not find forum channel: {category.value}")

        thread_name = os.path.splitext(file.filename)[0]
        content = f"Download link: {gofile_url}" if gofile_url else "File uploaded to Discord only"
        thread = await forum_channel.create_thread(name=thread_name, content=content, file=discord.File(file_path))

        await interaction.followup.send(f"file uploaded successfully.")

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
