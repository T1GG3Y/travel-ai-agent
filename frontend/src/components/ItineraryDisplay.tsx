import React from 'react';

interface ItineraryDisplayProps {
  itinerary: string;
}

const ItineraryDisplay: React.FC<ItineraryDisplayProps> = ({ itinerary }) => {
  // Basic formatting: split by lines and display as paragraphs or list items
  const formattedItinerary = itinerary.split('\n').map((line, index) => {
    // Simple heuristic to detect potential list items or headings
    if (line.trim().startsWith('- ')) {
      return <li key={index} className="ml-4">{line.trim().substring(2)}</li>;
    } else if (line.trim().endsWith(':')) {
        return <p key={index} className="mt-2 font-semibold">{line.trim()}</p>;
    }
    else {
      return <p key={index} className="mt-1">{line.trim()}</p>;
    }
  });

  return (
    <div className="bg-soft-pink text-text-gray p-3 rounded-lg max-w-xs overflow-y-auto">
      <strong>Detailed Itinerary:</strong>
      <ul className="list-none p-0 m-0">
        {formattedItinerary}
      </ul>
    </div>
  );
};

export default ItineraryDisplay;
