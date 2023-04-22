import discord
from discord.ext import commands
import json

masterPointsJson = "masterpoints.json"
logsJson = "logs.json"

mediaTypes = {"anime", "vn", "ln", "reading", "listening"}
pointSystem = {"anime" : 3100, "vn" : 1, "ln" : 1, "reading" : 1, "listening" : 660}

with open ("config.json", "r") as f:
    config = json.load(f)

client = commands.Bot(command_prefix="i$", intents=discord.Intents.all())
client.intents.message_content = True

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.load_extension("loggingSystem.LoggingSystem")

# @client.event
# async def on_message(message):
#     author = message.author
#     authorId = str(author.id)
#     messageString = message.content
#     if author == client.user:
#         return
#     await message.channel.send("FUCK OFF")

@client.command()
async def reload(ctx):
    await client.reload_extension("loggingSystem.LoggingSystem")
    await ctx.send("I have coldly recompiled the cogs.")
    return

client.run(config["token"])