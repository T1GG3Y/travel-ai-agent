import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet'; // Import Leaflet library

// Fix for default marker icon
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});


interface MapViewProps {
  center: [number, number] | null;
  pointsOfInterest: any[]; // Add pointsOfInterest prop
}

const ChangeView: React.FC<{ center: [number, number] | null }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
};

const MapView: React.FC<MapViewProps> = ({ center, pointsOfInterest }) => {
  const defaultPosition: [number, number] = [51.505, -0.09]; // Default position (e.g., London)

  return (
    <MapContainer center={center || defaultPosition} zoom={13} style={{ height: '400px', width: '100%' }}>
      <ChangeView center={center} /> {/* Component to change view */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {center && (
        <Marker position={center}>
          <Popup>
            AI Recommended Location <br /> Coordinates: {center[0]}, {center[1]}
          </Popup>
        </Marker>
      )}
      {pointsOfInterest.map((poi, index) => (
        // Ensure the point of interest has valid coordinates
        poi.lat && poi.lon && (
          <Marker key={index} position={[poi.lat, poi.lon]}>
            <Popup>
              <strong>{poi.tags.name || poi.type + ' ' + poi.id}</strong><br />
              {poi.tags.tourism || poi.tags.amenity || poi.tags.shop}
            </Popup>
          </Marker>
        )
      ))}
    </MapContainer>
  );
};

export default MapView;
