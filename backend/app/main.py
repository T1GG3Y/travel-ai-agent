import os # Import os
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file in the project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio
from .agent import MistralAgent # Import the MistralAgent
import requests # Import requests
import json # Import json
import re # Import re

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# Instantiate the MistralAgent
mistral_agent = MistralAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

class Message(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}

@app.post("/chat")
async def chat_endpoint(message: Message):
    ai_response_json_str = await mistral_agent.run_command(message.message)

    try:
        ai_response_data = json.loads(ai_response_json_str)
        # Assuming the AI response is a JSON object with 'recommended_trip', 'location', and 'points_of_interest'
        recommended_trip = ai_response_data.get("recommended_trip", "No recommendation provided.")
        location_name = ai_response_data.get("location")
        points_of_interest = ai_response_data.get("points_of_interest", [])

        # If location name is provided by AI, get coordinates for the map
        location_coords = None
        if location_name:
             try:
                # Call the internal geocode endpoint
                geocode_response = await geocode_endpoint(location=location_name)
                if "latitude" in geocode_response and "longitude" in geocode_response:
                    location_coords = [geocode_response["latitude"], geocode_response["longitude"]]
             except Exception as e:
                 print(f"Error getting geocode for AI location: {e}")


        return {
            "response": recommended_trip,
            "location": location_name,
            "location_coords": location_coords,
            "points_of_interest": points_of_interest
            }

    except json.JSONDecodeError:
        # If AI response is not valid JSON, return the raw text response
        return {"response": ai_response_json_str, "location": None, "location_coords": None, "points_of_interest": []}
    except Exception as e:
        print(f"Error processing AI response: {e}")
        return {"response": "Error processing AI response.", "location": None, "location_coords": None, "points_of_interest": []}


@sio.on('message')
async def handle_message(sid, message):
    print(f"Received message from {sid}: {message}")
    await sio.emit('message', f"Echo from backend: {message}", room=sid)

# app.mount("/", app=socketio.ASGIApp(sio)) # Temporarily commented out to debug routing

@app.get("/geocode")
async def geocode_endpoint(location: str):
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    headers = {'User-Agent': 'TravelAIApp/1.0'} # Add a User-Agent header
    try:
        response = requests.get(nominatim_url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()
        if data:
            return {"latitude": float(data[0]["lat"]), "longitude": float(data[0]["lon"])}
        else:
            return {"error": "Location not found"}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching geocode data: {e}")
        return {"error": "Error fetching geocode data"}

@app.get("/places")
async def get_places_endpoint(location: str):
    # This is a simplified example. A real implementation would need more sophisticated querying
    # based on the location and potentially the type of places (e.g., restaurants, attractions)
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node["name"="{location}"]["tourism"](around:10000);
    out;
    """
    headers = {'User-Agent': 'TravelAIApp/1.0'} # Add a User-Agent header
    try:
        response = requests.get(overpass_url, params={{'data': overpass_query}}, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching places data: {e}")
        return {"error": "Error fetching places data"}

@app.get("/weather")
async def get_weather_endpoint(lat: float, lon: float):
    # You will need to add OPENWEATHERMAP_API_KEY to your .env file
    openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not openweathermap_api_key:
        return {"error": "OpenWeatherMap API key not configured"}

    openweathermap_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={openweathermap_api_key}&units=metric"
    headers = {'User-Agent': 'TravelAIApp/1.0'} # Add a User-Agent header
    print(f"OpenWeatherMap URL: {openweathermap_url}") # Debug print
    try:
        response = requests.get(openweathermap_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data from OpenWeatherMap: {e}") # More specific error
        return {"error": "Error fetching weather data"}

# In-memory storage for preferences and votes (replace with database later)
# Keyed by a simple session identifier (e.g., a counter or user ID)
sessions_data = {}
session_counter = 0

class Preference(BaseModel):
    session_id: int # Use a session ID to link preferences
    user: str
    location: str
    budget: str
    dates: str
    mode: str

class Vote(BaseModel):
    session_id: int
    user: str
    trip_name: str

@app.post("/submit_preference")
async def submit_preference_endpoint(preference: Preference):
    global sessions_data
    session_id = preference.session_id

    if session_id not in sessions_data:
        sessions_data[session_id] = {"preferences": [], "recommended_trips": None, "votes": {}}

    sessions_data[session_id]["preferences"].append(preference.dict())
    return {"message": "Preference submitted successfully"}

@app.get("/get_recommendations/{session_id}")
async def get_recommendations_endpoint(session_id: int):
    global sessions_data
    if session_id not in sessions_data or not sessions_data[session_id]["preferences"]:
        return {"error": "No preferences submitted for this session"}

    preferences = sessions_data[session_id]["preferences"]
    prompt = "Based on the following travel preferences, suggest a few trip options that balances everyone's inputs. Make sure the activity list is descriptive."

    for pref in preferences:
        prompt += f"- {pref['user']} wants to travel to {pref['location']} on a {pref['mode']} trip with a budget of {pref['budget']} during {pref['dates']}.\n"

    # Request JSON output for recommendations as well
    prompt += """
    Please format the response in JSON format with a list of trip options:
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
        ai_response_json_str = await mistral_agent.run_command(prompt)
        trips = json.loads(ai_response_json_str)

        # Store recommended trips and initialize votes for the session
        sessions_data[session_id]["recommended_trips"] = trips
        sessions_data[session_id]["votes"] = {trip["name"]: 0 for trip in trips}

        return {"recommendations": trips}

    except json.JSONDecodeError:
        return {"error": "AI response is not valid JSON for recommendations."}
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return {"error": "Error getting recommendations from AI."}

@app.post("/vote_trip")
async def vote_trip_endpoint(vote: Vote):
    global sessions_data
    session_id = vote.session_id
    trip_name = vote.trip_name

    if session_id not in sessions_data or not sessions_data[session_id]["recommended_trips"]:
        return {"error": "No recommended trips available to vote on for this session."}

    if trip_name not in sessions_data[session_id]["votes"]:
        return {"error": f"Trip '{trip_name}' not found in recommendations for this session."}

    sessions_data[session_id]["votes"][trip_name] += 1
    return {"message": f"Vote for '{trip_name}' recorded successfully."}

@app.get("/finalize_trip/{session_id}")
async def finalize_trip_endpoint(session_id: int):
    global sessions_data
    if session_id not in sessions_data or not sessions_data[session_id]["votes"]:
        return {"error": "No votes have been cast for this session."}

    votes = sessions_data[session_id]["votes"]
    if not any(votes.values()):
         return {"error": "No votes have been cast for this session."}

    best_trip_name = max(votes, key=votes.get)
    recommended_trips = sessions_data[session_id]["recommended_trips"]
    selected_trip_data = next((trip for trip in recommended_trips if trip["name"] == best_trip_name), None)

    if not selected_trip_data:
        return {"error": "Selected trip details not found."}

    # Generate detailed itinerary using the AI agent
    trip_json = json.dumps(selected_trip_data, indent=2)
    prompt = f"Generate a detailed and descriptive travel itinerary for the following trip. Ensure a daily schedule based on the details provided.\nTrip Details:\n{trip_json}"

    try:
        itinerary_response = await mistral_agent.run_command(prompt)
        # Clean up response if needed (similar to bot.py)
        itinerary_text = itinerary_response.replace("\n\n\n", "\n").strip()

        return {"finalized_trip": selected_trip_data, "itinerary": itinerary_text}

    except Exception as e:
        print(f"Error generating itinerary: {e}")
        return {"error": "Error generating itinerary."}
