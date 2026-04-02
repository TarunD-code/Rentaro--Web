import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { getTheme, palettes } from '../theme';
import type { PaletteVariant } from '../theme';

interface ThemeContextType {
  palette: PaletteVariant;
  setPalette: (palette: PaletteVariant) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeContextProvider');
  }
  return context;
};

export const ThemeContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [palette, setPalette] = useState<PaletteVariant>(() => {
    const savedPalette = localStorage.getItem('theme') as PaletteVariant;
    return savedPalette || 'trust';
  });

  // Sync CSS Variables with MUI Theme
  useEffect(() => {
    const tokens = palettes[palette] || palettes['trust'];
    const root = document.documentElement;
    
    root.style.setProperty('--bg-default', tokens.background);
    root.style.setProperty('--bg-paper', tokens.paper);
    root.style.setProperty('--color-primary', tokens.primary);
    root.style.setProperty('--color-secondary', tokens.secondary);
    root.style.setProperty('--text-primary', tokens.text);
    root.style.setProperty('--color-alert', tokens.alert);
    
    localStorage.setItem('theme', palette);
    
    // Also update body background directly to ensure coverage
    document.body.style.backgroundColor = tokens.background;
  }, [palette]);

  const theme = useMemo(() => getTheme(palette), [palette]);

  return (
    <ThemeContext.Provider value={{ palette, setPalette }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};
