import os
import nextcord
from nextcord.ext import commands
#from config import TOKEN
from commands.setup_roles import setup_roles, add_reaction_handler
from commands.vote_mute import vote_mute
from commands.get_scammed import add_scam_command
from commands.match_history import add_match_history_command
# from commands.ask_chatgpt import add_gpt_chat_command
from commands.jar_counter import add_jar_commands
from commands.rank_check import add_rank_check_command
from commands.clash_check import add_clash_command
from commands.mastery import add_mastery_command
from commands.restart_server import add_restart_command


from dotenv import load_dotenv
import os
import logging
import asyncio

# Load .env file
load_dotenv()
#Load Variables:
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_IDS = list(map(int, os.getenv("GUILD_IDS", "").split(",")))

# Configure global logger with more detailed settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BotLogger")

# Create file handler
file_handler = logging.FileHandler("bot.log")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(file_handler)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(console_handler)

# Add Discord logging handler
class DiscordLoggingHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def log_to_discord(self, record):
        channel = self.bot.get_channel(self.channel_id)  # Use the channel_id from init
        if channel:
            try:
                message = self.format(record)
                # Truncate message if it's too long for Discord
                if len(message) > 1900:
                    message = message[:1900] + "..."
                await channel.send(f"```\n{message}\n```")
            except Exception as e:
                print(f"Failed to send log to Discord: {e}")
                logger.error(f"Failed to send log to Discord: {e}", exc_info=True)
        else:
            print(f"Could not find Discord channel with ID: {self.channel_id}")
            logger.error(f"Could not find Discord channel with ID: {self.channel_id}")

    def emit(self, record):
        # Create task to send log asynchronously
        asyncio.create_task(self.log_to_discord(record))

# Bot Configuration
intents = nextcord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    print(f"Bot logged in as {bot.user}")
    
    # Add Discord handler after bot is ready
    discord_handler = DiscordLoggingHandler(bot, 1336254169656590409)
    discord_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    # Change to INFO level to see all logs
    discord_handler.setLevel(logging.INFO)
    logger.addHandler(discord_handler)
    
    # Test message to verify Discord logging
    logger.info("Bot startup complete - Discord logging test message")
    
    # Sync all commands
    await bot.sync_all_application_commands()
    print("All commands synchronized.")
    logger.info("All commands synchronized.")



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
# add_gpt_chat_command(bot, GUILD_IDS)

#Jack counter
add_jar_commands(bot)

# Add the rank command to the bot
add_rank_check_command(bot)

# Add the clash command to the bot
add_clash_command(bot)

# Add mastery command
add_mastery_command(bot)

# Add the restart command to the bot
add_restart_command(bot, GUILD_IDS)

@bot.event
async def on_application_command(interaction: nextcord.Interaction):
    """Log slash command usage."""
    try:
        user = interaction.user
        command = interaction.application_command
        guild = interaction.guild.name if interaction.guild else "DM"
        channel = interaction.channel.name if interaction.channel else "Unknown"
        
        log_message = (
            f"Command Execution:\n"
            f"{user} ({user.id}) used /{command.name} in {guild}/{channel}"
        )
        logger.info(log_message)
        
        # Log command options if they exist
        if "options" in interaction.data:
            options = interaction.data["options"]
            options_str = " ".join([f"{opt['name']}:{opt['value']}" for opt in options])
            logger.info(f"Command options: {options_str}")
            
    except Exception as e:
        logger.error(f"Error logging command invocation: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Enhanced error logging."""
    try:
        command_name = ctx.command.name if ctx.command else "Unknown"
        user = ctx.author
        channel = ctx.channel.name if ctx.channel else "Unknown"
        guild = ctx.guild.name if ctx.guild else "DM"
        
        error_message = (
            f"Command Error:\n"
            f"Command: {command_name}\n"
            f"User: {user} (ID: {user.id})\n"
            f"Guild: {guild}\n"
            f"Channel: {channel}\n"
            f"Error: {str(error)}\n"
            f"Error Type: {type(error).__name__}"
        )
        
        if isinstance(error, commands.CommandNotFound):
            logger.warning(error_message)
        else:
            logger.error(error_message)
            
            # Log full traceback for non-CommandNotFound errors
            import traceback
            logger.error("Full traceback:", exc_info=error)
            
    except Exception as e:
        logger.error(f"Error in error handling: {e}")

bot.run(TOKEN)
