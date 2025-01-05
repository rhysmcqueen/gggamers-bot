import requests
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


RIOT_API_KEY = os.getenv("RIOT_API_KEY")  # Load from .env
REGION = "na1"  # Set the region for the Match API (adjust as needed)
ACCOUNT_REGION = "americas"  # Use the broader account region for the Account API

def get_account_data(game_name, tag_line):
    """Fetch account data by Riot ID."""
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_match_history(puuid, count):
    """Fetch match history for a given PUUID with a configurable count from the command."""
    # Ensure count is within the API limit of 1 to 100
    if not (1 <= count <= 100):
        raise ValueError("Count must be between 1 and 100.")

    # Construct the API URL with the dynamic count
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    # Make the API request
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_match_details(match_id):
    """Fetch match details by match ID."""
    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
import datetime

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
    account_data = get_account_data(game_name, tag_line)
    puuid = account_data["puuid"]

    # Construct summoner profile link
    summoner_profile_url = f"https://www.leagueofgraphs.com/summoner/na/{game_name}-{tag_line.upper()}"

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

        # Construct match details link with timestamp
        match_id = match["metadata"]["matchId"]
        timestamp = match["info"]["gameCreation"] // 1000  # Convert to seconds
        match_url = f"https://www.leagueofgraphs.com/match/na/{match_id.split('_')[1]}?t={timestamp}"

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

    return "\n".join(results)



def add_match_history_command(bot):
    @bot.slash_command(
        name="match_history",
        description="Get the match history of a summoner by Riot ID."
    )
    async def match_history_command(
        interaction: nextcord.Interaction,
        game_name: str,
        tag_line: str,
        match_count: int = 10  # Default to 10 matches, configurable via command
    ):
        # Limit match count to 1-50 for usability
        if match_count > 50:
            match_count = 50
        elif match_count < 1:
            match_count = 1

        await interaction.response.defer()  # Defer the response to prevent timeouts

        try:
            # Fetch and format the history with the specified match count
            history = await fetch_and_format_history(game_name, tag_line, match_count)

            # Send the response as a public message
            embed = nextcord.Embed(
                title=f"Match History for {game_name}#{tag_line}",
                description=history,
                color=0x1e90ff
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error fetching match history: {e}")
