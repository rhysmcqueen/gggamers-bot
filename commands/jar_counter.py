import nextcord
from nextcord.ext import commands
import os
import json

# File to store the jar counter
JAR_FILE = "jar_counter.json"

# Ensure the file exists
if not os.path.exists(JAR_FILE):
    with open(JAR_FILE, "w") as f:
        json.dump({"count": 0}, f)

def load_jar_count():
    """Load the jar count from the file."""
    with open(JAR_FILE, "r") as f:
        return json.load(f)["count"]

def save_jar_count(count):
    """Save the jar count to the file."""
    with open(JAR_FILE, "w") as f:
        json.dump({"count": count}, f)

def add_jar_commands(bot):
    @bot.slash_command(name="jar", description="Add a number to the jar counter. Defaults to 1 if no number is provided.")
    async def jar_command(interaction: nextcord.Interaction, number: int = 1):
        """Slash command to add a number to the jar counter."""
        count = load_jar_count()
        count += number
        save_jar_count(count)
        await interaction.response.send_message(f"Added {number} to the jar. Current count: {count}")

    @bot.slash_command(name="show_jar", description="Show the current value of the jar counter.")
    async def show_jar_command(interaction: nextcord.Interaction):
        """Slash command to display the current counter value."""
        count = load_jar_count()
        await interaction.response.send_message(f"Current jar count: {count}")
