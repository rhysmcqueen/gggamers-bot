import requests
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
import datetime

# Load .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")  # Load from .env
REGION = "na1"  # Set the region for the Match API (adjust as needed)
ACCOUNT_REGION = "americas"  # Use the broader account region for the Account API

# Mapping queue IDs to human-readable names
QUEUE_ID_MAPPING = {
    400: "Normal Draft",
    420: "Ranked Solo",
    430: "Normal Blind",
    440: "Ranked Flex",
    450: "ARAM",
    700: "Clash",
    900: "URF",
    1020: "One for All",
    # Add more queue IDs as needed from Riot's documentation
}

def format_timestamp(timestamp):
    """Convert Riot's game creation timestamp to a readable date format: DD-MM-YY HH:MM."""
    date = datetime.datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
    return date.strftime("%d-%m-%y %H:%M")


async def fetch_and_format_history(game_name, tag_line, match_count):
    """Fetch and format match history for a Riot ID, including total win-loss count and links."""
    # Step 1: Get account data
    account_data = get_account_data(summoner_name, tag_line)
    puuid = account_data["puuid"]

    # Construct summoner profile link
    encoded_summoner_name = summoner_name.replace(" ", "%20")
    summoner_profile_url = f"https://www.leagueofgraphs.com/summoner/na/{encoded_summoner_name}-{(tag_line or 'na1').upper()}"

    # Step 2: Get match IDs with the specified count
    match_ids = get_match_history(puuid, match_count)

    # Step 3: Fetch match details and format the results
    matches = [get_match_details(match_id) for match_id in match_ids]
    results = []
    wins, losses = 0, 0  # Track wins and losses

    for match in matches:
        participant = next(
            p for p in match["info"]["participants"] if p["puuid"] == puuid
        )
        win = "✅" if participant["win"] else "❌"
        champion = participant["championName"]
        kda = f"{participant['kills']}/{participant['deaths']}/{participant['assists']}"

        # Game creation timestamp
        game_creation = format_timestamp(match["info"]["gameCreation"])

        # Queue type
        queue_id = match["info"]["queueId"]
        queue_type = QUEUE_ID_MAPPING.get(queue_id, "Unknown Mode")

        # Construct match details link
        match_id = match["metadata"]["matchId"]
        match_url = f"https://www.leagueofgraphs.com/match/na/{match_id.split('_')[1]}"

        # Update win/loss counters
        if participant["win"]:
            wins += 1
        else:
            losses += 1

        # Combine all details with links
        results.append(
            f"{win} | {champion} {kda} | {queue_type} | {game_creation} | [Match Details]({match_url})"
        )

    # Add total win-loss count and summoner profile link
    results.append(f"\n**Total Games:** {wins + losses}")
    results.append(f"**Wins:** {wins} ✅ | **Losses:** {losses} ❌")
    results.append(f"\n[View Summoner Profile]({summoner_profile_url})")

    return results

def split_by_chunk_size(content, chunk_size):
    """Split a list into chunks of a specified size."""
    for i in range(0, len(content), chunk_size):
        yield content[i:i + chunk_size]

def add_match_history_command(bot):
    @bot.slash_command(
        name="match_history",
        description="Get the match history of a summoner by Summoner Name."
    )
    async def match_history_command(
        interaction: nextcord.Interaction,
        summoner_name: str,
        tag_line: str = None,  # Optional, defaults to None
        match_count: int = 10  # Default to 10 matches
    ):
        # Limit match count to 1-50 for usability
        if match_count > 50:
            match_count = 50
        elif match_count < 1:
            match_count = 1

        await interaction.response.defer()  # Defer the response to prevent timeouts

        try:
            # Fetch and format the history with the specified match count
            history = await fetch_and_format_history(summoner_name, tag_line, match_count)

            # Split the results into chunks of 20 entries
            chunks = list(split_by_chunk_size(history, 20))
            for i, chunk in enumerate(chunks):
                embed = nextcord.Embed(
                    title=f"Match History for {summoner_name}#{tag_line or 'na1'} (Page {i + 1}/{len(chunks)})",
                    description="\n".join(chunk),
                    color=0x1e90ff
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(str(e))
