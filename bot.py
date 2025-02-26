import os
import discord
import logging
import json
import re

from discord.ext import commands
from dotenv import load_dotenv
from agent import MistralAgent

PREFIX = "!"

# Setup logging
logger = logging.getLogger("discord")

# Load the environment variables
load_dotenv()

# Create the bot with all intents
# The message content and members intent must be enabled in the Discord Developer Portal for the bot to work.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Import the Mistral agent from the agent.py file
agent = MistralAgent()


# Get the token from the environment variables
token = os.getenv("DISCORD_TOKEN")

# Dictionary to store trip preferences
trip_preferences = {}
# Create the dictionary statically for testing
'''
trip_preferences["user_1"] = []
trip_preferences["user_1"].append({
    "user": "user_1",
    "location": "beach",
    "budget": "1,000",
    "dates": "3/10-3/16",
    "mode": "Relax"
})
trip_preferences["user_2"] = []
trip_preferences["user_2"].append({
    "user": "user_2",
    "location": "washington d.c.",
    "budget": "1,500",
    "dates": "3/11-3/15",
    "mode": "exploring"
})
'''

@bot.event
async def on_ready():
    """
    Called when the client is done preparing the data received from Discord.
    Prints message on terminal when bot successfully connects to discord.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_ready
    """
    logger.info(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in any channel the bot can see.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    """
    # Don't delete this line! It's necessary for the bot to process commands.
    await bot.process_commands(message)

    # Ignore messages from self or other bots to prevent infinite loops.
    if message.author.bot or message.content.startswith("!"):
        return

    # Process the message with the agent you wrote
    # Open up the agent.py file to customize the agent
    logger.info(f"Processing message from {message.author}: {message.content}")
    response = await agent.run(message)

    # Send the response back to the channel
    await message.reply(response)


# Commands


# This example command is here to show you how to add commands to the bot.
# Run !ping with any number of arguments to see the command in action.
# Feel free to delete this if your project will not need commands.
@bot.command(name="ping", help="Pings the bot.")
async def ping(ctx, *, arg=None):
    if arg is None:
        await ctx.send("Pong!")
    else:
        await ctx.send(f"Pong! Your argument was {arg}")

# Submit Trips
@bot.command(name="submit_trips", help="Users submit trip ideas and preferences")
async def submit_trips(ctx, location: str, budget: str, dates: str, mode: str):
    if ctx.guild.id not in trip_preferences:
        trip_preferences[ctx.guild.id] = []
    
    trip_preferences[ctx.guild.id].append({
        "user": ctx.author.name,
        "location": location,
        "budget": budget,
        "dates": dates,
        "mode": mode.lower()
    })

    await ctx.send(f"{ctx.author.name} submitted travel preferences: Location - {location}, Budget - {budget}, Dates - {dates}, Mode - {mode.capitalize()}.")

# Recommend Trips
@bot.command(name="recommend_trips", help="AI recommends trips")
async def recommend_trips(ctx, *, arg=None):
    # Should we add a certain number of recommendations?
    prompt = "Based on the following travel preferences, suggest a few trip options that balances everyone's inputs. Make sure the activity list is descriptive."
    
    # Add user preferences to the prompt
    for user_prefs in trip_preferences.values():
        for pref in user_prefs:
            prompt += f"- {pref['user']} wants to travel to {pref['location']} on a {pref['mode']} trip with a budget of {pref['budget']} during {pref['dates']}.\n"

    # AI answer is formatted as JSON
    prompt += "Please format the response in JSON with this structure. Return ONLY a raw JSON array. Do NOT use Markdown formatting, triple backticks, or any extra text:\n"
    prompt += """"
                [
                {
                    "name": "Trip Name",
                    "dates": "Trip Dates",
                    "trip_style": "Trip Style",
                    "budget": "Budget",
                    "activities": ["Activity 1", "Activity 2", "Activity 3"]
                },
                ...
                ]
                """
    response = await agent.run_command(prompt)
    # Try and parse the JSON
    try:
        trips = json.loads(response)
    except json.JSONDecodeError:
        await ctx.send("Error: AI response is not valid JSON. Here is what was returned:\n" + response)
        return

    # Print to the channel the recommended trip options
    full_response = "**AI-Recommended Trips:**\n"
    for i, trip in enumerate(trips, start=1):
        full_response += f"{i}. **{trip['name']}**\n"
        full_response += f"Dates: {trip['dates']}\n"
        full_response += f"Style: {trip['trip_style']}\n"
        full_response += f"Budget: {trip['budget']}\n"
        full_response += f"Activities: {', '.join(trip['activities'])}\n\n"
    await ctx.send(full_response)
    
# Start the bot, connecting it to the gateway
bot.run(token)
