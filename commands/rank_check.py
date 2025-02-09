import requests
import nextcord
from dotenv import load_dotenv
import os
import logging

# Load the .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"  # Default region

logger = logging.getLogger("BotLogger")

def handle_api_error(response):
    """Handle common API errors and return a user-friendly message."""
    if response.status_code == 429:
        return "Slow down! Riot's servers are rate-limited."
    elif response.status_code == 403:
        return "Invalid API key."
    elif response.status_code == 404:
        return "Summoner not found. Check the Riot ID format."
    return f"An error occurred: {response.status_code} {response.reason}"

def fetch_summoner_rank(riot_id):
    """Fetch the rank data for a summoner by Riot ID."""
    # Step 1: Get the account by riot ID
    # Remove any spaces and handle optional tag
    riot_id = riot_id.replace(" ", "")
    
    if "#" in riot_id:
        name, tag = riot_id.split("#")
    else:
        name = riot_id
        tag = "NA1"  # Default tag if none provided
    
    # First, get the PUUID using the account-v1 endpoint
    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    print(f"Requesting Account URL: {account_url}")  # Debug
    
    response = requests.get(account_url, headers=headers)
    print(f"Response Code: {response.status_code}, Response Body: {response.text}")  # Debug
    
    if response.status_code != 200:
        raise Exception(handle_api_error(response))

    account_data = response.json()
    puuid = account_data["puuid"]

    # Step 2: Get summoner data using PUUID
    summoner_url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    summoner_response = requests.get(summoner_url, headers=headers)
    
    if summoner_response.status_code != 200:
        raise Exception(handle_api_error(summoner_response))

    summoner_data = summoner_response.json()
    summoner_id = summoner_data["id"]  # Get the summoner ID

    # Step 3: Get the rank data using summoner ID
    rank_url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    rank_response = requests.get(rank_url, headers=headers)
    
    if rank_response.status_code != 200:
        raise Exception(handle_api_error(rank_response))

    rank_data = rank_response.json()
    return rank_data


def format_rank_data(rank_data):
    """Format the rank data into a human-readable string."""
    if not rank_data:
        return "Unranked"
    
    formatted_data = []
    for entry in rank_data:
        queue_type = "Ranked Solo" if entry["queueType"] == "RANKED_SOLO_5x5" else "Ranked Flex"
        tier = entry["tier"].capitalize()
        rank = entry["rank"]
        lp = entry["leaguePoints"]
        wins = entry["wins"]
        losses = entry["losses"]
        win_rate = round((wins / (wins + losses)) * 100, 2)

        formatted_data.append(
            f"**{queue_type}:** {tier} {rank} - {lp} LP\n"
            f"**Wins:** {wins} | **Losses:** {losses} | **Win Rate:** {win_rate}%"
        )
    
    return "\n\n".join(formatted_data)

def add_rank_check_command(bot):
    @bot.slash_command(
        name="rank",
        description="Get the rank of a summoner by Riot ID (tag is optional, defaults to NA1)"
    )
    async def rank_command(interaction: nextcord.Interaction, riot_id: str):
        await interaction.response.defer()

        try:
            logger.info(f"Fetching rank data for: {riot_id}")
            
            # Parse Riot ID
            if "#" in riot_id:
                name, tag = riot_id.split("#")
            else:
                name, tag = riot_id, "NA1"
            logger.info(f"Parsed Riot ID - Name: {name}, Tag: {tag}")
            
            # Fetch and format the rank data
            rank_data = fetch_summoner_rank(riot_id)
            logger.info(f"Successfully fetched rank data for {riot_id}")
            
            formatted_data = format_rank_data(rank_data)
            display_name = riot_id if "#" in riot_id else f"{riot_id}#NA1"

            embed = nextcord.Embed(
                title=f"Rank for {display_name}",
                description=formatted_data,
                color=0x1e90ff
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_msg = f"Error fetching rank data for {riot_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await interaction.followup.send(str(e))
