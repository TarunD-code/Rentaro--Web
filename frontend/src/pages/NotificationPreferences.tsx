import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  Switch, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon,
  Divider,
  Button,
  useTheme,
  alpha,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  PushNotifications, 
  Email, 
  Sms, 
  ArrowBack, 
  Save 
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const NotificationPreferences: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [prefs, setPrefs] = useState({
    push_enabled: true,
    email_enabled: true,
    sms_enabled: false
  });

  const fetchPrefs = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/notification/preferences`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setPrefs(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrefs();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/notification/preferences`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(prefs)
      });
      if (res.ok) {
        setSuccess(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Button 
        startIcon={<ArrowBack />} 
        onClick={() => navigate('/notifications')}
        sx={{ mb: 3 }}
      >
        Back to Notifications
      </Button>

      <Box mb={4}>
        <Typography variant="h4" fontWeight={800} gutterBottom>
          Communication Preferences
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Choose how you want Rentora to contact you.
        </Typography>
      </Box>

      {success && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: 3 }}>
          Preferences updated successfully!
        </Alert>
      )}

      <Paper 
        elevation={0} 
        sx={{ 
          borderRadius: 4, 
          overflow: 'hidden',
          border: `1px solid ${theme.palette.divider}`,
          bgcolor: alpha(theme.palette.background.paper, 0.4),
          backdropFilter: 'blur(10px)'
        }}
      >
        <List sx={{ p: 0 }}>
          <ListItem sx={{ py: 3, px: 3 }}>
            <ListItemIcon>
              <PushNotifications color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Push Notifications" 
              secondary="Receive real-time alerts on your browser and mobile device." 
            />
            <Switch 
              checked={prefs.push_enabled}
              onChange={(e) => setPrefs({...prefs, push_enabled: e.target.checked})}
            />
          </ListItem>
          <Divider />
          
          <ListItem sx={{ py: 3, px: 3 }}>
            <ListItemIcon>
              <Email color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Email Updates" 
              secondary="Get detailed reports, agreements, and payment receipts via email." 
            />
            <Switch 
              checked={prefs.email_enabled}
              onChange={(e) => setPrefs({...prefs, email_enabled: e.target.checked})}
            />
          </ListItem>
          <Divider />

          <ListItem sx={{ py: 3, px: 3 }}>
            <ListItemIcon>
              <Sms color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="SMS Alerts" 
              secondary="Receive urgent reminders and OTPs directly on your phone." 
            />
            <Switch 
              checked={prefs.sms_enabled}
              onChange={(e) => setPrefs({...prefs, sms_enabled: e.target.checked})}
            />
          </ListItem>
        </List>

        <Box sx={{ p: 3, bgcolor: alpha(theme.palette.background.paper, 0.2), display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="contained" 
            startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <Save />}
            onClick={handleSave}
            disabled={saving}
            sx={{ borderRadius: 3, px: 4 }}
          >
            Save Changes
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default NotificationPreferences;
