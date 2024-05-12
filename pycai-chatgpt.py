import nextcord
import firebase_admin
from nextcord.ext import commands
from PyCAI2 import PyAsyncCAI2
from firebase_admin import credentials, firestore

# Create a bot instance
prefix = "/"
intents = nextcord.Intents.all()
intents.messages = True
intents.message_content = True
intents.reactions = True  # Enable reactions intent
bot = commands.Bot(command_prefix=prefix, intents=intents)

# Initialize Firebase
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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

# Function to interact with PyCAI2
async def pycai(message):

    print("[PyCAI2] STARTING TO PROCESS MESSAGE")
    print("MESSAGE:", message)
    
    async with client.connect(owner_id) as chat2:
        r = await chat2.send_message(char, message, chat_id)

    if any(bad_word in r for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
        return "I'm sorry, I'm not allowed to mention everyone, here"

    print("[PyCAI2] Bot Message: ", r)
    return r

# Function to fetch available character IDs from Firestore
async def get_available_character_ids():
    """Retrieve available character IDs from Firestore."""
    available_ids = []

    try:
        collection_ref = db.collection('character_ids')
        docs = await collection_ref.get()  # Asynchronous operation
        for doc in docs:
            data = doc.to_dict()
            # Check if the "used" field is False
            if not data.get("used", False):
                available_ids.append(data.get("id"))
    except Exception as e:
        print(f"Error fetching available character IDs: {e}")

    return available_ids

# Function to check if a character ID is already used
async def is_character_id_used(char_id):
    """Check if a character ID is already used."""
    try:
        doc_ref = db.collection("character_ids").where("id", "==", char_id)
        docs = await doc_ref.get()
        for doc in docs:
            data = doc.to_dict()
            return data.get("used", False)
    except Exception as e:
        print(f"Error checking if character ID is used: {e}")
        return True

# Function to update the "used" field of a character ID
async def set_character_id_used(char_id, value):
    """Update the 'used' field of a character ID."""
    try:
        doc_ref = db.collection("character_ids").where("id", "==", char_id)
        docs = await doc_ref.get()
        for doc in docs:
            doc.reference.update({"used": value})
    except Exception as e:
        print(f"Error setting character ID used: {e}")

# Function to start a new chat using the retrieved character ID and Discord channel ID
async def start_new_chat(char_id, channel_id):
    """Start a new chat using the retrieved character ID and Discord channel ID."""
    try:
        async with client.connect(owner_id) as chat2:
            await chat2.new_chat(char_id, channel_id, with_greeting=False)
    except Exception as e:
        print(f"Error starting new chat: {e}")

# Initialize PyCAI2 variables
owner_id = get_cai_owner_id()
char = get_cai_char_id()
chat_id = get_cai_chat_id()
client = PyAsyncCAI2(owner_id)
public_channel_id = 1238511476302545017
ticket_category = 1239338386582671440
react_channel = 1239335417522815006
react_message = 1239338821842374709
react_emoji = "🌸"

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
    print("Bot is now online")
    channel = bot.get_channel(react_channel)
    if channel:
        print(f"Channel found: {channel.name}")
        message = await channel.fetch_message(react_message)
        if message:
            print(f"Message found: {message.content}")
            if react_emoji not in [reaction.emoji for reaction in message.reactions]:
                print(f"Reacting to the message with {react_emoji}")
                await message.add_reaction(react_emoji)
        else:
            print("Message not found")
    else:
        print("Channel not found")

# Event: When bot gets message
@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != public_channel_id:
        return

    username = message.author.name
    response = await pycai(f"{username}: {message.content}")

    if message.channel.id == public_channel_id:
        if any(bad_word in response for bad_word in ["@everyone", "@here", "<@&1182758208922714133>"]):
            await message.channel.send("I'm sorry, I'm not allowed to mention everyone, here")
            return

        await message.channel.send(response)
        return

# Function to get the reaction channel and message IDs
def get_reaction_ids():
    # Replace these with your actual channel and message IDs
    return 1239335417522815006, 1239338821842374709

# Function to react to the specified message
async def react_to_message():
    # Get the reaction channel and message IDs
    channel_id, message_id = get_reaction_ids()
    channel = bot.get_channel(channel_id)
    if channel:
        message = await channel.fetch_message(message_id)
        if message:
            # Replace '🌸' with your desired reaction emoji
            if '🌸' not in [reaction.emoji for reaction in message.reactions]:
                await message.add_reaction('🌸')
        else:
            print("Message not found")
    else:
        print("Channel not found")


# Event: When a reaction is added to a message
@bot.event
async def on_reaction_add(reaction, user):
    # Check if the reaction is added by the bot
    if user.bot:
        return

    # Get the reaction channel and message IDs
    channel_id, message_id = get_reaction_ids()

    # Check if the reaction is added to the specified message
    if reaction.message.channel.id == channel_id and reaction.message.id == message_id:
        # Check if the added reaction is the specified emoji
        if str(reaction.emoji) == '🌸':
            channel_name = f"{user.name}"
            for channel in category.text_channels:
                if channel.name.lower() == channel_name.lower():
                    print(f"Conversation Already Open - {user.name}#{user.discriminator} ({user.id})")
                    return

        overwrites = {
            reaction.message.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            user: nextcord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }

        channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
        embed = nextcord.Embed(
            title="Conversation Created !",
            description="Do f!activate to talk with the femboy assistant, f!close to delete the channel",
            color=0x2b2d31
        )
        embed.set_author(name=user.name+"#"+user.discriminator, icon_url=str(user.avatar.url))
        message = await channel.send(user.mention, embed=embed)
        print(f"Conversation created - {user.name}#{user.discriminator} ({user.id})")

# Command to reset chat
@bot.slash_command(description="idk")
async def rtv(ctx):
    if await permission_check(ctx):
        async with client.connect(owner_id) as chat2:
            await chat2.new_chat({get_cai_char_id}, with_greeting=False)

# Command to reset chat
@bot.slash_command(description="Command to test the permissioncheck function")
async def permissiontest(ctx):
    if await permission_check(ctx):
        await ctx.send("test success")

# Command to reset chat
@bot.slash_command(description="Command to send a message")
async def say(ctx):
    if await permission_check(ctx):
        await ctx.send("message")

# Run the bot
if __name__ == "__main__":
    run_bot()