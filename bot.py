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
if not token:
    logger.error("DISCORD_TOKEN environment variable not found. Please check your .env file.")
    raise ValueError("DISCORD_TOKEN environment variable is required")

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
    try:
        response = await agent.run(message)
        # Send the response back to the channel
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.reply("I encountered an error processing your message. Please try again later.")


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
    try:
        # Initialize if not exists
        if ctx.guild.id not in trip_preferences:
            trip_preferences[ctx.guild.id] = []
        else:
            trip_preferences[ctx.guild.id] = []
        await ctx.send(f"Removed {ctx.author.name}'s trip preferences")
    except Exception as e:
        logger.error(f"Error clearing preferences: {e}")
        await ctx.send("An error occurred while clearing preferences.")

# Submit Trips
@bot.command(name="submit_trips", help="Users submit trip ideas and preferences")
async def submit_trips(ctx, location: str = None, budget: str = None, dates: str = None, mode: str = None):
    try:
        # Validate inputs
        if not location or not budget or not dates or not mode:
            await ctx.send("All fields (location, budget, dates, mode) are required.")
            return
        
        # Validate budget is a number
        # Remove commas and spaces for validation
        clean_budget = budget.replace(",", "").replace(" ", "")
        if not clean_budget.replace(".", "").isdigit():
            await ctx.send("Budget must be a number (e.g., 1000 or 1,000).")
            return
        
        # Validate dates is either a month or a number format
        months = ["january", "february", "march", "april", "may", "june", "july", 
                 "august", "september", "october", "november", "december",
                 "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        
        # Check if dates contains a month name
        is_month = any(month in dates.lower() for month in months)
        # Check if dates contains numbers (like MM/DD-MM/DD or just a number)
        has_numbers = any(char.isdigit() for char in dates)
        
        if not (is_month or has_numbers):
            await ctx.send("Dates must be either a month name (e.g., 'January', 'Feb') or a date format (e.g., '3/10-3/16', '15').")
            return
        # Initialize if not exists
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
    except Exception as e:
        logger.error(f"Error submitting trip preferences: {e}")
        await ctx.send("An error occurred while submitting your preferences. Please try again.")

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
    try:
        response = await agent.run_command(prompt)
        # Remove markdown
        if response.startswith("```json"):
            response = response[7:-3].strip()
        elif response.startswith("```"):
            response = response[3:-3].strip()
        # Try and parse the JSON
        try:
            trips = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            await ctx.send("Error: AI response is not valid JSON. Here is what was returned:\n" + response)
            return
    except Exception as e:
        logger.error(f"Error calling AI service: {e}")
        await ctx.send("Error: Failed to get recommendations from AI service. Please try again later.")
        return

    # Add options to trip_votes
    try:
        # Validate trip data structure
        for trip in trips:
            if not isinstance(trip, dict):
                await ctx.send("Error: Invalid trip data format.")
                return
                
            required_fields = ["name", "dates", "trip_style", "budget", "activities"]
            for field in required_fields:
                if field not in trip:
                    await ctx.send(f"Error: Missing required field '{field}' in trip data.")
                    return
                    
            if not isinstance(trip["activities"], list):
                await ctx.send("Error: 'activities' field must be a list.")
                return
                
        # Initialize trip_votes for this guild
        trip_votes[ctx.guild.id] = {"trips": trips, "votes": {trip["name"]: 0 for trip in trips}}
    except Exception as e:
        logger.error(f"Error initializing trip votes: {e}")
        await ctx.send("An error occurred while processing trip data.")
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

# Vote trips command
@bot.command(name="vote_trip", help="Users vote for trips based on the number")
async def vote_trip(ctx, trip_number:int):
    try:
        if ctx.guild.id not in trip_votes or "trips" not in trip_votes[ctx.guild.id]:
            await ctx.send("No trips available to vote on. Use `!recommend_trips` first.")
            return
        
        trip_list = trip_votes[ctx.guild.id]["trips"]
        if trip_number < 1 or trip_number > len(trip_list):
            await ctx.send(f"Invalid trip number! Please choose a number between 1 and {len(trip_list)}.")
            return
            
        selected_trip = trip_list[trip_number - 1]["name"]
        
        # Initialize votes for this trip if not already present
        if selected_trip not in trip_votes[ctx.guild.id]["votes"]:
            trip_votes[ctx.guild.id]["votes"][selected_trip] = 0
            
        trip_votes[ctx.guild.id]["votes"][selected_trip] += 1
        vote_counts = "\n".join([f"{name}: {count} votes" for name, count in trip_votes[ctx.guild.id]["votes"].items()])
        await ctx.send(f"{ctx.author.name} voted for: {selected_trip}\n \n**Current Vote Count:**\n{vote_counts}")
    except Exception as e:
        logger.error(f"Error in vote_trip command: {e}")
        await ctx.send("An error occurred while processing your vote. Please try again.")

# Finalize a trip and get the full itinerary
@bot.command(name="finalize_trip", help="Generate a full itinerary for the trip with the most votes")
async def finalize_trip(ctx, *, arg=None):
    try:
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
        
        try:
            response = await agent.run_command(prompt)
            
            # Remove excess blank lines and fix encoding issues
            response = response.replace("\n\n\n", "\n").strip()
            
            # Ensure messages do not exceed Discord's 2000 character limit
            if not response:
                await ctx.send("Error: Received empty response from AI service.")
                return
                
            response_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await ctx.send("Finalized Trip Itinerary:")
            for chunk in response_chunks:
                await ctx.send(chunk)
                
        except Exception as e:
            logger.error(f"Error calling AI service for itinerary: {e}")
            await ctx.send("Error: Failed to generate itinerary. Please try again later.")
            
    except Exception as e:
        logger.error(f"Error in finalize_trip command: {e}")
        await ctx.send("An error occurred while finalizing the trip. Please try again.")


# Command to list all available commands
@bot.command(name="commands", help="Lists all available commands")
async def list_commands(ctx):
    command_list = "**Available Commands:**\n"
    for command in bot.commands:
        command_list += f"- !{command.name}: {command.help}\n"
    await ctx.send(command_list)

# Global error handler for command not found
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Extract the command name from the error message
        command_name = ctx.message.content.split()[0][len(PREFIX):]
        logger.error(f"Command not found: {command_name}")
        await ctx.send(f"Error: Command '{command_name}' not found. Use !commands to see all available commands.")
# Start the bot, connecting it to the gateway
try:
    bot.run(token)
except discord.errors.LoginFailure:
    logger.error("Invalid Discord token. Please check your DISCORD_TOKEN in the .env file.")
except Exception as e:
    logger.error(f"Error starting the bot: {e}")
