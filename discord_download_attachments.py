
import os 
import datetime
import discord # Discord API
from dotenv import load_dotenv # ENV vars
# by Jakub Grzana

# Simple Python script to download all attachments from your server using Discord Bot API
# Requirements:
#   Python 3.9.0
#   Discord API for python 1.6.0 (REQUIRES DISCORD_TOKEN)
#   python-dotenv 0.15.0


load_dotenv() # load environmental variables from file .env
DiscordClient = discord.Client()

def EnsureDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Program connects to Discord Client (bot)
# then asks you to choose one of connected guilds
# then scans all text channels (requresting history - this requires priviledge!)
# if it finds any attachment, it adds into "attachments" dict() in format attachments[path] = attachment
# After all channels are scanned and all attachments have been found, it downloads them, giving feedback in given interval

verbose_scanning = 1000
verbose_downloading = 100 
# year, month, day
after_date = datetime.datetime(2021,5,2)
before_date = datetime.datetime(2021,5,30)

async def Download(client, guild, after, before):
    print("Selected guild: " + guild.name)
    print("Process has started. Gathering attachments")
    attachments = dict()
    EnsureDir(guild.name)
    for channel in guild.text_channels:
        EnsureDir(guild.name+"/"+channel.name)
        print("Scanning channel: " + channel.name)
        try:
            async for message in channel.history(limit=None, after=after, before=before):
                for attached in message.attachments:
                    path = guild.name + "/" + channel.name + "/" + attached.filename
                    # dealing with multiple files with the same name
                    (path_and_filename, extension) = os.path.splitext(path)
                    edited_path = path_and_filename
                    ind = 0
                    while (edited_path+extension) in attachments:
                        ind = ind + 1
                        edited_path = path_and_filename + "_" + str(ind)
                    path = edited_path + extension
                    # adding to attachments dictionary
                    attachments[path] = attached
        except Exception as e:
            print("Error: " + str(e))
            print("Ommiting channel " + channel.name)

    num = len(attachments)
    print("Attachments gathered: " + str( num ) )
    print("Downloading... ")
    i = 0
    for path in attachments:
        if (i % verbose_downloading) == 0:
            print("Saving " + str(i+1) + "/" + str(num))
        attached = attachments[path]
        await attached.save(path)
        i = i + 1

################################ INITIALISATION ################################

@DiscordClient.event
async def on_ready():
    print("Initialisation finished")
    print(f'{DiscordClient.user} has connected to Discord!')
    print("Number of servers (guilds) bot is connected to: "+str(len(DiscordClient.guilds)))
    print("")
    print("Select guild you want to download pictures from: ")
    for i in range(len(DiscordClient.guilds)):
        print(str(i) + " - " + DiscordClient.guilds[i].name )
    ind = int(input("$ "))
    guild = DiscordClient.guilds[ind]
    print("\n")
    
    await Download(DiscordClient, guild, after_date, before_date)
    
    print("\n\n")
    print("Done. Please shutdown this terminal now")

if __name__ == '__main__':
    print("Startup finished. Connecting...")
    DiscordClient.run(os.getenv('DISCORD_TOKEN'))