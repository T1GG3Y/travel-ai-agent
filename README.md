# CS 153 Project -  Discord Travel Bot

This project was built on top of the starter code provided by the CS 153 teaching staff.

## Use Case

This Discord bot helps groups efficiently plan trips by collecting travel preferences, generating AI-based trip recommendations, facilitating voting, and finalizing comprehensive itineraries. The goal is to simplify group decision-making and ensure a well-organized travel experience.

<!---

## Demo Video
<> # [![Image 1224x834 Small](https://github.com/user-attachments/assets/990c87bc-17f8-44a6-8c0b-c313a8a04693)](https://drive.google.com/file/d/1doJQYJjCHA0fuOQ8hP3mcmDRORq7E28v/view)

-->
## Features
All of these commands are implemented in `bot.py`.

### Listing Commands
Command: `!commands`

Displays a list of all available commands along with their descriptions to help users navigate the bot’s functionality.
### Submit Travel Preferences
Command: `!submit_trips <location> <budget> <dates> <mode>` 

Users submit:
- Location: A destination or a type of location. If the location has multiple words, underscores can be used for spacing.
- Budget: The user's estimated spending amount, which can be numeric or a descriptive term.
- Dates: The range of available travel dates, formatted as MM/DD/YYYY-MM/DD/YYYY.
- Mode: The user's preferred travel style, such as relaxation, cultural, foodie, or exploration.
Users can submit multiple preferences, and once a submission is made, the bot displays all collected preferences for the group.
###  AI-Generated Trip Recommendations
Command: `!recommend_trips`

The bot analyzes all submitted preferences and uses Mistral AI to suggest a few optimized trip options. The AI-generated recommendations include:
- Location
- Dates
- Budget Estimate
- Activities
Each recommended trip is labeled with a trip number for easy selection.
### Trip Voting 
Command: `!vote_trip <trip_number>`

Users can vote for their preferred AI-generated trip. The bot tracks and updates vote counts in real time, allowing users to see which trip is leading at any moment.
### Finalizing a Trip and Generating a Full Itinerary
Command: `finalize_trip`

The bot selects the most voted trip and generates a detailed day-by-day itinerary. The itinerary includes:
- Accommodation
- Dining Options
- Attractions & Activities
- Transportation Details
- Estimated Total Budget
The itinerary is formatted for clarity and ease of use.
### Clearing Preferences
Command: `!clear_preferences`

Users can remove their submitted travel preferences. This allows for flexibility in planning multiple trips without retaining previous data.
