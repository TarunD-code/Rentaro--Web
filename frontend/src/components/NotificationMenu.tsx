import React, { useState, useEffect } from 'react';
import { 
  Badge, 
  IconButton, 
  Menu, 
  MenuItem, 
  Typography, 
  Box, 
  Divider,
  Avatar,
  alpha,
  useTheme
} from '@mui/material';
import { Notifications, Circle, CheckCircle } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface RentoraNotification {
  id: number;
  type: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

const NotificationMenu: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<RentoraNotification[]>([]);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await fetch(`${import.meta.env.VITE_API_URL}/profile/notifications`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const markAsRead = async (id: number) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${import.meta.env.VITE_API_URL}/profile/notifications/${id}/read`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <>
      <IconButton color="inherit" onClick={handleOpen}>
        <Badge badgeContent={unreadCount} color="error">
          <Notifications />
        </Badge>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          elevation: 4,
          sx: { 
            width: 320, 
            maxHeight: 400,
            mt: 1.5,
            borderRadius: 3,
            overflow: 'hidden'
          }
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle1" fontWeight={700}>Notifications</Typography>
          {unreadCount > 0 && (
            <Typography variant="caption" color="primary.main" sx={{ cursor: 'pointer' }}>
              Mark all as read
            </Typography>
          )}
        </Box>
        <Divider />
        
        <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
          {notifications.length === 0 ? (
            <Box p={3} textAlign="center">
              <Typography variant="body2" color="text.secondary">No new notifications</Typography>
            </Box>
          ) : (
            notifications.map((notif) => (
              <MenuItem 
                key={notif.id} 
                onClick={() => {
                  if (!notif.is_read) markAsRead(notif.id);
                  if (notif.type === 'message') navigate('/dashboard'); // routing logic based on type
                }}
                sx={{ 
                  py: 1.5, 
                  px: 2,
                  bgcolor: notif.is_read ? 'transparent' : alpha(theme.palette.primary.main, 0.05),
                  borderBottom: `1px solid ${theme.palette.divider}`
                }}
              >
                <Box display="flex" gap={2} width="100%" alignItems="center">
                  <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                    <Notifications fontSize="small" />
                  </Avatar>
                  <Box flex={1}>
                    <Typography variant="body2" fontWeight={notif.is_read ? 400 : 600} sx={{ whiteSpace: 'normal', lineHeight: 1.3 }}>
                      {notif.content}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" mt={0.5} display="block">
                      {new Date(notif.created_at).toLocaleDateString()} at {new Date(notif.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </Typography>
                  </Box>
                  {!notif.is_read && <Circle sx={{ color: 'primary.main', fontSize: 10 }} />}
                </Box>
              </MenuItem>
            ))
          )}
        </Box>
      </Menu>
    </>
  );
};

export default NotificationMenu;
