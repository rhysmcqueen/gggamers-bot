import nextcord
from nextcord.ext import commands
import requests
import os
import logging

# Load Pterodactyl API key and URL from environment variables
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY")
PTERODACTYL_URL = "https://Pterodactyl.local.McQueenLab.net/api"

logger = logging.getLogger("BotLogger")

HEADERS = {
    "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_servers():
    """Fetches a list of servers from Pterodactyl"""
    url = f"{PTERODACTYL_URL}/client"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        servers = response.json().get("data", [])
        return {server["attributes"]["identifier"]: server["attributes"]["name"] for server in servers}
    except requests.RequestException as e:
        logger.error(f"Error fetching servers: {e}")
        return {}

def restart_server(server_id):
    """Sends a restart request to a specified server on Pterodactyl"""
    url = f"{PTERODACTYL_URL}/client/servers/{server_id}/power"
    try:
        response = requests.post(url, headers=HEADERS, json={"signal": "restart"})
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Error restarting server {server_id}: {e}")
        return False

def add_restart_command(bot, GUILD_IDS):
    @bot.slash_command(name="restart", description="Restart a Minecraft server on Pterodactyl", guild_ids=GUILD_IDS)
    async def restart_command(interaction: nextcord.Interaction):
        """Lists available servers and allows restarting a selected one"""
        servers = get_servers()
        if not servers:
            await interaction.response.send_message("No servers found or API error.", ephemeral=True)
            return
        
        options = [
            nextcord.SelectOption(label=name, value=id) for id, name in servers.items()
        ]

        class ServerSelect(nextcord.ui.Select):
            def __init__(self):
                super().__init__(placeholder="Select a server to restart", options=options)

            async def callback(self, interaction: nextcord.Interaction):
                server_name = servers[self.values[0]]
                if restart_server(self.values[0]):
                    await interaction.response.send_message(f"Restarting **{server_name}**...", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Failed to restart **{server_name}**.", ephemeral=True)

        class ServerSelectView(nextcord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(ServerSelect())

        await interaction.response.send_message("Select a server to restart:", view=ServerSelectView(), ephemeral=True)
