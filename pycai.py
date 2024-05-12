import nextcord
from nextcord.ext import commands
from PyCAI2 import PyAsyncCAI2

# PyCAI2 configuration
owner_id = '5f23e6c7f9edf45042a341303e2a67d9fcf7d96e'
char = "kn4yt4Es3fmPZqn6-x5uwryrOKNz3UFLEXWoa-hzZtI"
chat_id = "169bc002-16c4-4c45-91e6-90881392ba79"
token = "MTIzODUxMTQ0MzI2ODA3OTY5OQ.GIVfY9.20YTA_vI_9FfV89xASZvOGv2l6KgLz1jEfJ_-I"
client = PyAsyncCAI2(owner_id)

# Discord bot configuration
bot = commands.Bot(command_prefix="f!", intents=nextcord.Intents.all())
token_discord = "MTIzODUxMTQ0MzI2ODA3OTY5OQ.GIVfY9.20YTA_vI_9FfV89xASZvOGv2l6KgLz1jEfJ_-I"

# PyCAI enabled flag
pycai_enabled = True

# Allowed channel ID
allowed_channel_id = 1238511476302545017 #CHANGE ME BACK OR NO FEMBOYS!! :3


# Add event for PyCAI2
@bot.event
async def on_message(message):
    global pycai_enabled


    if message.channel.id == allowed_channel_id:
        print(f"{message.author.name}: {message.content}")
        if message.author == bot.user:
            return

        # Check if the message contains commands to disable or enable the bot
        if 'f!disable' in message.content or 'f!enable' in message.content:
            await bot.process_commands(message)
        # Check if the message contains the command to create a new chat
        elif 'f!rtv' in message.content:
            await bot.process_commands(message)
        # Check if the message contains the command to close the channel
        elif 'f!close' in message.content:
            await bot.process_commands(message)
        # Process normal messages if the bot is enabled
        elif pycai_enabled:
            await process_message(message)
        # Ignore messages if the bot is disabled
        else:
            return

# Function to handle messages
async def process_message(message):
    username = message.author.name
    response = await pycai(f"{username}: {message.content}")

    if any(bad_word in response for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
        await message.channel.send("I'm sorry, I'm not allowed to mention everyone, here")
        return
    
    await message.channel.send(response)

# Function to interact with PyCAI2
async def pycai(message):
    print("[PyCAI2] STARTING TO PROCESS MESSAGE")
    
    async with client.connect(owner_id) as chat2:
        r = await chat2.send_message(char, message, chat_id)

    if any(bad_word in r for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
        return "I'm sorry, I'm not allowed to mention everyone, here"

    print("[PyCAI2] Bot Message: ", r)
    return r


# Command to disable PyCAI
@bot.command()
async def disable(ctx):
    global pycai_enabled
    if ctx.author.id == authorized_user_id:
        if not pycai_enabled:
            await ctx.send("PyCAI is already disabled.")
        else:
            pycai_enabled = False
            await ctx.send("PyCAI has been disabled.")
    else:
        return

# Command to enable PyCAI
@bot.command()
async def enable(ctx):
    global pycai_enabled
    if ctx.author.id == authorized_user_id:
        pycai_enabled = True
        await ctx.send("PyCAI has been enabled.")
    else:
        return
    
# Command to reset chat
@bot.command()
async def rtv(ctx):
    async with client.connect(owner_id) as chat2:
        await chat2.new_chat("kn4yt4Es3fmPZqn6-x5uwryrOKNz3UFLEXWoa-hzZtI", with_greeting=False)

# Run the bot
bot.run(token_discord)
