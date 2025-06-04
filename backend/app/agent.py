import os
from mistralai import Mistral

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = "You are a helpful assistant."


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        print(f"MISTRAL_API_KEY loaded: {MISTRAL_API_KEY is not None}")
        if MISTRAL_API_KEY:
            print(f"MISTRAL_API_KEY starts with: {MISTRAL_API_KEY[:5]}...")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run_command(self, message: str):
        # Send the message content to Mistral's API and return Mistral's response
        prompt_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

        # Add instructions for JSON output with location and points of interest
        prompt_messages.append({
            "role": "user",
            "content": """
            Please provide the response in JSON format with the following structure:
            {
              "recommended_trip": "Your trip recommendation text here",
              "location": "Recommended location name",
              "points_of_interest": [
                {"name": "POI Name", "type": "POI Type", "latitude": 0.0, "longitude": 0.0},
                ...
              ]
            }
            Ensure the location name is accurate for geocoding and include relevant points of interest with coordinates if possible.
            """
        })

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=prompt_messages,
            response_format={"type": "json_object"} # Request JSON object output
        )
        return response.choices[0].message.content
