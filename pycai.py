import nextcord
import firebase_admin
from nextcord.ext import commands
from PyCAI2 import PyAsyncCAI2
from firebase_admin import credentials, firestore
from enum import Enum

prefix = "f!"

# Create a bot instance with a command prefix
intents = nextcord.Intents.all()
intents.messages = True
intents.message_content = True  # Enable MESSAGE_CONTENT intent
bot = commands.Bot(command_prefix=prefix, intents=intents)

# Initialize Firebase
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Function to check what roles are allowed to run commands
async def get_allowed_roles():
    """Retrieve allowed roles from Firestore."""
    allowed_roles = {}

    try:
        doc_ref = db.collection('role_names').document('allowed_commands')
        doc = doc_ref.get()  # Remove 'await' from here
        if doc.exists:
            data = doc.to_dict()
            allowed_roles = {role_name: allow for role_name, allow in data.items()}  # Get the dictionary of allowed roles
    except Exception as e:
        print(f"Error fetching allowed roles: {e}")

    return allowed_roles

# Function to check the user for permissions to run the command
async def permission_check(ctx):
    """Check permissions for executing commands."""
    allowed_roles = await get_allowed_roles()  # Await the asynchronous operation

    # Get the names of the roles the user has
    user_role_names = [role.name for role in ctx.user.roles]

    # Check if any of the user's roles are allowed
    for role_name in user_role_names:
        if role_name in allowed_roles and allowed_roles[role_name]:
            return True

    # If none of the user's roles match the allowed roles or if the roles are not allowed
    await ctx.send("You do not have permission to use this command.")
    return False

# Function to get the bot token from Firestore
def get_bot_token():
    # Assuming the personal access token is stored in a document named 'bot_token'
    token_ref = db.collection("secrets").document("bot_token")
    token_doc = token_ref.get()
    if token_doc.exists:
        return token_doc.to_dict().get("token")
    else:
        return None

# Function to fetch c.ai API key from Firestore
def get_cai_owner_id():
    doc_ref = db.collection("secrets").document("c.ai_ownerid")
    doc = doc_ref.get()
    return doc.to_dict()["id"]

# Function to fetch c.ai API key from Firestore
def get_cai_char_id():
    doc_ref = db.collection("secrets").document("c.ai_charid")
    doc = doc_ref.get()
    return doc.to_dict()["id"]

# Function to fetch c.ai API key from Firestore
def get_cai_chat_id():
    doc_ref = db.collection("secrets").document("c.ai_chatid")
    doc = doc_ref.get()
    return doc.to_dict()["id"]

# Initialize PyCAI2 variables
owner_id = get_cai_owner_id()
char = get_cai_char_id()
chat_id = get_cai_chat_id()

client = PyAsyncCAI2(owner_id)

# Function to start the bot
def run_bot():
    # Get the personal access token from Firestore
    token = get_bot_token()
    if token:
        # Initialize the bot with the token
        bot.run(token)
    else:
        print("Failed to retrieve Firebase personal access token.")

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} is now online')
    await bot.change_presence(status=nextcord.Status.online)

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

async def set_setting(setting_name, setting_value):
    setting_ref = db.collection("command_configuration").document(setting_name)
    if isinstance(setting_value, bool):
        setting_ref.set({"value": setting_value})
    else:
        setting_ref.set({"value": setting_value})

# Command to disable PyCAI
@bot.command()
async def disable(ctx):
    global pycai_enabled
    if await permission_check(ctx):
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
    if await permission_check(ctx):
        pycai_enabled = True
        await ctx.send("PyCAI has been enabled.")
    else:
        return
    
# Command to reset chat
@bot.command()
async def rtv(ctx):
    async with client.connect(owner_id) as chat2:
        await chat2.new_chat({get_cai_char_id}, with_greeting=False)

# Run the bot
if __name__ == "__main__":
    run_bot()