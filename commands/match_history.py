import requests
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
import datetime

# Load .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")  # Load from .env
REGION = "na1"  # Default region
ACCOUNT_REGION = "americas"  # Use the broader account region for the Account API

# Mapping queue IDs to human-readable names
QUEUE_ID_MAPPING = {
    400: "Normal Draft",
    420: "Ranked Solo",
    430: "Normal Blind",
    440: "Ranked Flex",
    450: "ARAM",
    480: "Swiftplay",
    700: "Clash",
    900: "URF",
    1020: "One for All",
}

def handle_api_error(response):
    """Handle common API errors and return a user-friendly message."""
    if response.status_code == 429:
        return "Slow down! Riot's servers are rate-limited."
    elif response.status_code == 403:
        return "Invalid API key."
    elif response.status_code == 404:
        return "Summoner not found. Check the Riot ID format."
    return f"An error occurred: {response.status_code} {response.reason}"

def parse_riot_id(riot_id):
    """Parses a Riot ID in the format 'SummonerName#TAG' and returns name and tag."""
    if "#" in riot_id:
        name, tag = riot_id.split("#", 1)
    else:
        name, tag = riot_id, "na1"  # Default to NA1 if no tag is provided
    return name, tag

def get_account_data(summoner_name, tag_line):
    """Fetch account data by Riot ID."""
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    return response.json()

def get_match_history(puuid, count):
    """Fetch match history for a given PUUID with a configurable count."""
    if not (1 <= count <= 100):
        raise ValueError("Count must be between 1 and 100.")
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    return response.json()

def get_match_details(match_id):
    """Fetch match details by match ID."""
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    return response.json()

async def fetch_and_format_history(riot_id, match_count):
    """Fetch and format match history for a Riot ID, including total win-loss count and links."""
    summoner_name, tag_line = parse_riot_id(riot_id)

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
    
    # Filter out early surrender games by checking both game and participant flags
    filtered_matches = []
    for match in matches:
        participant = next(p for p in match["info"]["participants"] if p["puuid"] == puuid)
        if not participant["teamEarlySurrendered"]:
            filtered_matches.append(match)
    matches = filtered_matches
    
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
        game_creation = datetime.datetime.fromtimestamp(
            match["info"]["gameCreation"] / 1000
        ).strftime("%d-%m-%y %H:%M")

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
        yield content[i : i + chunk_size]

def add_match_history_command(bot):
    @bot.slash_command(
        name="match_history",
        description="Get the match history of a summoner by Riot ID (SummonerName#TAG)."
    )
    async def match_history_command(
        interaction: nextcord.Interaction,
        riot_id: str,  # Riot ID input (e.g., "SummonerName#TAG")
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
            history = await fetch_and_format_history(riot_id, match_count)

            # Split the results into chunks of 20 entries
            chunks = list(split_by_chunk_size(history, 20))
            for i, chunk in enumerate(chunks):
                embed = nextcord.Embed(
                    title=f"Match History for {riot_id} (Page {i + 1}/{len(chunks)})",
                    description="\n".join(chunk),
                    color=0x1e90ff
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(str(e))