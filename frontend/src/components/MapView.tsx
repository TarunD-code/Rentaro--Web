import React, { useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useNavigate } from 'react-router-dom';
import MapPopupCard from './MapPopupCard';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const MapUpdater = ({ center, zoom }: { center: [number, number], zoom: number }) => {
  const map = useMap();
  useEffect(() => {
    if (center[0] !== 0) {
      map.setView(center, zoom, { animate: true });
    }
  }, [center, zoom, map]);
  return null;
};

interface MapViewProps {
  center: [number, number];
  zoom: number;
  properties: any[];
  pois: any[];
  favorites: number[];
  onLike: (id: number) => void;
}

const MapView: React.FC<MapViewProps> = ({ center, zoom, properties, pois, favorites }) => {
  const navigate = useNavigate();

  return (
    <Box 
      className="map-container"
      sx={{ 
        height: '600px', 
        borderRadius: 6, 
        overflow: 'hidden',
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        position: 'relative'
      }}
    >
      <MapContainer 
        center={center} 
        zoom={zoom} 
        style={{ height: '100%', width: '100%' }}
        className="map-canvas"
      >
        <MapUpdater center={center} zoom={zoom} />
        <TileLayer
          attribution='&copy; <a href="https://www.maptiler.com/">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={`https://api.maptiler.com/maps/streets-v2/256/{z}/{x}/{y}.png?key=${import.meta.env.VITE_MAPTILER_KEY || 'mock_key'}`}
        />
        
        {/* Property Markers */}
        <MarkerClusterGroup>
          {properties.map((property) => {
            const lat = property.address?.geo?.lat || property.address_geo_lat || (center[0] + (Math.random() - 0.5) * 0.05);
            const lng = property.address?.geo?.lng || property.address_geo_lng || (center[1] + (Math.random() - 0.5) * 0.05);
            
            return (
              <Marker 
                key={property.id} 
                position={[lat, lng]}
                eventHandlers={{
                  mouseover: (e) => { e.target.openPopup(); },
                  click: () => { navigate(`/property/${property.id}`); }
                }}
              >
                <Popup closeButton={false} className="custom-property-popup" autoPan={false}>
                  <Box sx={{ width: 220, p: 0.5 }}>
                    <MapPopupCard property={property} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        display: 'block', 
                        textAlign: 'center', 
                        mt: 1, 
                        color: 'primary.main', 
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      Click to view details
                    </Typography>
                  </Box>
                </Popup>
              </Marker>
            );
          })}
        </MarkerClusterGroup>

        {/* POI Markers */}
        {pois.map((poi, idx) => (
          <Marker 
            key={`poi-${idx}`} 
            position={[poi.lat, poi.lng]}
            icon={L.divIcon({
              html: `<div style="background: white; border-radius: 50%; padding: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); display: flex; color: ${poi.category === 'metro' ? '#1a73e8' : poi.category === 'hospital' ? '#d93025' : '#5f6368'}">
                ${poi.category === 'metro' ? '<span class="material-icons" style="font-size: 16px">train</span>' : 
                  poi.category === 'hospital' ? '<span class="material-icons" style="font-size: 16px">local_hospital</span>' : 
                  '<span class="material-icons" style="font-size: 16px">place</span>'}
              </div>`,
              className: 'custom-poi-icon',
              iconSize: [24, 24]
            })}
          >
            <Popup>
              <Typography variant="subtitle2">{poi.name}</Typography>
              <Typography variant="caption" color="text.secondary">{poi.category.toUpperCase()}</Typography>
              {poi.distance && <Typography variant="caption" display="block">~{poi.distance}m away</Typography>}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </Box>
  );
};

export default MapView;
