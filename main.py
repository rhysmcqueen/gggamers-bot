import nextcord
from nextcord.ext import commands
from config import TOKEN
from setup_roles import setup_roles

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

@bot.slash_command(name="setup", description="Set up the reaction role message.")
async def setup_command(interaction: nextcord.Interaction):
    await setup_roles(interaction)

bot.run(TOKEN)