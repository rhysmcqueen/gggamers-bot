import os
import nextcord
from nextcord.ext import commands
from config import TOKEN
from commands.setup_roles import setup_roles, add_reaction_handler
from commands.vote_mute import vote_mute
from commands.get_scammed import add_scam_command

# Define the guild ID for faster command sync
GUILD_IDS = [546931899768242177]

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
@bot.slash_command(name="setup", description="Set up the reaction role message.", guild_ids=[546931899768242177] )
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

bot.run(TOKEN)
