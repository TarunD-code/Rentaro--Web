import React from 'react';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Divider, 
  IconButton, 
  Box, 
  Typography, 
  alpha, 
  useTheme,
  ListItemButton,
  Chip
} from '@mui/material';
import { 
  Close, 
  AccountCircle, 
  Dashboard, 
  Search, 
  AddCircle, 
  Assignment, 
  Notifications, 
  Settings, 
  VerifiedUser, 
  ExitToApp,
  Chat,
  AutoAwesome
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

interface AppMenuProps {
  open: boolean;
  onClose: () => void;
}

const AppMenu: React.FC<AppMenuProps> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const role = localStorage.getItem('role') || 'tenant';

  const menuItems = [
    { label: 'Dashboard', icon: <Dashboard />, path: role === 'owner' ? '/owner/dashboard' : '/dashboard', roles: ['tenant', 'owner', 'admin'] },
    { label: 'Browse Listings', icon: <Search />, path: '/listings', roles: ['tenant', 'owner', 'admin'] },
    { label: 'Add Property', icon: <AddCircle />, path: '/create', roles: ['owner', 'admin'] },
    { divider: true },
    { label: 'Edit Profile', icon: <AccountCircle />, path: '/profile', roles: ['tenant', 'owner', 'admin'] },
    { label: 'KYC Verification', icon: <VerifiedUser />, path: '/profile', roles: ['tenant', 'owner', 'admin'] }, // KYC is currently in Profile
    { label: 'Digital Agreements', icon: <Assignment />, path: '/onboarding/agreements', roles: ['tenant', 'owner', 'admin'] },
    { label: 'Messages', icon: <Chat />, path: '/chat', roles: ['tenant', 'owner', 'admin'] },
    { label: 'Premium Benefits', icon: <AutoAwesome />, path: '/tenant/subscription', roles: ['tenant'] },
    { divider: true },
    { label: 'Notifications', icon: <Notifications />, path: '/dashboard', roles: ['tenant', 'owner', 'admin'] },
    { label: 'Settings', icon: <Settings />, path: '/profile', roles: ['tenant', 'owner', 'admin'] },
  ];

  const handleNavigate = (path: string) => {
    navigate(path);
    onClose();
  };

  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    navigate('/login');
    onClose();
  };

  return (
    <Drawer 
      anchor="left" 
      open={open} 
      onClose={onClose}
      PaperProps={{
        sx: { 
          width: 280, 
          bgcolor: 'background.paper',
          borderRight: `1px solid ${theme.palette.divider}`
        }
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" fontWeight={800} color="primary">Rentora</Typography>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </Box>

      <Box sx={{ px: 2, pb: 2 }}>
        <Chip 
          label={role.toUpperCase()} 
          size="small" 
          color="primary" 
          variant="outlined" 
          sx={{ fontWeight: 700, fontSize: 10 }} 
        />
      </Box>

      <Divider />

      <List sx={{ flexGrow: 1, pt: 1 }}>
        {menuItems.map((item, index) => {
          if (item.divider) return <Divider key={index} sx={{ my: 1 }} />;
          if (item.roles && !item.roles.includes(role)) return null;

          const isActive = location.pathname === item.path;

          return (
            <ListItem key={index} disablePadding>
              <ListItemButton 
                onClick={() => handleNavigate(item.path!)}
                selected={isActive}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  mb: 0.5,
                  '&.Mui-selected': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    color: 'primary.main',
                    '& .MuiListItemIcon-root': { color: 'primary.main' }
                  }
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                <ListItemText 
                  primary={item.label} 
                  primaryTypographyProps={{ fontWeight: isActive ? 700 : 500, variant: 'body2' }} 
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider />

      <List>
        <ListItem disablePadding>
          <ListItemButton 
            onClick={handleLogout} 
            sx={{ 
              mx: 1, 
              borderRadius: 2, 
              color: 'error.main',
              '&:hover': { bgcolor: alpha(theme.palette.error.main, 0.05) } 
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: 'error.main' }}><ExitToApp /></ListItemIcon>
            <ListItemText primary="Logout" primaryTypographyProps={{ fontWeight: 700, variant: 'body2' }} />
          </ListItemButton>
        </ListItem>
      </List>
      
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.disabled">Rentora v1.0.0-Sprint21</Typography>
      </Box>
    </Drawer>
  );
};

export default AppMenu;
