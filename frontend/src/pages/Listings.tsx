import React, { useState, useEffect } from 'react';import { 
  Box, 
  Typography, 
  Grid, 
  TextField, 
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
// MapPopupCard available for future map popup integration
import { PropertyGridSkeleton } from '../components/SkeletonLoader';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import SearchBar from '../components/SearchBar';
import MapView from '../components/MapView';

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
  const [distance, _setDistance] = useState(5);
  const [_verifiedOnly, _setVerifiedOnly] = useState(false);
  const [_petFriendly, _setPetFriendly] = useState(false);
  const [_furnished, _setFurnished] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<number[]>([0, 600000]);
  const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [otherAmenity, setOtherAmenity] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [isFurnished, setIsFurnished] = useState(false);
  const [isPetFriendly, setIsPetFriendly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [rankingProfile, setRankingProfile] = useState<string>('default');
  const [mapCenter, setMapCenter] = useState<[number, number]>([12.9716, 77.5946]); // Default: Bengaluru
  const [mapZoom, setMapZoom] = useState(12);

  // Debounced bounding-box fetch — fires when map stops moving.
  // Replaces the centre-based radius search with a true viewport query so only
  // pins visible on screen are loaded (no off-screen network waste).
  const boundsTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleBoundsChange = React.useCallback(
    (bounds: { minLat: number; minLng: number; maxLat: number; maxLng: number }) => {
      // Debounce: wait 400 ms after the last moveend before firing the request
      if (boundsTimerRef.current) clearTimeout(boundsTimerRef.current);
      boundsTimerRef.current = setTimeout(async () => {
        try {
          const { minLat, minLng, maxLat, maxLng } = bounds;
          const response = await fetch(
            `${import.meta.env.VITE_API_URL}/search/properties`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                min_lat: minLat, min_lng: minLng,
                max_lat: maxLat, max_lng: maxLng,
                min_price: priceRange[0],
                max_price: priceRange[1],
                ...(propertyTypes.length ? { property_type: propertyTypes[0] } : {}),
                ...(isFurnished ? { furnished: true } : {}),
                ...(isPetFriendly ? { pet_friendly: true } : {}),
                ranking_profile: rankingProfile,
                page: 1,
                page_size: 100,
              }),
            }
          );
          if (response.ok) {
            const data = await response.json();
            setProperties(data.results || []);
          }
        } catch (err) {
          console.error('[MapView] Viewport fetch error:', err);
        }
      }, 400);
    },
    [priceRange, propertyTypes, isFurnished, isPetFriendly, rankingProfile]
  );

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
      let currentCenter = mapCenter;
      if (searchQuery && searchQuery.toLowerCase().includes('bangalore')) {
        currentCenter = [12.9716, 77.5946];
        setMapCenter(currentCenter);
        setMapZoom(13);
        fetchPois(12.9716, 77.5946);
      }
      const payload: any = {
        min_price: priceRange[0],
        max_price: priceRange[1],
        ranking_profile: rankingProfile,
        page: 1,
        page_size: 50
      };
      if (searchQuery) payload.q = searchQuery;
      if (propertyTypes.length) payload.property_type = propertyTypes[0];
      if (isFurnished) payload.furnished = true;
      if (isPetFriendly) payload.pet_friendly = true;
      if (viewMode === 'map' && currentCenter) {
        payload.near_lat = currentCenter[0];
        payload.near_lng = currentCenter[1];
        payload.radius_km = distance;
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/search/properties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok) {
        setProperties(data.results || []);
      }
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
      const response = await fetch(`${import.meta.env.VITE_API_URL}/search/autocomplete?q=${q}`);
      const data = await response.json();
      if (response.ok) setSuggestions(data.suggestions || []);
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
    (p?.title || '').toLowerCase().includes((searchQuery || '').toLowerCase()) || 
    (p?.address || '').toLowerCase().includes((searchQuery || '').toLowerCase())
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
          <SearchBar 
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={fetchProperties}
            suggestions={suggestions}
            onSuggestionSelect={(s: any) => {
              const nameStr = s.term || s.name || '';
              setSearchQuery(nameStr);
              setSuggestions([]);
              if (s.lat && s.lng) {
                let lat = parseFloat(s.lat);
                let lon = parseFloat(s.lng);
                if (nameStr.toLowerCase().includes('bangalore')) {
                  lat = 12.9716;
                  lon = 77.5946;
                }
                setMapCenter([lat, lon]);
                setMapZoom(16);
                if (viewMode === 'map') fetchPois(lat, lon);
              }
              setTimeout(fetchProperties, 100);
            }}
          />

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
                  max={600000}
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

              {/* Ranking Profile Selector */}
              <Box width="100%" mt={2}>
                <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" mb={1}>
                  Intelligent Ranking Profile
                </Typography>
                <Select
                  size="small"
                  value={rankingProfile}
                  onChange={(e) => setRankingProfile(e.target.value)}
                  sx={{ width: 250, bgcolor: 'background.paper' }}
                >
                  <MenuItem value="default">Default Relevance</MenuItem>
                  <MenuItem value="family">Family Friendly</MenuItem>
                  <MenuItem value="student">Student / Budget</MenuItem>
                  <MenuItem value="it_professional">IT Professional (Commute Focus)</MenuItem>
                  <MenuItem value="luxury">Luxury / Premium</MenuItem>
                </Select>
              </Box>

              {/* Action Buttons */}
              <Box width="100%" display="flex" gap={2} mt={1}>
                <Button variant="contained" onClick={fetchProperties} sx={{ borderRadius: 3, px: 4 }}>Apply Filters</Button>
                <Button 
                  onClick={() => { 
                    setPriceRange([0, 600000]); setPropertyTypes([]); setSelectedAmenities([]); 
                    setOtherAmenity(''); setAvailableFrom(''); setIsFurnished(false); setIsPetFriendly(false); 
                    setSearchQuery(''); setRankingProfile('default'); fetchProperties(); 
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

        {/* Bengaluru micro-market quick-jump chips — only shown in map view */}
        {viewMode === 'map' && (
          <Box>
            <Typography variant="body2" sx={{ mr: 1, mb: 1, fontWeight: 600, display: 'inline' }}>
              Jump to:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap" mt={0.5}>
              {[
                { label: 'HSR Layout',      lng: 77.6412, lat: 12.9121 },
                { label: 'Koramangala',     lng: 77.6271, lat: 12.9352 },
                { label: 'Indiranagar',     lng: 77.6413, lat: 12.9784 },
                { label: 'Whitefield',      lng: 77.7499, lat: 12.9698 },
                { label: 'Electronic City', lng: 77.6762, lat: 12.8399 },
                { label: 'Hebbal',          lng: 77.5970, lat: 13.0358 },
              ].map((nb) => (
                <Chip
                  key={nb.label}
                  label={nb.label}
                  size="small"
                  variant="outlined"
                  clickable
                  color="primary"
                  sx={{ borderRadius: 6, fontWeight: 600 }}
                  onClick={() => {
                    // Update center — MapView.flyTo fires via the center useEffect,
                    // then moveend triggers handleBoundsChange to fetch viewport properties.
                    setMapCenter([nb.lat, nb.lng]);
                    setMapZoom(14);
                  }}
                />
              ))}
            </Box>
          </Box>
        )}
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
        <MapView 
          center={mapCenter}
          zoom={mapZoom}
          properties={filteredProperties}
          pois={pois}
          favorites={favorites}
          onLike={handleToggleFavorite}
          onBoundsChange={handleBoundsChange}
        />
      )}
    </Box>
  );
};

export default Listings;
