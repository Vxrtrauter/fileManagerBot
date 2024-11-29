import discord
from discord import app_commands
import aiohttp
import os
import config
import asyncio
from urllib.parse import unquote
import zipfile
import io
import requests
from requests.exceptions import RequestException

MAX_SIZE = 25 * 1024 * 1024


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

async def scan_repository_for_files(owner, repo_name, category):
    files = {}
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"
    
    async with aiohttp.ClientSession() as session:
        async def fetch_contents(url, current_path=""):
            async with session.get(url, headers={"Authorization": f"token {config.GITHUB_TOKEN}"}) as response:
                if response.status == 200:
                    contents = await response.json()
                    for item in contents:
                        if item['type'] == 'file':
                            if category in ['plugin', 'mod'] and item['name'].endswith('.jar'):
                                files[current_path] = files.get(current_path, []) + [item['download_url']]
                            elif category == 'client' and (item['name'].endswith('.jar') or item['name'].endswith('.json')):
                                files[current_path] = files.get(current_path, []) + [item['download_url']]
                            elif category == 'resourcepack' and item['name'].endswith('.zip'):
                                files[current_path] = files.get(current_path, []) + [item['download_url']]
                        elif item['type'] == 'dir':
                            await fetch_contents(item['url'], current_path + item['name'] + '/')
        
        await fetch_contents(api_url)
    return files

async def check_existing_threads(channel):
    existing_threads = {}
    threads = channel.threads
    for thread in threads:
        existing_threads[thread.name] = thread.id
    return existing_threads

async def has_required_role(member: discord.Member) -> bool:
    return any(role.id == config.REQUIRED_ROLE_ID for role in member.roles)

async def check_file_size(url):
    try:
        response = requests.head(url)
        file_size = int(response.headers.get('content-length', 0))
        return file_size
    except Exception as e:
        print(f"Error checking file size: {str(e)}")
    return None

async def download_file(url, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return response.content
        except RequestException as e:
            print(f"Error downloading file (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (attempt + 1))
            else:
                print(f"Failed to download file after {max_retries} attempts")
                return None

@app_commands.command(name="bulkupload", description="upload files from a GitHub repository based on category")
@app_commands.choices(category=[
    app_commands.Choice(name="plugin", value="plugin"),
    app_commands.Choice(name="client", value="client"),
    app_commands.Choice(name="mod", value="mod"),
    app_commands.Choice(name="resourcepack", value="resourcepack")
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

    files = await scan_repository_for_files(owner, repo_name, category.value)
    
    if not files:
        await interaction.followup.send(f"No {'JAR' if category.value != 'resourcepack' else 'ZIP'} files found in the repository.")
        return

    forum_channel_id = config.CHANNELS.get(category.value)
    forum_channel = interaction.guild.get_channel(forum_channel_id)
    
    if not forum_channel:
        await interaction.followup.send(f"Could not find forum channel for category: {category.value}")
        return

    existing_threads = await check_existing_threads(forum_channel)

    for folder_path, file_urls in files.items():
        folder_name = os.path.basename(folder_path.rstrip('/')) or repo_name
        thread_name = folder_name
        
        if thread_name in existing_threads:
            await interaction.followup.send(f"Skipped {thread_name}: already uploaded.")
            await asyncio.sleep(1)
            continue
        
        skip_folder = False
        folder_files = []
        
        for file_url in file_urls:
            file_size = await check_file_size(file_url)
            if file_size is None or file_size > MAX_SIZE:
                await interaction.followup.send(f"Skipped folder {folder_name}: File {os.path.basename(unquote(file_url))} exceeds 25 MB limit or size check failed.")
                skip_folder = True
                await asyncio.sleep(1)
                break
            
            file_name = os.path.basename(unquote(file_url))
            if f"{thread_name}/{file_name}" in existing_threads or file_name in existing_threads:
                await interaction.followup.send(f"Skipped {file_name}: already uploaded.")
                skip_folder = True
                await asyncio.sleep(1)
                break
            
            folder_files.append((file_url, file_size))
        
        if skip_folder:
            continue
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_url, _ in folder_files:
                file_name = os.path.basename(unquote(file_url))
                file_content = await download_file(file_url)
                
                if file_content is not None:
                    zip_file.writestr(file_name, file_content)
                else:
                    await interaction.followup.send(f"Failed to download {file_name} after multiple attempts. Skipping.")
                    continue
        
        zip_buffer.seek(0)
        upload_filename = f"{thread_name}.zip"
        
        try:
            gofile_url = await upload_to_gofile(zip_buffer)
            content = f"Download link: {gofile_url}" if gofile_url else "File uploaded to Discord only."
            file_to_send = discord.File(zip_buffer, filename=upload_filename)
            
            thread = await forum_channel.create_thread(name=thread_name, content=content, file=file_to_send)
            await interaction.followup.send(f"Uploaded {thread_name} successfully.")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred while processing {thread_name}: {str(e)}")
        
        finally:
            try:
                await interaction.followup.send("All files have been processed.")
            except discord.HTTPException as e:
                print(f"Failed to send follow-up message: {str(e)}")