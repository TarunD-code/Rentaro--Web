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
  Chip
} from '@mui/material';
import { 
  Search, 
  GridView, 
  Map as MapIcon, 
  Tune,
  LocationOn
} from '@mui/icons-material';
import PropertyCard from '../components/PropertyCard';
import { PropertyGridSkeleton } from '../components/SkeletonLoader';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const Listings: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const [properties, setProperties] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  const fetchProperties = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (minPrice) params.append('min_price', minPrice);
      if (maxPrice) params.append('max_price', maxPrice);

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
                top: 60, 
                left: 0, 
                width: 'calc(80% - 16px)', 
                zIndex: 10, 
                borderRadius: 3, 
                boxShadow: theme.shadows[4],
                overflow: 'hidden'
              }}
            >
              {suggestions.map((s, i) => (
                <Box 
                  key={i} 
                  onClick={() => { setSearchQuery(s); setSuggestions([]); fetchProperties(); }}
                  sx={{ p: 2, cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' }, borderBottom: i < suggestions.length - 1 ? '1px solid' : 'none', borderColor: 'divider' }}
                >
                   <Typography variant="body2">{s}</Typography>
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
            <Box display="flex" gap={3} p={2} bgcolor={alpha(theme.palette.primary.main, 0.05)} borderRadius={4}>
              <TextField 
                label="Min Price" 
                size="small" 
                type="number" 
                value={minPrice} 
                onChange={(e) => setMinPrice(e.target.value)} 
              />
              <TextField 
                label="Max Price" 
                size="small" 
                type="number" 
                value={maxPrice} 
                onChange={(e) => setMaxPrice(e.target.value)} 
              />
              <Button variant="contained" size="small" onClick={fetchProperties}>Apply</Button>
              <Button size="small" onClick={() => { setMinPrice(''); setMaxPrice(''); setSearchQuery(''); fetchProperties(); }}>Reset</Button>
            </Box>
          </motion.div>
        )}

        <Box display="flex" gap={1} flexWrap="wrap">
          <Typography variant="body2" sx={{ mr: 1, py: 0.5, fontWeight: 600 }}>Quick Filters:</Typography>
          {['Apartment', 'Villa', 'Studio', '< 20k', 'Pet Friendly'].map((filter, i) => (
             <Chip key={i} label={filter} size="small" variant="outlined" clickable sx={{ borderRadius: 6 }} />
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
        /* Mock Map View */
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
          <Box 
             sx={{ 
               width: '100%', 
               height: '100%', 
               background: 'transparent',
               display: 'flex',
               alignItems: 'center',
               justifyContent: 'center',
               flexDirection: 'column'
             }}
          >
             <MapIcon sx={{ fontSize: 80, mb: 2, opacity: 0.3 }} />
             <Typography variant="h6" fontWeight={700} color="text.secondary">Interactive Map View</Typography>
             <Typography variant="body2" color="text.secondary">Mock map integration for this phase.</Typography>
             
             {[1, 2, 3, 4, 5].map((_, i) => (
               <Box 
                 key={i}
                 sx={{ 
                   position: 'absolute', 
                   top: `${20 + i * 15}%`, 
                   left: `${30 + i * 12}%`,
                   bgcolor: 'primary.main',
                   color: '#fff',
                   px: 1.5,
                   py: 0.5,
                   borderRadius: 4,
                   boxShadow: 4,
                   display: 'flex',
                   alignItems: 'center',
                   gap: 0.5
                 }}
               >
                 <LocationOn sx={{ fontSize: 16 }} />
                 <Typography variant="caption" fontWeight="bold">₹ {20+i}k</Typography>
               </Box>
             ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Listings;
