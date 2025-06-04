# Codebase Summary: Travel AI Web Application

## Key Components and Their Interactions
- **Frontend (React):** Handles user interface, real-time chat display, map visualization, and itinerary presentation. Interacts with the backend via REST APIs and WebSockets.
- **Backend (FastAPI):** Provides API endpoints for chat, recommendations, itinerary generation, and data retrieval from external APIs. Contains the core logic for processing user requests and interacting with the AI agent.
- **AI Agent (MistralAgent):** The existing Python class will be integrated into the FastAPI backend to handle AI-based recommendations and itinerary generation.

## Data Flow
- User input from the frontend chat interface is sent to the backend via WebSockets or a REST API endpoint.
- The backend processes the input, potentially interacting with the AI agent or external APIs.
- The backend sends responses back to the frontend via WebSockets for real-time updates.
- Trip preferences, recommendations, and itinerary data will be managed in the backend, initially in memory, and later persisted in a database.

## External Dependencies
- **Existing:** `discord.py`, `dotenv`, `mistralai` (will be used in the backend)
- **New (Frontend):** `react`, `react-dom`, `typescript`, `tailwindcss`, `socket.io-client`, `react-router-dom`, `leaflet`, `react-leaflet`
- **New (Backend):** `fastapi`, `uvicorn`, `python-socketio`, `requests` (for external API calls), database driver (e.g., `psycopg2` for PostgreSQL or `pymongo` for MongoDB - future)

## Recent Significant Changes
- Creation of the `cline_docs` directory and initial documentation files (`projectRoadmap.md`, `currentTask.md`, `techStack.md`, `codebaseSummary.md`).

## User Feedback Integration and Its Impact on Development
- User feedback has guided the technology stack selection (React + FastAPI) and the initial focus on the chat interface with a pink theme. The use of free APIs is also a direct result of user input.
