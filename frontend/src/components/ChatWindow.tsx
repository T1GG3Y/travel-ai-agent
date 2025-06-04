import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import MapView from './MapView'; // Import MapView
import ItineraryDisplay from './ItineraryDisplay'; // Import ItineraryDisplay

const socket = io('http://localhost:8000'); // Keep WebSocket for potential future use

const ChatWindow: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<{ text: string; sender: 'user' | 'ai' }[]>([]);
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null); // State for map center
  const [weatherData, setWeatherData] = useState<any>(null); // State for weather data
  const [pointsOfInterest, setPointsOfInterest] = useState<any[]>([]); // State for points of interest
  const [recommendedTrips, setRecommendedTrips] = useState<any[]>([]); // State for recommended trips
  const [sessionId, setSessionId] = useState<number | null>(null); // State for session ID
  const [itinerary, setItinerary] = useState<string | null>(null); // State for itinerary

  // Optional: Keep WebSocket connection open for real-time features later
  useEffect(() => {
    // Generate a simple session ID on component mount
    if (sessionId === null) {
        setSessionId(Math.floor(Math.random() * 1000000)); // Simple random ID for now
    }

    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    // Example of receiving a message via WebSocket (if backend sends any)
    socket.on('message', (msg: string) => {
       console.log('Received WebSocket message:', msg);
       // setMessages((prevMessages) => [...prevMessages, { text: `WebSocket: ${msg}`, sender: 'ai' }]);
    });


    return () => {
      socket.disconnect();
    };
  }, [sessionId]); // Add sessionId to dependency array

  const sendMessage = async () => {
    if (message.trim()) {
      const userMessage = message;
      setMessages((prevMessages) => [...prevMessages, { text: userMessage, sender: 'user' }]);
      setMessage('');

      try {
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessage }),
        });

        if (response.ok) {
          const data = await response.json();
          const aiResponseText = data.response;
          const placesData = data.points_of_interest; // Get points of interest data
          const locationCoords = data.location_coords; // Get location coordinates
          const recommendedTripsData = data.recommended_trips; // Get recommended trips data

          setMessages((prevMessages) => [...prevMessages, { text: aiResponseText, sender: 'ai' }]);

          if (locationCoords) {
             setMapCenter(locationCoords as [number, number]); // Update map center
             fetchWeatherData(locationCoords[0], locationCoords[1]); // Fetch weather data
          } else if (data.location) {
              // If AI provided location name but not coords, try geocoding
              fetchLocationCoordinates(data.location);
          }

          if (placesData && Array.isArray(placesData)) {
            setPointsOfInterest(placesData); // Set points of interest data
            console.log("Received points of interest:", placesData);
          } else {
             setPointsOfInterest([]); // Clear previous points of interest if no data or invalid format
          }

          // Handle recommended trips from chat endpoint (if AI provides them here)
          if (recommendedTripsData && Array.isArray(recommendedTripsData)) {
              setRecommendedTrips(recommendedTripsData);
              setMessages((prevMessages) => [...prevMessages, { text: "Here are some trip recommendations:", sender: 'ai' }]);
              // TODO: Display recommendations in a user-friendly format in chat
          }


        } else {
          setMessages((prevMessages) => [...prevMessages, { text: 'Error: Could not get response from AI.', sender: 'ai' }]);
        }
      } catch (error) {
        console.error('Error sending message:', error);
        setMessages((prevMessages) => [...prevMessages, { text: 'Error: Could not connect to backend.', sender: 'ai' }]);
      }
    }
  };

  const fetchLocationCoordinates = async (locationName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/geocode?location=${encodeURIComponent(locationName)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.latitude && data.longitude) {
          const newCenter: [number, number] = [data.latitude, data.longitude];
          setMapCenter(newCenter);
          fetchWeatherData(newCenter[0], newCenter[1]); // Fetch weather data
        } else {
          console.error("Geocoding error:", data.error);
        }
      } else {
        console.error("Geocoding API error:", response.statusText);
      }
    } catch (error) {
      console.error("Error fetching geocode data:", error);
    }
  };

  const fetchWeatherData = async (lat: number, lon: number) => {
    try {
      const response = await fetch(`http://localhost:8000/weather?lat=${lat}&lon=${lon}`);
      if (response.ok) {
        const data = await response.json();
        if (!data.error) {
          setWeatherData(data);
        } else {
          console.error("Weather data error:", data.error);
          setWeatherData(null); // Clear previous weather data on error
        }
      } else {
        console.error("Weather API error:", response.statusText);
        setWeatherData(null); // Clear previous weather data on error
      }
    } catch (error) {
      console.error("Error fetching weather data:", error);
      setWeatherData(null); // Clear previous weather data on error
    }
  };

  // Function to handle submitting preferences (example)
  const submitPreferences = async (prefs: any) => {
      if (sessionId === null) return; // Ensure session ID exists

      try {
          const response = await fetch('http://localhost:8000/submit_preference', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ ...prefs, session_id: sessionId, user: "web_user" }), // Add session ID and a placeholder user
          });

          if (response.ok) {
              const data = await response.json();
              console.log(data.message);
              // Optionally fetch recommendations after submitting preferences
              fetchRecommendations(sessionId);
          } else {
              console.error("Error submitting preferences:", response.statusText);
          }
      } catch (error) {
          console.error("Error submitting preferences:", error);
      }
  };

  // Function to fetch recommendations
  const fetchRecommendations = async (sessionId: number) => {
      try {
          const response = await fetch(`http://localhost:8000/get_recommendations/${sessionId}`);
          if (response.ok) {
              const data = await response.json();
              if (data.recommendations) {
                  setRecommendedTrips(data.recommendations);
                  setMessages((prevMessages) => [...prevMessages, { text: "Here are some trip recommendations:", sender: 'ai' }]);
                  // TODO: Display recommendations in a user-friendly format in chat
              } else if (data.error) {
                  console.error("Error fetching recommendations:", data.error);
                  setRecommendedTrips([]);
              }
          } else {
              console.error("Error fetching recommendations:", response.statusText);
              setRecommendedTrips([]);
          }
      } catch (error) {
          console.error("Error fetching recommendations:", error);
          setRecommendedTrips([]);
      }
  };

  // Function to vote for a trip (example)
  const voteForTrip = async (tripName: string) => {
       if (sessionId === null) return;

       try {
           const response = await fetch('http://localhost:8000/vote_trip', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json',
               },
               body: JSON.stringify({ session_id: sessionId, user: "web_user", trip_name: tripName }),
           });

           if (response.ok) {
               const data = await response.json();
               console.log(data.message);
               // TODO: Update vote count display
           } else {
               console.error("Error voting for trip:", response.statusText);
           }
       } catch (error) {
           console.error("Error voting for trip:", error);
       }
  };

  // Function to finalize a trip (example)
  const finalizeTrip = async () => {
      if (sessionId === null) return;

      try {
          const response = await fetch(`http://localhost:8000/finalize_trip/${sessionId}`);
          if (response.ok) {
              const data = await response.json();
              if (data.itinerary) {
                  setItinerary(data.itinerary); // Set itinerary state
                  setMessages((prevMessages) => [...prevMessages, { text: "Here is the finalized itinerary:", sender: 'ai' }]);
                  // TODO: Display finalized trip and itinerary in a user-friendly format
              } else if (data.error) {
                  console.error("Error finalizing trip:", data.error);
                  setMessages((prevMessages) => [...prevMessages, { text: `Error finalizing trip: ${data.error}`, sender: 'ai' }]);
              }
          } else {
              console.error("Error finalizing trip:", response.statusText);
              setMessages((prevMessages) => [...prevMessages, { text: 'Error finalizing trip.', sender: 'ai' }]);
          }
      } catch (error) {
          console.error("Error finalizing trip:", error);
          setMessages((prevMessages) => [...prevMessages, { text: 'Error finalizing trip.', sender: 'ai' }]);
      }
  };


  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background-blush text-text-gray">
      <MapView center={mapCenter} pointsOfInterest={pointsOfInterest} /> {/* Pass mapCenter and pointsOfInterest */}
      {weatherData && (
        <div className="p-2 bg-soft-pink text-text-gray text-center">
          Weather: {weatherData.weather[0].description}, Temperature: {weatherData.main.temp}°C
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, index) => (
          <div key={index} className={`mb-4 ${msg.sender === 'user' ? 'flex justify-end' : ''}`}>
            <div
              className={`p-3 rounded-lg max-w-xs ${
                msg.sender === 'user'
                  ? 'bg-soft-pink text-text-gray'
                  : 'bg-primary-pink text-white'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
         {pointsOfInterest.length > 0 && (
            <div className="mb-4">
                <div className="bg-soft-pink text-text-gray p-3 rounded-lg max-w-xs">
                    <strong>Points of Interest:</strong>
                    <ul className="list-disc list-inside">
                        {pointsOfInterest.map((poi, index) => (
                            <li key={index}>
                                <strong>{(poi.tags && poi.tags.name) || `Point of Interest ${index + 1}`}</strong>
                                {(poi.tags && poi.tags.tourism) && <span> ({poi.tags.tourism})</span>}
                                {(poi.tags && poi.tags.amenity) && <span> ({poi.tags.amenity})</span>}
                                {(poi.tags && poi.tags.shop) && <span> ({poi.tags.shop})</span>}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        )}

        {/* Placeholder for Recommended Trips and Voting UI */}
        {recommendedTrips.length > 0 && (
             <div className="mb-4">
                <div className="bg-primary-pink text-white p-3 rounded-lg max-w-xs">
                    <strong>Recommended Trips:</strong>
                    <ul className="list-disc list-inside">
                        {recommendedTrips.map((trip, index) => (
                            <li key={index}>
                                <strong>{trip.name}</strong> ({trip.trip_style})
                                <button onClick={() => voteForTrip(trip.name)} className="ml-2 px-2 py-1 bg-white text-primary-pink rounded">Vote</button>
                            </li>
                        ))}
                    </ul>
                    <button onClick={finalizeTrip} className="mt-2 px-4 py-2 bg-accent-pink text-white rounded">Finalize Trip</button>
                </div>
            </div>
        )}

        {/* Display Itinerary */}
        {itinerary && (
            <div className="mb-4">
                <ItineraryDisplay itinerary={itinerary} />
            </div>
        )}

      </div>
      <div className="p-4 bg-white flex">
        <input
          type="text"
          placeholder="Type your message..."
          className="flex-1 p-2 border rounded-l-lg focus:outline-none"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          className="bg-accent-pink text-white p-2 rounded-r-lg hover:bg-primary-pink"
          onClick={sendMessage}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
