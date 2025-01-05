import openai
import nextcord
from nextcord.ext import commands
import os
# Load OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")


def add_gpt_chat_command(bot, guild_ids):
    @bot.slash_command(
        name="chat",
        description="Ask a question to GPT.",
        guild_ids=guild_ids
    )
    async def chat_command(interaction, prompt: str):
        await interaction.response.defer()  # Defer response to prevent timeout

        try:
            # Use OpenAI's async ChatCompletion API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.7
            )

            # Extract and send GPT's response
            gpt_response = response["choices"][0]["message"]["content"]
            await interaction.followup.send(f"**GPT:** {gpt_response}")
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")