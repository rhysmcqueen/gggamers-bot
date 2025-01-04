import nextcord
from nextcord.ext import commands
from nextcord.utils import get

# A dictionary to map emojis to roles
EMOJI_ROLE_MAP = {
    "🍎": "Apple",  # Replace with your emoji and role
    "🍌": "Banana",
    "🍊": "Orange",
}

async def setup_roles(interaction: nextcord.Interaction):
    """Set up the reaction role message."""
    description = "React to this message to get a role:\n"
    for emoji, role_name in EMOJI_ROLE_MAP.items():
        description += f"{emoji} - {role_name}\n"

    embed = nextcord.Embed(title="Reaction Roles", description=description, color=0x00ff00)
    message = await interaction.channel.send(embed=embed)

    for emoji in EMOJI_ROLE_MAP.keys():
        await message.add_reaction(emoji)

    await interaction.response.send_message("Reaction role message setup complete!", ephemeral=True)

main.py is:
import nextcord
from nextcord.ext import commands
from nextcord.utils import get

# A dictionary to map emojis to roles
EMOJI_ROLE_MAP = {
    "🍎": "Apple",  # Replace with your emoji and role
    "🍌": "Banana",
    "🍊": "Orange",
}

async def setup_roles(interaction: nextcord.Interaction):
    """Set up the reaction role message."""
    description = "React to this message to get a role:\n"
    for emoji, role_name in EMOJI_ROLE_MAP.items():
        description += f"{emoji} - {role_name}\n"

    embed = nextcord.Embed(title="Reaction Roles", description=description, color=0x00ff00)
    message = await interaction.channel.send(embed=embed)

    for emoji in EMOJI_ROLE_MAP.keys():
        await message.add_reaction(emoji)

    await interaction.response.send_message("Reaction role message setup complete!", ephemeral=True)