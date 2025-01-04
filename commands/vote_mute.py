import nextcord
from nextcord.ext import commands
import asyncio

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

    # Respond immediately to the interaction
    await interaction.response.send_message("Vote is cast!", ephemeral=True)

    # Bot joins the voice channel and plays the sound
    vc = await channel.connect()
    audio_source = nextcord.FFmpegPCMAudio("/home/serveradmin/gggamers-discord-bot/commands/vote_to_mute.mp3")

    if not vc.is_playing():
        vc.play(audio_source)

    # Wait for the sound to finish
    while vc.is_playing():
        await asyncio.sleep(1)

    # Disconnect after playing the sound
    await vc.disconnect()

    # Voting setup
    voters = [member for member in channel.members if not member.bot]
    votes_needed = max(len(voters) // 2, 1)  # At least one vote is required

    votes_yes, votes_no = 0, 0

    # Embed for voting
    embed = nextcord.Embed(
        title="Vote to Mute",
        description=f"Vote to mute {user.mention} for 5 minutes.\nVotes needed: {votes_needed}\nReact with 👍 for YES or 👎 for NO.",
        color=0xff0000
    )
    message = await interaction.channel.send(embed=embed)  # Public message
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    def check(reaction, member):
        return (
            reaction.message.id == message.id
            and member in voters
            and str(reaction.emoji) in ["👍", "👎"]
        )

    # Collect votes
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
                description=f"Vote to mute {user.mention} for 5 minutes.\nVotes needed: {votes_needed}\n👍 Yes: {votes_yes}\n👎 No: {votes_no}",
                color=0xff0000
            ))
    except asyncio.TimeoutError:
        await message.edit(embed=nextcord.Embed(
            title="Vote to Mute",
            description=f"Vote timed out.\n👍 Yes: {votes_yes}\n👎 No: {votes_no}",
            color=0xff0000
        ))
        return

    # Apply mute if votes pass
    if votes_yes >= votes_needed:
        await user.edit(mute=True)
        await interaction.channel.send(f"{user.mention} has been muted for 5 minutes.")
        await asyncio.sleep(300)
        await user.edit(mute=False)
        await interaction.channel.send(f"{user.mention} has been unmuted.")
    else:
        await interaction.channel.send(f"Vote failed. {user.mention} will not be muted.")
