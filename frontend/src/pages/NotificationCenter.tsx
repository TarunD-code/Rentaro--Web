import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  List, 
  ListItem, 
  ListItemAvatar, 
  ListItemText, 
  Avatar, 
  IconButton, 
  Chip, 
  Divider,
  Tab,
  Tabs,
  Button,
  alpha,
  useTheme
} from '@mui/material';
import { 
  Notifications, 
  FiberManualRecord, 
  Delete, 
  Settings,
  Payments,
  Chat,
  VerifiedUser,
  Info
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface Notification {
  id: number;
  type: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

const NotificationCenter: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/notification/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setNotifications(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch notifications", err);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${import.meta.env.VITE_API_URL}/notification/${id}/read`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'rent.due': return <Payments color="error" />;
      case 'message.received': return <Chat color="primary" />;
      case 'user.signup': return <VerifiedUser color="success" />;
      default: return <Info color="info" />;
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (tabValue === 0) return true;
    if (tabValue === 1) return !n.is_read;
    return n.is_read;
  });

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" fontWeight={800} gutterBottom>
            Notification Center
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your alerts and staying updated on your properties.
          </Typography>
        </Box>
        <Button 
          variant="outlined" 
          startIcon={<Settings />} 
          onClick={() => navigate('/notifications/preferences')}
          sx={{ borderRadius: 3 }}
        >
          Preferences
        </Button>
      </Box>

      <Paper 
        elevation={0} 
        sx={{ 
          borderRadius: 4, 
          overflow: 'hidden',
          border: `1px solid ${theme.palette.divider}`,
          bgcolor: alpha(theme.palette.background.paper, 0.6),
          backdropFilter: 'blur(20px)'
        }}
      >
        <Tabs 
          value={tabValue} 
          onChange={(_, v) => setTabValue(v)}
          sx={{ px: 2, pt: 1, borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All" />
          <Tab label="Unread" />
          <Tab label="Archived" />
        </Tabs>

        <List sx={{ p: 0 }}>
          {filteredNotifications.length === 0 ? (
            <Box py={10} textAlign="center">
              <Notifications sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
              <Typography color="text.secondary">No notifications found.</Typography>
            </Box>
          ) : (
            filteredNotifications.map((n, idx) => (
              <React.Fragment key={n.id}>
                <ListItem 
                  alignItems="flex-start"
                  sx={{ 
                    py: 2.5,
                    px: 3,
                    bgcolor: n.is_read ? 'transparent' : alpha(theme.palette.primary.main, 0.03),
                    transition: 'all 0.2s ease',
                    '&:hover': { bgcolor: alpha(theme.palette.action.hover, 0.1) }
                  }}
                  secondaryAction={
                    !n.is_read && (
                      <IconButton edge="end" onClick={() => handleMarkRead(n.id)}>
                        <FiberManualRecord sx={{ color: 'primary.main', fontSize: 14 }} />
                      </IconButton>
                    )
                  }
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), width: 48, height: 48 }}>
                      {getIcon(n.type)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1" fontWeight={n.is_read ? 600 : 800}>
                          {n.content}
                        </Typography>
                        {!n.is_read && <Chip label="New" size="small" color="primary" sx={{ height: 18, fontSize: '0.6rem' }} />}
                      </Box>
                    }
                    secondary={
                      <Box mt={0.5}>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(n.created_at).toLocaleString()}
                        </Typography>
                        <Box mt={1}>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              color: 'primary.main', 
                              cursor: 'pointer',
                              fontWeight: 600,
                              '&:hover': { textDecoration: 'underline' }
                            }}
                          >
                            View Details
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
                {idx < filteredNotifications.length - 1 && <Divider />}
              </React.Fragment>
            ))
          )}
        </List>
      </Paper>
    </Container>
  );
};

export default NotificationCenter;
