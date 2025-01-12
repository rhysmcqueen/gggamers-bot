import nextcord
from nextcord.ext import commands
import asyncio
import os

async def vote_mute(interaction: nextcord.Interaction, user: nextcord.Member):
    """Initiate a vote to mute a user in voice chat and play a sound upon command invocation."""

    # Ensure the command issuer is in a voice channel
    channel = interaction.user.voice.channel if interaction.user.voice else None
    if not channel:
        await interaction.response.send_message("You need to be in a voice channel to initiate a vote.", ephemeral=True)
        return

    # Ensure the target user is in the same voice channel
    if user not in channel.members:
        await interaction.response.send_message(f"{user.display_name} is not in the same voice channel.", ephemeral=True)
        return

    # Defer interaction response publicly
    try:
        await interaction.response.defer(ephemeral=False)
        print("Interaction deferred successfully.")
    except nextcord.errors.InteractionResponded:
        print("Interaction already responded to.")
        return

    # Ensure the bot is not already connected to a voice channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()

    # Path to audio file
    audio_path = "/home/serveradmin/gggamers-bot/commands/vote_to_mute.mp3"
    if not os.path.exists(audio_path):
        await interaction.followup.send("Audio file not found. Please check the file path.")
        return

    # Connect to the voice channel and play the audio
    try:
        vc = await channel.connect()
        audio_source = nextcord.FFmpegPCMAudio(audio_path)

        if not vc.is_playing():
            vc.play(audio_source)
            print("Audio is playing.")

        # Wait for the audio to finish
        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("Audio finished and bot disconnected.")
    except Exception as e:
        print(f"Error connecting or playing audio: {e}")
        await interaction.followup.send("Failed to connect to the voice channel or play the audio.")
        return

    # Voting setup
    voters = [member for member in channel.members if not member.bot]
    votes_needed = max(len(voters) // 2, 1)

    votes_yes, votes_no = 0, 0

    # Embed for voting
    embed = nextcord.Embed(
        title="Vote to Mute",
        description=f"Vote to mute {user.mention} for 30 seconds.\nVotes needed: {votes_needed}\nReact with 👍 for YES or 👎 for NO.",
        color=0xff0000
    )
    try:
        message = await interaction.channel.send(embed=embed)
        print("Voting embed sent successfully.")
        await message.add_reaction("👍")
        await message.add_reaction("👎")
    except Exception as e:
        print(f"Error sending embed or adding reactions: {e}")
        return

    # Reaction handling for votes
    def check(reaction, member):
        return (
            reaction.message.id == message.id
            and member in voters
            and str(reaction.emoji) in ["👍", "👎"]
        )

    try:
        while votes_yes < votes_needed and votes_no < votes_needed:
            reaction, member = await interaction.client.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "👍":
                votes_yes += 1
            elif str(reaction.emoji) == "👎":
                votes_no += 1

            # Update the embed
            await message.edit(embed=nextcord.Embed(
                title="Vote to Mute",
                description=f"Vote to mute {user.mention} for 30 seconds.\nVotes needed: {votes_needed}\n👍 Yes: {votes_yes}\n👎 No: {votes_no}",
                color=0xff0000
            ))
    except asyncio.TimeoutError:
        await message.edit(embed=nextcord.Embed(
            title="Vote to Mute",
            description=f"Vote timed out.\n👍 Yes: {votes_yes}\n👎 No: {votes_no}",
            color=0xff0000
        ))
        print("Voting timed out.")
        return

    # Apply mute if votes pass
    if votes_yes >= votes_needed:
        await user.edit(mute=True)  # Mute the user
        await interaction.channel.send(f"{user.mention} has been muted for 30 seconds.")
        await asyncio.sleep(30)  # Wait for 30 seconds
        await user.edit(mute=False)  # Unmute the user
        await interaction.channel.send(f"{user.mention} has been unmuted.")
    else:
        await interaction.channel.send(f"Vote failed. {user.mention} will not be muted.")
