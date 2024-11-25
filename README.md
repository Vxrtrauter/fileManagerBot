# fileManagerBot
FileManager Bot for the FarmerLibrary




## Base Functions:
- Upload Files to Threads
- Bulk-Upload files from GitHub to Threads
- Clear Threads with Duplicate Names


## Commands:
- /upload [filetype] [file] - uploads a file to the specified forum channel
- /bulkupload [filetype] [github repo] - pulls all jarfiles and uploads them
- /clearduplicate [channel] - clears all threads that have the same name

## Config:
The Config File contains a couple of Values:
- DISCORD_TOKEN - Your Discord Bot Token
- GOFILE_API_KEY - Your GoFile API Key
- GITHUB_TOKEN - Your GitHub Token
- REQUIRED_ROLE_ID - ID of the Role that gives perms to use Bot

### Channel Configs:
- Plugin - ID of your Plugin forum channel
- Client - ID of your Client forum channel
- Mod - ID of your Mod forum channel
- Resourcepack - ID of your Resourcepack forum channel

## Add new Commands:
### Main File: 
- In the Main file, import
’from commands.fileName import command’
- Above the Bot Login, add
bot.tree.add_command(command) 
- Make sure to replace commane and fileName with the correct command and fileName






