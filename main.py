import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
import asyncio
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Disable default help command to avoid conflicts
bot.remove_command("help")

# Role & Channel IDs
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))
CLIENT_ROLE_ID = int(os.getenv('CLIENT_ROLE_ID'))
ADMIN_CHANNEL_ID = int(os.getenv('ADMIN_CHANNEL_ID'))
CLIENT_CHANNEL_ID = int(os.getenv('CLIENT_CHANNEL_ID'))

# Load stock from file with error handling
def load_keys():
    keys = {"day": [], "week": [], "month": [], "lifetime": []}
    try:
        if os.path.exists("stock.txt"):
            with open("stock.txt", "r") as f:
                lines = f.readlines()
                current_type = None
                for line in lines:
                    line = line.strip()
                    if line in keys:
                        current_type = line
                    elif current_type and line:
                        keys[current_type].append(line)
    except Exception as e:
        print(f"Error loading keys: {str(e)}")
    return keys

# Save stock to file with error handling
def save_keys(keys):
    try:
        with open("stock.txt", "w") as f:
            for key_type, key_list in keys.items():
                f.write(f"{key_type}\n")
                for key in key_list:
                    f.write(f"{key}\n")
    except Exception as e:
        print(f"Error saving keys: {str(e)}")

# Load initial stock
keys = load_keys()

# Check if the user has a role
def has_role(ctx, role_id):
    return any(role.id == role_id for role in ctx.author.roles)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("❌ Invalid command. Use `!help` to see available commands.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Please check `!help` for proper usage.")
    else:
        error_msg = f"An error occurred: {str(error)}"
        print(f"Error details: {traceback.format_exc()}")
        await ctx.send(error_msg)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

# Upload command (Admin only)
@bot.command()
async def upload(ctx, key_type: str, *keys_to_upload):
    if not has_role(ctx, ADMIN_ROLE_ID):
        await ctx.send("❌ You do not have permission to upload keys.")
        return

    key_type = key_type.lower()
    if key_type not in keys:
        await ctx.send("❌ Invalid key type. Valid types: `day`, `week`, `month`, `lifetime`.")
        return

    keys[key_type].extend(keys_to_upload)
    save_keys(keys)
    await ctx.send(f"✅ Successfully uploaded `{len(keys_to_upload)}` keys to `{key_type}` stock.")

# Generate command (Client only)
@bot.command()
async def gen(ctx, key_type: str, amount: int):
    if not has_role(ctx, CLIENT_ROLE_ID):
        await ctx.send("❌ You do not have permission to generate keys.")
        return

    key_type = key_type.lower()
    if key_type not in keys or len(keys[key_type]) < amount:
        await ctx.send(f"❌ Not enough `{key_type}` keys available in stock.")
        return

    generated_keys = [keys[key_type].pop(0) for _ in range(amount)]
    save_keys(keys)

    try:
        await ctx.author.send(f"🔑 Your `{key_type}` keys: {', '.join(generated_keys)}")
        await ctx.send(f"✅ `{amount}` `{key_type}` key(s) have been sent to your DMs.")
    except discord.Forbidden:
        for key in generated_keys:
            keys[key_type].insert(0, key)  # Put the keys back if DM fails
        save_keys(keys)
        await ctx.send("⚠️ I couldn't DM you! Please enable DMs and try again.")

# View stock command (Client only)
@bot.command()
async def view_stock(ctx):
    if not has_role(ctx, CLIENT_ROLE_ID):
        await ctx.send("❌ You do not have permission to view stock.")
        return

    stock_message = "**📦 Current Stock:**\n"
    for key_type, key_list in keys.items():
        stock_message += f"**{key_type.capitalize()}**: `{len(key_list)}` keys\n"

    try:
        await ctx.author.send(stock_message)
        await ctx.send("✅ Stock overview has been sent to your DMs.")
    except discord.Forbidden:
        await ctx.send("⚠️ I couldn't DM you! Please enable DMs and try again.")

# HWID request command (Client only)
@bot.command()
async def hwid(ctx, keys_input: str):
    if not has_role(ctx, CLIENT_ROLE_ID):
        await ctx.send("❌ You do not have permission to request HWID binding.")
        return

    keys_list = [key.strip() for key in keys_input.split(",")]
    invalid_keys = [key for key in keys_list if key not in [k for key_list in keys.values() for k in key_list]]

    if invalid_keys:
        await ctx.send(f"❌ Invalid keys: {', '.join(invalid_keys)}. Please check the keys and try again.")
        return

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        for key in keys_list:
            await admin_channel.send(f"⚙️ HWID bind request for key `{key}` from `{ctx.author.name}`")
        await ctx.send(f"✅ Your HWID bind request for keys `{', '.join(keys_list)}` has been sent to the admin.")
    else:
        await ctx.send("⚠️ Could not find the admin channel.")

# Shutdown command (Admin only)
@bot.command()
async def shutdown(ctx):
    if not has_role(ctx, ADMIN_ROLE_ID):
        await ctx.send("❌ You do not have permission to shut down the bot.")
        return
    await ctx.send("🔴 Bot is shutting down...")
    await bot.close()

# Custom Help Command
@bot.command()
async def help(ctx):
    help_message = """**🤖 Available Commands:**
🔹 `!upload <day|week|month|lifetime> <key1> <key2> ...` *(Admin Only)*
 ➥ Uploads keys to the stock.
🔹 `!gen <day|week|month|lifetime> <amount>` *(Client Only)*
 ➥ Generates and sends multiple keys from stock via DM.
🔹 `!view_stock` *(Client Only)*
 ➥ Views available key stock. Sent via DM.
🔹 `!hwid <key1, key2, ...>` *(Client Only)*
 ➥ Requests HWID binding for specific keys.
🔹 `!shutdown` *(Admin Only)*
 ➥ Shuts down the bot.
"""
    try:
        await ctx.author.send(help_message)
        await ctx.send("✅ Help message sent to your DMs.")
    except discord.Forbidden:
        await ctx.send("⚠️ I couldn't DM you! Please enable DMs and try again.")

# Start the keep_alive server and run the bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
