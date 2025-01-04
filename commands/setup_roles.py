import nextcord
from nextcord.utils import get

# A dictionary to map emojis to roles
EMOJI_ROLE_MAP = {
    "🍎": "Apple",  # Replace with your emoji and role
    "🍌": "Banana",
    "🍊": "Orange",
}

# Message IDs for which reactions should assign roles
ALLOWED_MESSAGE_IDS = set()  # Global set to store allowed message IDs

# Channel ID where reactions are allowed
ALLOWED_CHANNEL_ID = 969187161641467914  # Replace with the actual ID of #testing-ground

async def setup_roles(interaction: nextcord.Interaction):
    """Set up the reaction role message."""
    description = "React to this message to get a role:\n"
    for emoji, role_name in EMOJI_ROLE_MAP.items():
        description += f"{emoji} - {role_name}\n"

    embed = nextcord.Embed(title="Reaction Roles", description=description, color=0x00ff00)
    message = await interaction.channel.send(embed=embed)

    for emoji in EMOJI_ROLE_MAP.keys():
        await message.add_reaction(emoji)

    # Add the message ID to ALLOWED_MESSAGE_IDS
    ALLOWED_MESSAGE_IDS.add(message.id)

    await interaction.response.send_message("Reaction role message setup complete!", ephemeral=True)

def add_reaction_handler(bot):
    """Add reaction event handlers to the bot."""
    @bot.event
    async def on_raw_reaction_add(payload):
        """Handle reactions to assign roles."""
        # Check if the reaction is in the allowed channel
        if payload.channel_id != ALLOWED_CHANNEL_ID:
            return

        # Check if the reaction is on an allowed message
        if payload.message_id not in ALLOWED_MESSAGE_IDS:
            return

        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        # Check if the emoji is mapped to a role
        role_name = EMOJI_ROLE_MAP.get(payload.emoji.name)
        if not role_name:
            return

        role = get(guild.roles, name=role_name)
        if not role:
            print(f"Role {role_name} not found in the guild")
            return

        await member.add_roles(role)
        print(f"Assigned role {role_name} to {member.name}")

    @bot.event
    async def on_raw_reaction_remove(payload):
        """Handle reactions to remove roles."""
        # Check if the reaction is in the allowed channel
        if payload.channel_id != ALLOWED_CHANNEL_ID:
            return

        # Check if the reaction is on an allowed message
        if payload.message_id not in ALLOWED_MESSAGE_IDS:
            return

        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        # Check if the emoji is mapped to a role
        role_name = EMOJI_ROLE_MAP.get(payload.emoji.name)
        if not role_name:
            return

        role = get(guild.roles, name=role_name)
        if not role:
            print(f"Role {role_name} not found in the guild")
            return

        await member.remove_roles(role)
        print(f"Removed role {role_name} from {member.name}")
