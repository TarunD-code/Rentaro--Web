import React, { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Paper, 
  List, 
  ListItemButton, 
  ListItemText, 
  alpha, 
  useTheme,
  Button
} from '@mui/material';
import { Search, LocationOn } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { fetchSuggestions } from '../api/properties';
import { motion, AnimatePresence } from 'framer-motion';

const HeroSearch: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim()) {
        const data = await fetchSuggestions(query);
        setSuggestions(data);
        setShowSuggestions(true);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSearch = (q: string, lat?: number, lon?: number) => {
    let url = `/listings?q=${encodeURIComponent(q)}`;
    if (lat !== undefined && lon !== undefined) {
      url += `&lat=${lat}&lng=${lon}`;
    }
    navigate(url);
    setShowSuggestions(false);
  };

  return (
    <Box 
      sx={{ 
        width: '100%', 
        maxWidth: 700, 
        position: 'relative',
        zIndex: 1000 
      }}
    >
      <Paper 
        elevation={0}
        sx={{ 
          p: 1, 
          borderRadius: 8, 
          display: 'flex', 
          alignItems: 'center',
          bgcolor: 'background.paper',
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 20px 40px -10px rgba(0,0,0,0.1)'
        }}
      >
        <TextField 
          autoComplete="off"
          placeholder="Where are you moving to?"
          variant="standard"
          fullWidth
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && setShowSuggestions(true)}
          sx={{ ml: 2, '& .MuiInput-root::before, & .MuiInput-root::after': { display: 'none' } }}
          InputProps={{
            startAdornment: <Search sx={{ color: 'text.secondary', mr: 1 }} />,
          }}
        />
        <Button 
          variant="contained" 
          onClick={() => handleSearch(query)}
          sx={{ 
            borderRadius: 6, 
            px: 4, 
            height: 48, 
            boxShadow: 'none',
            '&:hover': { boxShadow: 'none' }
          }}
        >
          Search
        </Button>
      </Paper>

      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            style={{ position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 12 }}
          >
            <Paper 
              sx={{ 
                borderRadius: 4, 
                overflow: 'hidden', 
                border: `1px solid ${theme.palette.divider}`,
                boxShadow: theme.shadows[4]
              }}
            >
              <List sx={{ py: 0 }}>
                {suggestions.map((s, i) => (
                  <ListItemButton 
                    key={i} 
                    onClick={() => handleSearch(s.name, s.lat, s.lon)}
                    sx={{ py: 2, '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.05) } }}
                  >
                    <LocationOn sx={{ mr: 2, color: 'text.secondary', fontSize: 20 }} />
                    <ListItemText primary={s.name} />
                  </ListItemButton>
                ))}
              </List>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

export default HeroSearch;
