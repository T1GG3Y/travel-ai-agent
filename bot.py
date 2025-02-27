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
# Dictionary to store trip votes
trip_votes = {}

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

# Clear preferences command
@bot.command(name="clear_preferences", help="Remove a user's trip preferences")
async def clear_preferences(ctx, *, arg=None):
    trip_preferences[ctx.guild.id] = []
    await ctx.send(f"Removed {ctx.author.name}'s trip preferences")

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
    # Display all submitted preferences
    preferences_message = "**Current Trip Preferences:**\n"
    for pref in trip_preferences[ctx.guild.id]:
        preferences_message += (f"- {pref['user']}: Location - {pref['location']}, Budget - {pref['budget']}, "
                                f"Dates - {pref['dates']}, Mode - {pref['mode'].capitalize()}\n")
    await ctx.send(f"{ctx.author.name} submitted travel preferences: Location - {location}, Budget - {budget}, Dates - {dates}, Mode - {mode.capitalize()}.")
    await ctx.send(preferences_message)

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
    prompt += "Please format the response in JSON with this structure. Return ONLY a raw JSON array. Do NOT use Markdown formatting, triple backticks, or any extra text, again just the raw JSON array:\n"
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
    # Remove markdown
    if response.startswith("```json"):
        response = response[7:-3].strip()
    elif response.startswith("```"):
        response = response[3:-3].strip()
    # Try and parse the JSON
    try:
        trips = json.loads(response)
    except json.JSONDecodeError:
        await ctx.send("Error: AI response is not valid JSON. Here is what was returned:\n" + response)
        return

    # Add options to trip_votes
    trip_votes[ctx.guild.id] = {"trips": trips, "votes": {trip["name"]: 0 for trip in trips}}

    # Print to the channel the recommended trip options
    full_response = "**AI-Recommended Trips:**\n"
    for i, trip in enumerate(trips, start=1):
        full_response += f"{i}. **{trip['name']}**\n"
        full_response += f"Dates: {trip['dates']}\n"
        full_response += f"Style: {trip['trip_style']}\n"
        full_response += f"Budget: {trip['budget']}\n"
        full_response += f"Activities: {', '.join(trip['activities'])}\n\n"
    await ctx.send(full_response)

# Vote trips command
@bot.command(name="vote_trip", help="Users vote for trips based on the number")
async def vote_trip(ctx, trip_number:int):
    if ctx.guild.id not in trip_votes or "trips" not in trip_votes[ctx.guild.id]:
        await ctx.send("No trips available to vote on. Use `!recommend_trips` first.")
        return
    trip_list = trip_votes[ctx.guild.id]["trips"]
    if trip_number < 1 or trip_number > len(trip_list):
        await ctx.send("Invalid trip number!")
        return
    selected_trip = trip_list[trip_number - 1]["name"]
    trip_votes[ctx.guild.id]["votes"][selected_trip] += 1
    vote_counts = "\n".join([f"{name}: {count} votes" for name, count in trip_votes[ctx.guild.id]["votes"].items()])
    await ctx.send(f"{ctx.author.name} voted for: {selected_trip}\n \n**Current Vote Count:**\n{vote_counts}")

# Finalize a trip and get the full itinerary
@bot.command(name="finalize_trip", help="Generate a full itinerary for the trip with the most votes")
async def finalize_trip(ctx, *, arg=None):
    if ctx.guild.id not in trip_votes or not trip_votes[ctx.guild.id]["votes"]:
        await ctx.send("No trips have been voted on yet! Use `!vote_trip` to cast your votes.")
        return
    best_trip = max(trip_votes[ctx.guild.id]["votes"], key=trip_votes[ctx.guild.id]["votes"].get, default=None)
    if not best_trip or trip_votes[ctx.guild.id]["votes"][best_trip] == 0:
        await ctx.send("No votes have been cast yet!")
        return
    
    # Include full trip details in the prompt
    selected_trip_data = next((trip for trip in trip_votes[ctx.guild.id]["trips"] if trip["name"] == best_trip), None)
    if not selected_trip_data:
        await ctx.send("Error: Selected trip details not found.")
        return
    trip_json = json.dumps(selected_trip_data, indent=2)
    # Should we ask for more descriptive itineraries?
    prompt = f"Generate a detailed travel itinerary for the following trip. Ensure a daily schedule based on the details provided.\nTrip Details:\n{trip_json}"
    response = await agent.run_command(prompt)

    # Remove excess blank lines and fix encoding issues
    response = response.replace("\n\n\n", "\n").strip()
    # Ensure messages do not exceed Discord's 2000 character limit
    response_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
    await ctx.send("Finalized Trip Itinerary:")
    for chunk in response_chunks:
        await ctx.send(chunk)

# Start the bot, connecting it to the gateway
bot.run(token)
