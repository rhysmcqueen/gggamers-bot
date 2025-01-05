import os
import nextcord
from nextcord.ext import commands
#from config import TOKEN
from commands.setup_roles import setup_roles, add_reaction_handler
from commands.vote_mute import vote_mute
from commands.get_scammed import add_scam_command
from commands.match_history import add_match_history_command
from commands.ask_chatgpt import add_gpt_chat_command

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()
#Load Variables:
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_IDS = list(map(int, os.getenv("GUILD_IDS", "").split(",")))

# Bot Configuration
intents = nextcord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    # Sync all commands
    await bot.sync_all_application_commands()
    print("All commands synchronized.")



# /setup command (adds and removes roles based on reactions)
@bot.slash_command(name="setup", description="Set up the reaction role message.", guild_ids=GUILD_IDS )
async def setup_command(interaction: nextcord.Interaction):
    await setup_roles(interaction)


# vote to mute:
@bot.slash_command(name="vote_mute", description="Initiate a vote to mute a user in voice chat for 5 minutes.")
async def vote_mute_command(interaction: nextcord.Interaction, user: nextcord.Member):
    await vote_mute(interaction, user)

# Add reaction handler
add_reaction_handler(bot)

# Add the scam command to the bot
add_scam_command(bot, guild_ids=GUILD_IDS)

#Leauge Commands:
add_match_history_command(bot)

#chat GPT
add_gpt_chat_command(bot, GUILD_IDS)


bot.run(TOKEN)
