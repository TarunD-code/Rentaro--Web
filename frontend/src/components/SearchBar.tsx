import React, { useState, useRef, useLayoutEffect, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  InputAdornment, 
  Paper, 
  Typography,
  useTheme,
  alpha
} from '@mui/material';
import { Search, Map as MapIcon } from '@mui/icons-material';
import Portal from './Portal';

interface SearchBarProps {
  value: string;
  onChange: (val: string) => void;
  onSearch: () => void;
  suggestions: any[];
  onSuggestionSelect: (s: any) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  value, 
  onChange, 
  onSearch, 
  suggestions, 
  onSuggestionSelect 
}) => {
  const theme = useTheme();
  const inputRef = useRef<HTMLDivElement>(null);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  // Update position of suggestions menu
  const updateRect = () => {
    if (inputRef.current) {
      setRect(inputRef.current.getBoundingClientRect());
    }
  };

  useLayoutEffect(() => {
    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, []);

  // Map pointer-events control
  useEffect(() => {
    const isVisible = showSuggestions && suggestions.length > 0;
    const mapEl = document.querySelector('.map-canvas') as HTMLElement;
    if (mapEl) {
      mapEl.style.pointerEvents = isVisible ? 'none' : 'auto';
    }
    return () => {
      if (mapEl) mapEl.style.pointerEvents = 'auto';
    };
  }, [showSuggestions, suggestions]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0) {
        onSuggestionSelect(suggestions[activeIndex]);
        setShowSuggestions(false);
        setActiveIndex(-1);
      } else {
        onSearch();
        setShowSuggestions(false);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <Box className="search-bar-wrapper" sx={{ flex: 4, position: 'relative', zIndex: 1000 }} ref={inputRef}>
      <TextField 
        placeholder="Search locations, building names..."
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowSuggestions(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        onKeyDown={handleKeyDown}
        autoComplete="off"
        fullWidth
        sx={{ '& .MuiOutlinedInput-root': { bgcolor: alpha(theme.palette.background.default, 0.4) } }}
        InputProps={{
          startAdornment: <InputAdornment position="start"><Search /></InputAdornment>,
        }}
      />
      
      {showSuggestions && suggestions.length > 0 && rect && (
        <Portal id="search-suggestions-portal-root">
          <Paper 
            className="search-suggestions-portal"
            elevation={12}
            sx={{ 
              position: 'absolute', 
              top: rect.bottom + window.scrollY + 8, 
              left: rect.left + window.scrollX, 
              width: rect.width,
              zIndex: 1100,
              pointerEvents: 'auto',
              maxHeight: '400px',
              overflowY: 'auto',
              borderRadius: 3,
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: '0 10px 30px rgba(0,0,0,0.15)'
            }}
          >
            {suggestions.map((s, i) => (
              <Box 
                 key={i} 
                 onClick={() => {
                   onSuggestionSelect(s);
                   setShowSuggestions(false);
                 }}
                 sx={{ 
                   p: 2, 
                   cursor: 'pointer', 
                   bgcolor: i === activeIndex ? 'action.hover' : 'transparent',
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
        </Portal>
      )}
    </Box>
  );
};

export default SearchBar;
