import requests
import nextcord
from dotenv import load_dotenv
import os
import logging

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"

logger = logging.getLogger("BotLogger")

def handle_api_error(response):
    """Handle Riot API error responses."""
    error_codes = {
        400: "Bad request",
        401: "Unauthorized - Check API key",
        403: "Forbidden - Check API key",
        404: "Data not found",
        429: "Rate limit exceeded",
        500: "Internal server error",
        503: "Service unavailable"
    }
    return error_codes.get(response.status_code, f"Unknown error (HTTP {response.status_code})")

def get_champion_mastery(puuid):
    """Get champion mastery data for a summoner."""
    url = f"https://{REGION}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    
    return response.json()

def get_champion_data():
    """Fetch champion data from Data Dragon API."""
    try:
        # Get latest version
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        version = requests.get(version_url).json()[0]
        
        # Get champion data
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
        response = requests.get(url)
        data = response.json()
        
        # Create mapping of champion IDs to names
        champion_names = {}
        for champion in data['data'].values():
            champion_names[champion['key']] = champion['name']
        
        return champion_names
    except Exception as e:
        print(f"Error fetching champion data: {e}")
        return {}

def format_mastery_data(mastery_data, limit=10):
    """Format mastery data into readable text."""
    if not mastery_data:
        return "No champion mastery data found."
    
    # Load champion data from Data Dragon
    champion_names = get_champion_data()
    
    formatted_data = ["**Top Champions:**"]
    
    for entry in mastery_data[:limit]:
        champion_name = champion_names.get(str(entry["championId"]), f"Champion {entry['championId']}")
        mastery_level = entry["championLevel"]
        mastery_points = format(entry["championPoints"], ",")
        
        formatted_data.append(
            f"• **{champion_name}** - Level {mastery_level} "
            f"({mastery_points} points)"
        )
    
    return "\n".join(formatted_data)

def add_mastery_command(bot):
    @bot.slash_command(
        name="mastery",
        description="Show a player's top champions by mastery"
    )
    async def mastery_command(
        interaction: nextcord.Interaction, 
        riot_id: str, 
        limit: int = 10
    ):
        await interaction.response.defer()
        
        try:
            logger.info(f"Fetching mastery data for summoner: {riot_id}")
            # Parse Riot ID
            if "#" in riot_id:
                name, tag = riot_id.split("#")
            else:
                name, tag = riot_id, "NA1"
            
            # Get account data
            account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
            headers = {"X-Riot-Token": RIOT_API_KEY}
            response = requests.get(account_url, headers=headers)
            if response.status_code != 200:
                raise Exception(handle_api_error(response))
            
            puuid = response.json()["puuid"]
            
            # Get and format mastery data
            mastery_data = get_champion_mastery(puuid)
            formatted_data = format_mastery_data(mastery_data, limit)
            
            embed = nextcord.Embed(
                title=f"Champion Mastery for {riot_id}",
                description=formatted_data,
                color=0x1e90ff
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_msg = f"Error fetching mastery data for {riot_id}: {str(e)}"
            logger.error(error_msg)
            await interaction.followup.send(
                "An error occurred while fetching mastery data. Please try again later.",
                ephemeral=True
            ) 