import nextcord
import firebase_admin
from nextcord.ext import commands
from PyCAI2 import PyAsyncCAI2
from firebase_admin import credentials, firestore

# Set your bot's prefix
prefix = "/"

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

async def get_channel_id(command_name, channel_name):
    """Get the channel ID from Firestore."""
    channel_ref = db.collection("channel_ids").document(command_name)
    try:
        snapshot = channel_ref.get()
        if snapshot.exists:
            return snapshot.to_dict().get(channel_name)
        else:
            return None
    except Exception as e:
        print(f"Error getting channel ID: {e}")
        return None

async def set_channel_id(command_name, channel_name, channel_id):
    """Set the channel ID in Firestore."""
    channel_ref = db.collection("channel_ids").document(command_name)
    try:
        channel_ref.set({channel_name: channel_id})
    except Exception as e:
        print(f"Error setting channel ID: {e}")

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

public_channel_id = 1238511476302545017

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

# Add event for PyCAI2
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    username = message.author.name
    response = await pycai(f"{username}: {message.content}")

    if message.channel.id == public_channel_id:
        if any(bad_word in response for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
            await message.channel.send("I'm sorry, I'm not allowed to mention everyone, here")
            return

        await message.channel.send(response)
        return

# Function to interact with PyCAI2
async def pycai(message):

    print("[PyCAI2] STARTING TO PROCESS MESSAGE")
    print("MESSAGE:", message)
    
    async with client.connect(owner_id) as chat3:
        r = await chat3.send_message(char, message, chat_id)

    if any(bad_word in r for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
        return "I'm sorry, I'm not allowed to mention everyone, here"

    print("[PyCAI2] Bot Message: ", r)
    return r

# Command to disable PyCAI
@bot.slash_command(description="add later")
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
@bot.slash_command(description="add later")
async def enable(ctx):
    global pycai_enabled
    if await permission_check(ctx):
        pycai_enabled = True
        await ctx.send("PyCAI has been enabled.")
    else:
        return

# Command to reset chat
@bot.slash_command(description="add later")
async def rtv(ctx):
    if await permission_check(ctx):
        async with client.connect(owner_id) as chat2:
            await chat2.new_chat({get_cai_char_id}, with_greeting=False)

# Command to reset chat
@bot.slash_command(description="add later")
async def test(ctx):
    if await permission_check(ctx):
        await ctx.send("test success")

# Run the bot
if __name__ == "__main__":
    run_bot()