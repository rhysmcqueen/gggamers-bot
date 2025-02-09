import requests
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
import datetime
import logging

# Load .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")  # Load from .env
REGION = "na1"  # Default region
ACCOUNT_REGION = "americas"  # Use the broader account region for the Account API

logger = logging.getLogger("BotLogger")

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
    """Fetch and format match history for a Riot ID."""
    try:
        summoner_name, tag_line = parse_riot_id(riot_id)
        logger.info(f"Parsed Riot ID - Name: {summoner_name}, Tag: {tag_line}")

        # Get account data
        account_data = get_account_data(summoner_name, tag_line)
        logger.info(f"Successfully fetched account data for {riot_id}")

        puuid = account_data["puuid"]
        match_ids = get_match_history(puuid, match_count)
        logger.info(f"Retrieved {len(match_ids)} match IDs")

        matches = []
        for match_id in match_ids:
            try:
                match_data = get_match_details(match_id)
                matches.append(match_data)
                logger.info(f"Successfully fetched details for match {match_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch details for match {match_id}: {e}")

        # Format results
        results = format_match_results(matches, puuid)
        logger.info("Successfully formatted match history")
        return results

    except Exception as e:
        logger.error(f"Error in fetch_and_format_history: {e}", exc_info=True)
        raise

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
        riot_id: str,
        match_count: int = 10
    ):
        await interaction.response.defer()

        try:
            logger.info(f"Fetching match history for {riot_id}, count: {match_count}")
            
            # Validate match count
            if match_count > 50:
                logger.info(f"Adjusted match count from {match_count} to 50")
                match_count = 50
            elif match_count < 1:
                logger.info(f"Adjusted match count from {match_count} to 1")
                match_count = 1

            # Fetch and format the history
            history = await fetch_and_format_history(riot_id, match_count)
            logger.info(f"Successfully fetched {len(history)} matches for {riot_id}")

            # Split and send results
            chunks = list(split_by_chunk_size(history, 20))
            for i, chunk in enumerate(chunks):
                embed = nextcord.Embed(
                    title=f"Match History for {riot_id} (Page {i + 1}/{len(chunks)})",
                    description="\n".join(chunk),
                    color=0x1e90ff
                )
                await interaction.followup.send(embed=embed)
                logger.info(f"Sent match history page {i + 1}/{len(chunks)} for {riot_id}")

        except Exception as e:
            error_msg = f"Error fetching match history for {riot_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await interaction.followup.send(str(e))
