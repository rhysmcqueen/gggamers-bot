import nextcord
from nextcord.utils import get

# A dictionary to map emojis to roles
EMOJI_ROLE_MAP = {
    "🦸": "Marvel Rivals",  # Replace with your emoji and role
    "⛏️": "Grass Block",
    "🤮": "LoL Players",
    "🔪": "@among us",
    "📦": "JackBox",
}

# List of allowed channel names
ALLOWED_CHANNEL_NAMES = ["roles-and-bots", "testing-ground"]  # Add other allowed channel names here


async def setup_roles(interaction: nextcord.Interaction):
    """Set up the reaction role message."""

    # Check if the command is used in an allowed channel
    if interaction.channel.name not in ALLOWED_CHANNEL_NAMES:
        await interaction.response.send_message(
            "This command can only be used in the allowed channels: "
            + ", ".join(ALLOWED_CHANNEL_NAMES),
            ephemeral=True,
        )
        print(f"Command attempted in {interaction.channel.name} but restricted to allowed channels.")
        return

    # Create the reaction role message
    description = "React to this message to get a role:\n"
    for emoji, role_name in EMOJI_ROLE_MAP.items():
        description += f"{emoji} - {role_name}\n"

    embed = nextcord.Embed(title="Reaction Roles", description=description, color=0x00ff00)
    message = await interaction.channel.send(embed=embed)

    for emoji in EMOJI_ROLE_MAP.keys():
        await message.add_reaction(emoji)

    print(f"Reaction role message setup in channel: {interaction.channel.name}")

    await interaction.response.send_message("Reaction role message setup complete!", ephemeral=True)


def add_reaction_handler(bot):
    """Add reaction event handlers to the bot."""
    @bot.event
    async def on_raw_reaction_add(payload):
        """Handle reactions to assign roles or delete invalid reactions."""
        print(f"Reaction added: {payload.emoji.name} by user {payload.user_id} in channel {payload.channel_id}")

        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print("Guild not found.")
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel or channel.name not in ALLOWED_CHANNEL_NAMES:
            print(f"Reaction not in the allowed channel. Channel name: {channel.name if channel else 'Unknown'}")
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            print("Member not found or is a bot.")
            return

        # Check if the emoji is mapped to a role
        role_name = EMOJI_ROLE_MAP.get(payload.emoji.name)
        if not role_name:
            print(f"Invalid reaction: {payload.emoji.name}. Deleting it.")
            # Delete the reaction
            message = await channel.fetch_message(payload.message_id)
            reaction = nextcord.utils.get(message.reactions, emoji=payload.emoji.name)
            if reaction:
                await reaction.remove(member)
            return

        role = get(guild.roles, name=role_name)
        if not role:
            print(f"Role {role_name} not found in the guild.")
            return

        await member.add_roles(role)
        print(f"Assigned role {role_name} to {member.name} ({member.id})")

    @bot.event
    async def on_raw_reaction_remove(payload):
        """Handle reactions to remove roles."""
        print(f"Reaction removed: {payload.emoji.name} by user {payload.user_id} in channel {payload.channel_id}")

        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print("Guild not found.")
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel or channel.name not in ALLOWED_CHANNEL_NAMES:
            print(f"Reaction removal not in the allowed channel. Channel name: {channel.name if channel else 'Unknown'}")
            return

        member = guild.get_member(payload.user_id)
        if not member:
            print("Member not found.")
            return

        # Check if the emoji is mapped to a role
        role_name = EMOJI_ROLE_MAP.get(payload.emoji.name)
        if not role_name:
            print(f"Emoji {payload.emoji.name} not mapped to any role.")
            return

        role = get(guild.roles, name=role_name)
        if not role:
            print(f"Role {role_name} not found in the guild.")
            return

        await member.remove_roles(role)
        print(f"Removed role {role_name} from {member.name} ({member.id})")
