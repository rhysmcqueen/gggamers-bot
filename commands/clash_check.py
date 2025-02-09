import requests
import nextcord
from dotenv import load_dotenv
import os
from datetime import datetime

# Load the .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGION = "na1"  # Default region

def handle_api_error(response):
    """Handle common API errors and return a user-friendly message."""
    if response.status_code == 429:
        return "Slow down! Riot's servers are rate-limited."
    elif response.status_code == 403:
        return "Invalid API key."
    elif response.status_code == 404:
        return "Player not found in any active Clash teams."
    return f"An error occurred: {response.status_code} {response.reason}"

def get_summoner_by_riot_id(name, tag):
    """Get summoner data using Riot ID."""
    # First get PUUID
    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    response = requests.get(account_url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    
    puuid = response.json()["puuid"]
    
    # Then get summoner data
    summoner_url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    response = requests.get(summoner_url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    
    return response.json()

def get_active_tournaments():
    """Get list of active and upcoming Clash tournaments."""
    url = f"https://{REGION}.api.riotgames.com/lol/clash/v1/tournaments"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    
    return response.json()

def get_clash_team_by_summoner(summoner_id):
    """Get Clash team data for a summoner."""
    url = f"https://{REGION}.api.riotgames.com/lol/clash/v1/players/by-summoner/{summoner_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(handle_api_error(response))
    
    player_data = response.json()
    if not player_data:
        return None
    
    # Get team details
    team_id = player_data[0]["teamId"]
    team_url = f"https://{REGION}.api.riotgames.com/lol/clash/v1/teams/{team_id}"
    team_response = requests.get(team_url, headers=headers)
    
    if team_response.status_code != 200:
        raise Exception(handle_api_error(team_response))
    
    return team_response.json()

def format_team_data(team_data, tournaments):
    """Format team data into a readable string."""
    if not team_data:
        return "No active Clash team found."
    
    # Find tournament name
    tournament_name = "Unknown Tournament"
    for tournament in tournaments:
        if tournament["id"] == team_data["tournamentId"]:
            tournament_name = tournament["name"]
            tournament_date = datetime.fromtimestamp(tournament["schedule"][0]["registrationTime"] / 1000).strftime("%B %d, %Y")
    
    # Get team tier name
    tier_names = {1: "Tier I (Highest)", 2: "Tier II", 3: "Tier III", 4: "Tier IV (Lowest)"}
    tier = tier_names.get(team_data["tier"], f"Tier {team_data['tier']}")
    
    formatted_data = [
        f"**Tournament:** {tournament_name} ({tournament_date})",
        f"**Team Name:** {team_data['name']}",
        f"**Tier:** {tier}",
        f"**Captain:** {team_data['captain']['summonerName']}",
        "\n**Team Members:**"
    ]
    
    for player in team_data["players"]:
        position = player.get("position", "UNASSIGNED").capitalize()
        formatted_data.append(f"• {player['summonerName']} - {position}")
    
    return "\n".join(formatted_data)

def add_clash_command(bot):
    @bot.slash_command(
        name="clash",
        description="Get information about a player's Clash team"
    )
    async def clash_command(interaction: nextcord.Interaction, riot_id: str):
        await interaction.response.defer()
        
        try:
            # Parse Riot ID
            if "#" in riot_id:
                name, tag = riot_id.split("#")
            else:
                name, tag = riot_id, "NA1"
            
            # Get summoner data
            summoner = get_summoner_by_riot_id(name, tag)
            
            # Get tournaments
            tournaments = get_active_tournaments()
            
            # Get and format team data
            team_data = get_clash_team_by_summoner(summoner["id"])
            formatted_data = format_team_data(team_data, tournaments)
            
            embed = nextcord.Embed(
                title=f"Clash Team Info for {riot_id}",
                description=formatted_data,
                color=0x1e90ff
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(str(e)) 