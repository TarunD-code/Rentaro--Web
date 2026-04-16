import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  TextField, 
  InputAdornment, 
  Button, 
  ToggleButton, 
  ToggleButtonGroup,
  useTheme,
  alpha,
  Paper,
  Chip,
  FormControlLabel,
  Checkbox,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormGroup
} from '@mui/material';
import { 
  Search, 
  GridView, 
  Map as MapIcon, 
  Tune
} from '@mui/icons-material';
import { useSearchParams } from 'react-router-dom';
import PropertyCard from '../components/PropertyCard';
import MapPopupCard from '../components/MapPopupCard';
import { PropertyGridSkeleton } from '../components/SkeletonLoader';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
const DefaultIcon = L.icon({
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

const Listings: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  
  const [properties, setProperties] = useState<any[]>([]);
  const [pois, setPois] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<number[]>([0, 200000]);
  const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [otherAmenity, setOtherAmenity] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [isFurnished, setIsFurnished] = useState(false);
  const [isPetFriendly, setIsPetFriendly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>([19.0760, 72.8777]);
  const [mapZoom, setMapZoom] = useState(11);

  useEffect(() => {
    const lat = searchParams.get('lat');
    const lng = searchParams.get('lng');
    const q = searchParams.get('q');

    if (lat && lng) {
      const coords: [number, number] = [parseFloat(lat), parseFloat(lng)];
      setMapCenter(coords);
      setViewMode('map');
      fetchPois(coords[0], coords[1]);
    } else if (q) {
      setSearchQuery(q);
    }

    if (navigator.geolocation && !lat && viewMode === 'map') {
      navigator.geolocation.getCurrentPosition(
        (position) => setMapCenter([position.coords.latitude, position.coords.longitude]),
        () => console.log("Geolocation access denied or unavailable.")
      );
    }
  }, [searchParams, viewMode]);

  const fetchPois = async (lat: number, lng: number) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/property/location/pois?lat=${lat}&lng=${lng}`);
      if (res.ok) {
        const data = await res.json();
        setPois(data.pois || []);
      }
    } catch (err) {
      console.error("POI Fetch Error", err);
    }
  };

  const fetchProperties = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      params.append('min_price', priceRange[0].toString());
      params.append('max_price', priceRange[1].toString());
      if (propertyTypes.length) params.append('property_type', propertyTypes.join(','));
      if (selectedAmenities.length || otherAmenity) {
        const allAm = [...selectedAmenities];
        if (otherAmenity) allAm.push(otherAmenity);
        params.append('amenities', allAm.join(','));
      }
      if (availableFrom) params.append('available_from', availableFrom);
      if (isFurnished) params.append('furnished', 'true');
      if (isPetFriendly) params.append('pet_friendly', 'true');

      const response = await fetch(`${import.meta.env.VITE_API_URL}/property/?${params.toString()}`);
      const data = await response.json();
      if (response.ok) setProperties(data);
    } catch (err) {
      console.error('Fetch Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFavorites = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/property/favorites`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) setFavorites(data);
    } catch (err) {
      console.error('Fav Fetch Error:', err);
    }
  };

  const fetchSuggestions = async (q: string) => {
    if (!q) {
      setSuggestions([]);
      return;
    }
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/property/search/suggestions?q=${q}`);
      const data = await response.json();
      if (response.ok) setSuggestions(data);
    } catch (err) {
      console.error('Suggestions Error:', err);
    }
  };

  useEffect(() => {
    fetchProperties();
    fetchFavorites();
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSuggestions(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleToggleFavorite = async (propertyId: number) => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const isFav = favorites.includes(propertyId);
    // Optimistic UI
    setFavorites(prev => isFav ? prev.filter(id => id !== propertyId) : [...prev, propertyId]);

    try {
      await fetch(`${import.meta.env.VITE_API_URL}/property/favorites/${propertyId}`, {
        method: isFav ? 'DELETE' : 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (err) {
      // Rollback
      setFavorites(prev => isFav ? [...prev, propertyId] : prev.filter(id => id !== propertyId));
    }
  };

  const handleViewChange = (_: React.MouseEvent<HTMLElement>, nextView: 'grid' | 'map' | null) => {
    if (nextView) setViewMode(nextView);
  };

  const filteredProperties = properties.filter(p => 
    p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    p.address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Box sx={{ py: 2 }}>
      {/* Search and Filters Header */}
      <Paper 
        elevation={0}
        sx={{ 
          p: 3, 
          mb: 5, 
          borderRadius: 6,
          bgcolor: alpha(theme.palette.background.paper, 0.4),
          backdropFilter: 'blur(10px)',
          border: `1px solid ${theme.palette.divider}`,
          display: 'flex',
          flexDirection: 'column',
          gap: 3
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {t('browse_listings')}
          </Typography>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={handleViewChange}
            size="small"
            aria-label="view toggle"
            sx={{ 
              px: 0.5, 
              bgcolor: alpha(theme.palette.divider, 0.3), 
              borderRadius: '12px',
              '& .Mui-selected': {
                bgcolor: `${theme.palette.primary.main} !important`,
                color: '#fff !important',
                borderRadius: '10px !important'
              }
            }}
          >
            <ToggleButton value="grid" aria-label="grid view" sx={{ borderRadius: '10px !important', px: 2 }}>
              <GridView fontSize="small" sx={{ mr: 1 }} /> Grid
            </ToggleButton>
            <ToggleButton value="map" aria-label="map view" sx={{ borderRadius: '10px !important', px: 2 }}>
              <MapIcon fontSize="small" sx={{ mr: 1 }} /> Map
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box display="flex" gap={2} flexWrap="wrap" position="relative">
          <TextField 
            placeholder="Search locations, building names..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && fetchProperties()}
            autoComplete="off"
            sx={{ flex: 4, '& .MuiOutlinedInput-root': { bgcolor: alpha(theme.palette.background.default, 0.4) } }}
            InputProps={{
              startAdornment: <InputAdornment position="start"><Search /></InputAdornment>,
            }}
          />
          
          {suggestions.length > 0 && (
            <Paper 
              sx={{ 
                position: 'absolute', 
                top: '100%', 
                left: 0, 
                width: { xs: '100%', md: 'calc(80% - 16px)' }, 
                zIndex: 2000, 
                borderRadius: 3, 
                boxShadow: theme.shadows[8],
                mt: 1,
                overflow: 'hidden',
                border: `1px solid ${theme.palette.divider}`
              }}
            >
              {(suggestions as any[]).map((s, i) => (
                <Box 
                   key={i} 
                   onClick={() => {
                     setSearchQuery(s.name);
                     setSuggestions([]);
                     if (s.lat && s.lon) {
                       const lat = parseFloat(s.lat);
                       const lon = parseFloat(s.lon);
                       setMapCenter([lat, lon]);
                       setMapZoom(16); // High zoom for exact location
                       // Fix: Only fetch POIs if in map view, don't force switch view
                       if (viewMode === 'map') {
                         fetchPois(lat, lon);
                       }
                     }
                     setTimeout(fetchProperties, 100);
                   }}
                   sx={{ 
                     p: 2, 
                     cursor: 'pointer', 
                     '&:hover': { bgcolor: 'action.hover' }, 
                     borderBottom: i < suggestions.length - 1 ? '1px solid' : 'none', 
                     borderColor: 'divider',
                     display: 'flex',
                     alignItems: 'center',
                     gap: 2
                   }}
                >
                   <MapIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                   <Typography variant="body2">{s.name}</Typography>
                </Box>
              ))}
            </Paper>
          )}

          <Button 
            variant={showFilters ? "contained" : "outlined"}
            disableElevation
            startIcon={<Tune />}
            onClick={() => setShowFilters(!showFilters)}
            sx={{ flex: 1, height: 56, borderRadius: '12px', borderColor: theme.palette.divider }}
          >
            Filters
          </Button>
        </Box>

        {showFilters && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}>
            <Box display="flex" gap={4} p={3} mb={3} bgcolor={alpha(theme.palette.primary.main, 0.03)} borderRadius={4} flexWrap="wrap" sx={{ border: `1px solid ${alpha(theme.palette.divider, 0.5)}` }}>
              
              {/* Price Slider */}
              <Box display="flex" flexDirection="column" gap={1} flex={1} minWidth={200}>
                <Typography variant="caption" color="text.secondary" fontWeight={600}>Price Range (â‚¹)</Typography>
                <Slider
                  value={priceRange}
                  onChange={(_, newValue) => setPriceRange(newValue as number[])}
                  valueLabelDisplay="auto"
                  min={0}
                  max={200000}
                  step={5000}
                  sx={{ mx: 1, width: 'calc(100% - 16px)' }}
                />
              </Box>

              {/* Property Type Multi-select */}
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Property Type</InputLabel>
                <Select
                  multiple
                  value={propertyTypes}
                  onChange={(e) => setPropertyTypes(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                  label="Property Type"
                >
                  {['Apartment', 'Villa', 'Studio', 'Penthouse'].map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Date Filter */}
              <TextField
                label="Available From"
                type="date"
                size="small"
                InputLabelProps={{ shrink: true }}
                value={availableFrom}
                onChange={(e) => setAvailableFrom(e.target.value)}
              />

              {/* Advanced Flags */}
              <Box display="flex" alignItems="center" gap={1}>
                <FormControlLabel control={<Checkbox checked={isFurnished} onChange={(e) => setIsFurnished(e.target.checked)} size="small" />} label="Furnished" />
                <FormControlLabel control={<Checkbox checked={isPetFriendly} onChange={(e) => setIsPetFriendly(e.target.checked)} size="small" />} label="Pet-Friendly" />
              </Box>

              {/* Amenities Checkboxes */}
              <Box width="100%">
                <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" mb={1}>Amenities Requirements</Typography>
                <FormGroup row>
                  {['Pool', 'Gym', 'Parking', 'CCTV', 'Generator', 'Lift', 'Garden'].map((amenity) => (
                    <FormControlLabel 
                       key={amenity}
                       control={
                         <Checkbox 
                           size="small" 
                           checked={selectedAmenities.includes(amenity)}
                           onChange={(e) => {
                              if (e.target.checked) setSelectedAmenities([...selectedAmenities, amenity]);
                              else setSelectedAmenities(selectedAmenities.filter(a => a !== amenity));
                           }}
                         />
                       } 
                       label={<Typography variant="body2">{amenity}</Typography>} 
                    />
                  ))}
                </FormGroup>
                <TextField 
                  size="small" 
                  placeholder="Other (specify)" 
                  value={otherAmenity} 
                  onChange={(e) => setOtherAmenity(e.target.value)} 
                  sx={{ mt: 1, width: 200 }}
                />
              </Box>

              {/* Action Buttons */}
              <Box width="100%" display="flex" gap={2} mt={1}>
                <Button variant="contained" onClick={fetchProperties} sx={{ borderRadius: 3, px: 4 }}>Apply Filters</Button>
                <Button 
                  onClick={() => { 
                    setPriceRange([0, 200000]); setPropertyTypes([]); setSelectedAmenities([]); 
                    setOtherAmenity(''); setAvailableFrom(''); setIsFurnished(false); setIsPetFriendly(false); 
                    setSearchQuery(''); fetchProperties(); 
                  }}
                  sx={{ borderRadius: 3 }}
                >
                  Reset All
                </Button>
              </Box>
            </Box>
          </motion.div>
        )}

        <Box display="flex" gap={1} flexWrap="wrap">
          <Typography variant="body2" sx={{ mr: 1, py: 0.5, fontWeight: 600 }}>Quick Filters:</Typography>
          {['Apartment', 'Villa', 'Studio', 'Parking', 'Pool'].map((filter, i) => (
             <Chip 
               key={i} 
               label={filter} 
               size="small" 
               variant="outlined" 
               clickable 
               sx={{ borderRadius: 6 }} 
               onClick={() => {
                 if (['Apartment', 'Villa', 'Studio'].includes(filter)) {
                   setPropertyTypes([filter]);
                 } else {
                   setSelectedAmenities([filter]);
                 }
                 setTimeout(fetchProperties, 100);
               }}
             />
          ))}
        </Box>
      </Paper>

      {/* Content Area */}
      {loading ? (
        <PropertyGridSkeleton />
      ) : viewMode === 'grid' ? (
        <AnimatePresence>
          <Grid container spacing={4}>
            {filteredProperties.map((property, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={property.id}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <PropertyCard 
                    property={property} 
                    isLiked={favorites.includes(property.id)}
                    onLike={() => handleToggleFavorite(property.id)}
                  />
                </motion.div>
              </Grid>
            ))}
            {filteredProperties.length === 0 && (
              <Box sx={{ width: '100%', py: 10, textAlign: 'center', opacity: 0.5 }}>
                <Search sx={{ fontSize: 48, mb: 2 }} />
                <Typography variant="h6">No properties found matching your search</Typography>
              </Box>
            )}
          </Grid>
        </AnimatePresence>
      ) : (
        /* Live Map View */
        <Box 
          sx={{ 
            height: '600px', 
            borderRadius: 6, 
            overflow: 'hidden',
            border: `1px solid ${theme.palette.divider}`,
            position: 'relative',
            bgcolor: 'background.paper'
          }}
        >
          <MapContainer center={mapCenter} zoom={mapZoom} style={{ height: '100%', width: '100%', zIndex: 0 }}>
            <MapUpdater center={mapCenter} zoom={mapZoom} />
            <TileLayer
              attribution='&copy; <a href="https://www.maptiler.com/">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url={`https://api.maptiler.com/maps/streets-v2/256/{z}/{x}/{y}.png?key=${import.meta.env.VITE_MAPTILER_KEY || 'mock_key'}`}
            />
            
            {/* Property Markers */}
            <MarkerClusterGroup>
              {filteredProperties.map((property) => {
                const lat = property.address_geo_lat || (mapCenter[0] + (Math.random() - 0.5) * 0.05);
                const lng = property.address_geo_lng || (mapCenter[1] + (Math.random() - 0.5) * 0.05);
                return (
                  <Marker key={property.id} position={[lat, lng]}>
                    <Popup closeButton={false} className="custom-property-popup">
                      <MapPopupCard property={property} />
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
      )}
    </Box>
  );
};

export default Listings;
