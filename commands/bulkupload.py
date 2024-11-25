import discord
from discord import app_commands
import aiohttp
import os
import config
import asyncio
from urllib.parse import unquote 

async def get_gofile_server():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.gofile.io/getServer') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['server']
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

async def scan_repository_for_jars(owner, repo_name):
    jar_files = []
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"

    async with aiohttp.ClientSession() as session:
        async def fetch_contents(url):
            async with session.get(url, headers={"Authorization": f"token {config.GITHUB_TOKEN}"}) as response:
                if response.status == 200:
                    contents = await response.json()
                    for item in contents:
                        if item['type'] == 'file' and item['name'].endswith('.jar'):
                            jar_files.append(item['download_url'])
                        elif item['type'] == 'dir':
                            # Recursively fetch contents of the directory
                            await fetch_contents(item['url'])

        await fetch_contents(api_url)
    
    return jar_files

async def check_existing_threads(channel):
    existing_threads = {}
    threads = channel.threads  

    for thread in threads:
        existing_threads[thread.name] = thread.id

    return existing_threads

async def has_required_role(member: discord.Member) -> bool:
    return any(role.id == config.REQUIRED_ROLE_ID for role in member.roles)

@app_commands.command(name="bulkupload", description="Upload all JAR files from a GitHub repository")
@app_commands.choices(category=[
    app_commands.Choice(name="Plugin", value="plugin"),
    app_commands.Choice(name="Client", value="client"),
    app_commands.Choice(name="Mod", value="mod"),
    app_commands.Choice(name="Resourcepack", value="resourcepack")
])
async def bulkupload(interaction: discord.Interaction, category: app_commands.Choice[str], repo_link: str):
    await interaction.response.defer(thinking=True)  


    if not await has_required_role(interaction.user):
        await interaction.followup.send("You do not have permission to execute this command.")
        return


    try:
        parts = repo_link.split('/')
        owner = parts[-2]
        repo_name = parts[-1].replace('.git', '')  
    except IndexError:
        await interaction.followup.send("Invalid GitHub repository link.")
        return


    jar_files = await scan_repository_for_jars(owner, repo_name)

    if not jar_files:
        await interaction.followup.send("No JAR files found in the repository.")
        return


    forum_channel_id = config.CHANNELS.get(category.value)
    forum_channel = interaction.guild.get_channel(forum_channel_id)

    if not forum_channel:
        await interaction.followup.send(f"Could not find forum channel for category: {category.value}")
        return

    existing_threads = await check_existing_threads(forum_channel)


    for jar_file_url in jar_files:
        jar_file_name = os.path.basename(unquote(jar_file_url))
        

        if jar_file_name in existing_threads:
            await interaction.followup.send(f"Skipped {jar_file_name}: already uploaded.")
            continue
        

        async with aiohttp.ClientSession() as session:
            jar_file_response = await session.get(jar_file_url)
            if jar_file_response.status == 200:
                jar_file_path = f"./{jar_file_name}"
                

                with open(jar_file_path, 'wb') as jar_file:
                    jar_file.write(await jar_file_response.read())
                
                try:

                    gofile_url = await upload_to_gofile(jar_file_path)

                    thread_name = os.path.splitext(jar_file_name)[0]
                    content = f"Download link: {gofile_url}" if gofile_url else "File uploaded to Discord only."
                    

                    with open(jar_file_path, 'rb') as file_to_send:
                        thread = await forum_channel.create_thread(name=thread_name, content=content, file=discord.File(file_to_send, filename=jar_file_name))


                    await interaction.followup.send(f"Uploaded {jar_file_name} successfully.")

                except Exception as e:
                    await interaction.followup.send(f"An error occurred while processing {jar_file_name}: {str(e)}")
                
                finally:

                    await asyncio.sleep(3)
            else:
                print(f"Failed to download {jar_file_name}: {jar_file_response.status}")
    
    try:
        await interaction.followup.send("All JAR files have been processed.")
    except discord.HTTPException as e:
        print(f"Failed to send follow-up message: {str(e)}")
