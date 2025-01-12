import nextcord
import re
import json
import os

# Regular expression for SIN pattern
SIN_REGEX = r"^\d{3}-?\d{3}-?\d{3}$"

# JSON file to save matched messages
JSON_FILE = "SIN.json"

def validate_sin(sin):
    """Validate a SIN using the check digit algorithm."""
    # Remove hyphens
    sin = sin.replace("-", "")

    # Ensure it's exactly 9 digits
    if len(sin) != 9:
        return False

    # Extract the payload (first 8 digits) and the check digit (last digit)
    payload, check_digit = sin[:-1], int(sin[-1])

    # Step 1: Double every second digit from right to left
    doubled_digits = [
        int(digit) * 2 if (index % 2 == 1) else int(digit)
        for index, digit in enumerate(reversed(payload))
    ]

    # Step 2: Subtract 9 from any result greater than 9
    processed_digits = [
        (d - 9) if d > 9 else d for d in doubled_digits
    ]

    # Step 3: Sum all digits
    s = sum(processed_digits)

    # Step 4: Calculate the expected check digit
    calculated_check_digit = (10 - (s % 10)) % 10

    # Compare with the provided check digit
    return calculated_check_digit == check_digit

async def scrape_sin(interaction: nextcord.Interaction):
    """Scrape all channels for messages matching the SIN pattern."""
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    matches = []

    # Iterate through all text channels
    await interaction.response.defer(ephemeral=True)  # Defer the interaction to avoid timeout
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=None):
                # Skip bot messages
                if message.author.bot:
                    continue

                # Check if the message matches the SIN pattern
                if re.match(SIN_REGEX, message.content):
                    # Validate the SIN
                    if validate_sin(message.content):
                        match_data = {
                            "user": str(message.author),
                            "message_link": message.jump_url,
                            "content": message.content
                        }
                        matches.append(match_data)

                        # Reply to the message
                        await message.reply("Get scammed!")
        except Exception as e:
            print(f"Error reading channel {channel.name}: {e}")

    # Save matches to JSON
    if matches:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r") as f:
                existing_data = json.load(f)
            matches = existing_data + matches

        with open(JSON_FILE, "w") as f:
            json.dump(matches, f, indent=4)

        await interaction.followup.send(f"Scraping completed. Found {len(matches)} valid SINs. Data saved to `{JSON_FILE}`.")
    else:
        await interaction.followup.send("No valid SINs found.")

def add_scam_command(bot, guild_ids):
    """Add the scrape_sin command to the bot."""
    @bot.slash_command(name="scrape_sin", description="Scrape all channels for SIN-like patterns.", guild_ids=guild_ids)
    async def scrape_sin_command(interaction: nextcord.Interaction):
        await scrape_sin(interaction)
