import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  IconButton, 
  Box, 
  Container, 
  useScrollTrigger, 
  Slide, 
  Paper, 
  BottomNavigation, 
  BottomNavigationAction,
  useMediaQuery,
  useTheme,
  Menu,
  MenuItem,
  Avatar,
  Tooltip,
  alpha
} from '@mui/material';
import { 
  AccountCircle, 
  Dashboard as DashboardIcon, 
  Search as ListingsIcon, 
  AddCircle as AddIcon,
  Language,
  ExitToApp
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useThemeContext } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { palettes } from '../theme';
import type { PaletteVariant } from '../theme';
import { Palette as PaletteIcon, Check } from '@mui/icons-material';
import NotificationMenu from './NotificationMenu';

interface Props {
  children: React.ReactNode;
}

function HideOnScroll(props: { children: React.ReactElement }) {
  const { children } = props;
  const trigger = useScrollTrigger();

  return (
    <Slide direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

const Layout: React.FC<Props> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { palette, setPalette } = useThemeContext();
  const { t, i18n } = useTranslation();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [langAnchorEl, setLangAnchorEl] = useState<null | HTMLElement>(null);
  const [paletteAnchorEl, setPaletteAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleLangMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLangAnchorEl(event.currentTarget);
  };

  const handlePaletteMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setPaletteAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setLangAnchorEl(null);
    setPaletteAnchorEl(null);
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    handleMenuClose();
  };

  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    navigate('/login');
    handleMenuClose();
  };

  const isAuthPage = ['/login', '/register', '/verify'].includes(location.pathname);

  const [role, setRole] = useState<string | null>(localStorage.getItem('role'));

  React.useEffect(() => {
    setRole(localStorage.getItem('role'));
  }, [location.pathname]);

  // Define nav items based on role
  const navItems = [
    { label: t('dashboard'), icon: <DashboardIcon />, path: '/dashboard' },
    { label: t('browse_listings'), icon: <ListingsIcon />, path: '/listings' },
    ...((role === 'owner' || role === 'admin') ? 
      [{ label: t('add_property'), icon: <AddIcon />, path: '/create' }] : []),
    { label: t('profile'), icon: <AccountCircle />, path: '/profile' }
  ];

  const currentNavValue = navItems.findIndex(item => location.pathname.startsWith(item.path));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {!isAuthPage && (
        <HideOnScroll>
          <AppBar 
            elevation={0} 
            sx={{ 
              background: alpha(theme.palette?.background?.paper || '#FFFFFF', 0.8),
              backdropFilter: 'blur(10px)',
              borderBottom: `1px solid ${theme.palette?.divider || 'rgba(0,0,0,0.1)'}`,
              color: theme.palette?.text?.primary || '#000000',
              zIndex: (theme) => theme.zIndex.drawer + 1
            }}
          >
            <Container maxWidth="lg">
              <Toolbar disableGutters sx={{ justifyContent: 'space-between' }}>
                <Box 
                  display="flex" 
                  alignItems="center" 
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate('/dashboard')}
                >
                  <Typography 
                    variant="h5" 
                    component="div" 
                    sx={{ 
                      fontWeight: 700, 
                      color: theme.palette?.primary?.main || '#0A3D62',
                      letterSpacing: -0.5
                    }}
                  >
                    Rentora
                  </Typography>
                </Box>

                {!isMobile && (
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button color="inherit" onClick={() => navigate('/dashboard')}>{t('dashboard')}</Button>
                    <Button color="inherit" onClick={() => navigate('/listings')}>{t('browse_listings')}</Button>
                    {(role === 'owner' || role === 'admin') && (
                      <Button 
                        variant="contained" 
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/create')}
                      >
                        {t('add_property')}
                      </Button>
                    )}
                  </Box>
                )}

                <Box display="flex" alignItems="center" gap={1.2}>
                  {!isMobile ? (
                    <Box display="flex" gap={0.8} sx={{ mr: 1 }}>
                      {(Object.keys(palettes) as PaletteVariant[]).map((v) => (
                        <Tooltip key={v} title={v.charAt(0).toUpperCase() + v.slice(1)}>
                          <Box
                            onClick={() => setPalette(v)}
                            sx={{
                              width: 18,
                              height: 18,
                              borderRadius: '50%',
                              bgcolor: palettes[v].primary,
                              cursor: 'pointer',
                              border: palette === v ? `2px solid ${theme.palette.text.primary}` : 'none',
                              outline: palette === v ? `1px solid ${theme.palette.background.paper}` : 'none',
                              transform: palette === v ? 'scale(1.25)' : 'none',
                              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                              boxShadow: palette === v ? `0 0 10px ${alpha(palettes[v].primary, 0.5)}` : 'none',
                              '&:hover': { transform: 'scale(1.4)' }
                            }}
                          />
                        </Tooltip>
                      ))}
                    </Box>
                  ) : (
                    <Tooltip title="Switch Theme Palette">
                      <IconButton onClick={handlePaletteMenuOpen} color="inherit" size="small">
                        <PaletteIcon />
                      </IconButton>
                    </Tooltip>
                  )}

                  <NotificationMenu />

                  <Tooltip title="Change language">
                    <IconButton onClick={handleLangMenuOpen} color="inherit">
                      <Language />
                    </IconButton>
                  </Tooltip>

                  <IconButton
                    edge="end"
                    aria-label="account of current user"
                    aria-haspopup="true"
                    onClick={handleProfileMenuOpen}
                    color="inherit"
                  >
                    <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette?.primary?.main || '#0A3D62' }}>
                      <AccountCircle />
                    </Avatar>
                  </IconButton>
                </Box>
              </Toolbar>
            </Container>
          </AppBar>
        </HideOnScroll>
      )}

      {/* Language Menu */}
      <Menu
        anchorEl={langAnchorEl}
        open={Boolean(langAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => changeLanguage('en')}>English</MenuItem>
        <MenuItem onClick={() => changeLanguage('hi')}>हिन्दी (Hindi)</MenuItem>
        <MenuItem onClick={() => changeLanguage('mr')}>मराठी (Marathi)</MenuItem>
        <MenuItem onClick={() => changeLanguage('ta')}>தமிழ் (Tamil)</MenuItem>
        <MenuItem onClick={() => changeLanguage('te')}>తెలుగు (Telugu)</MenuItem>
        <MenuItem onClick={() => changeLanguage('kn')}>ಕನ್ನಡ (Kannada)</MenuItem>
        <MenuItem onClick={() => changeLanguage('ml')}>മലയാളം (Malayalam)</MenuItem>
        <MenuItem onClick={() => changeLanguage('bn')}>বাংলা (Bengali)</MenuItem>
      </Menu>

      {/* Palette Menu for Mobile */}
      <Menu
        anchorEl={paletteAnchorEl}
        open={Boolean(paletteAnchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { width: 200, mt: 1.5, borderRadius: 3, p: 1 }
        }}
      >
        <Typography variant="overline" sx={{ px: 2, fontWeight: 700, color: 'text.secondary' }}>
          Select Palette
        </Typography>
        {(Object.keys(palettes) as PaletteVariant[]).map((v) => (
          <MenuItem 
            key={v} 
            onClick={() => { setPalette(v); handleMenuClose(); }}
            sx={{ borderRadius: 2, gap: 2 }}
          >
            <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: palettes[v].primary }} />
            <Typography variant="body2" sx={{ flexGrow: 1, textTransform: 'capitalize' }}>
              {v}
            </Typography>
            {palette === v && <Check sx={{ fontSize: 16, color: 'primary.main' }} />}
          </MenuItem>
        ))}
      </Menu>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => { navigate('/profile'); handleMenuClose(); }}>
          <AccountCircle sx={{ mr: 1, fontSize: 20 }} /> {t('profile')}
        </MenuItem>
        <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
          <ExitToApp sx={{ mr: 1, fontSize: 20 }} /> {t('logout')}
        </MenuItem>
      </Menu>

      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          pt: !isAuthPage ? { xs: 10, sm: 12 } : 0,
          pb: isMobile && !isAuthPage ? 10 : 4,
          minHeight: '100vh',
          background: theme.palette.background.default
        }}
      >
        <Container maxWidth="lg">
          {children}
        </Container>
      </Box>

      {/* Sticky Bottom Navigation for Mobile */}
      {isMobile && !isAuthPage && (
        <Paper 
          sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1200 }} 
          elevation={10}
        >
          <BottomNavigation
            showLabels
            value={navItems.findIndex(item => location.pathname.startsWith(item.path))}
            onChange={(_, newValue) => {
              navigate(navItems[newValue].path);
            }}
          >
            {navItems.map((item, idx) => (
              <BottomNavigationAction key={idx} label={item.label} icon={item.icon} />
            ))}
          </BottomNavigation>
        </Paper>
      )}
    </Box>
  );
};

export default Layout;
