import { createTheme, alpha } from '@mui/material/styles';

export type PaletteVariant = 
  | 'trust' | 'modern' | 'luxury' | 'minimal' | 'warm' 
  | 'cool' | 'bold' | 'earthy' | 'pastel' | 'dark';

export interface PaletteTokens {
  primary: string;
  secondary: string;
  background: string;
  paper: string;
  text: string;
  alert: string;
}

export const palettes: Record<PaletteVariant, PaletteTokens> = {
  trust: {
    primary: '#0A3D62',
    secondary: '#1ABC9C',
    background: '#FFFFFF',
    paper: '#F5F5F5',
    text: '#2C3E50',
    alert: '#E74C3C',
  },
  modern: {
    primary: '#3F51B5',
    secondary: '#A4C639',
    background: '#ECF0F1',
    paper: '#FFFFFF',
    text: '#2C3E50',
    alert: '#FF9800',
  },
  luxury: {
    primary: '#001F3F',
    secondary: '#FFD700',
    background: '#FAF3E0',
    paper: '#FFFFFF',
    text: '#2F3A44',
    alert: '#800020',
  },
  minimal: {
    primary: '#000000',
    secondary: '#87CEEB',
    background: '#FFFFFF',
    paper: '#F9F9F9',
    text: '#000000',
    alert: '#FF7F50',
  },
  warm: {
    primary: '#228B22',
    secondary: '#F5F5DC',
    background: '#F5F5DC',
    paper: '#FFFFFF',
    text: '#2E3B2B',
    alert: '#E2725B',
  },
  cool: {
    primary: '#191970',
    secondary: '#00FFFF',
    background: '#F0FFFF',
    paper: '#FFFFFF',
    text: '#0B1A3A',
    alert: '#6A5ACD', // Darker lavender for contrast
  },
  bold: {
    primary: '#DC143C',
    secondary: '#7DF9FF',
    background: '#0A0A0A',
    paper: '#111111',
    text: '#FFFFFF',
    alert: '#39FF14',
  },
  earthy: {
    primary: '#808000',
    secondary: '#8A9A5B',
    background: '#C2B280',
    paper: '#FFFFFF',
    text: '#3B2F2F',
    alert: '#87CEEB',
  },
  pastel: {
    primary: '#FFB6C1',
    secondary: '#98FF98',
    background: '#FFF8F0',
    paper: '#FFFFFF',
    text: '#2C3E50',
    alert: '#FFDAB9',
  },
  dark: {
    primary: '#0A0A0A',
    secondary: '#00FFFF',
    background: '#0A0A0A',
    paper: '#111111',
    text: '#FFFFFF',
    alert: '#FF2400',
  },
};

export const getTheme = (variant: PaletteVariant = 'trust') => {
  const tokens = palettes[variant] || palettes['trust'];
  
  return createTheme({
    palette: {
      mode: (variant === 'bold' || variant === 'dark') ? 'dark' : 'light',
      primary: {
        main: tokens.primary,
        contrastText: '#fff',
      },
      secondary: {
        main: tokens.secondary,
      },
      error: {
        main: tokens.alert,
      },
      background: {
        default: tokens.background,
        paper: tokens.paper,
      },
      text: {
        primary: tokens.text,
        secondary: alpha(tokens.text, 0.7),
      },
      divider: alpha(tokens.text, 0.1),
    },
    typography: {
      fontFamily: '"Roboto", "Open Sans", "Helvetica", "Arial", sans-serif',
      h1: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 700 },
      h2: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 600 },
      h3: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 600 },
      h4: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 600 },
      h5: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 500 },
      h6: { fontFamily: '"Inter", "Poppins", sans-serif', fontWeight: 500 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: tokens.background,
            color: tokens.text,
            transition: 'background-color 0.3s ease, color 0.3s ease',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: '10px 24px',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            },
            transition: 'all 0.3s ease',
          },
          containedPrimary: {
            background: `linear-gradient(45deg, ${tokens.primary} 30%, ${alpha(tokens.primary, 0.8)} 90%)`,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            backgroundColor: tokens.paper,
            border: `1px solid ${alpha(tokens.text, 0.1)}`,
            boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
            transition: 'transform 0.3s ease, box-shadow 0.3s ease',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: alpha(tokens.background, 0.8),
            backdropFilter: 'blur(10px)',
            borderBottom: `1px solid ${alpha(tokens.text, 0.1)}`,
            color: tokens.text,
          },
        },
      },
    },
  });
};
