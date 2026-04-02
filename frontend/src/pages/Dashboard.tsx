import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  Avatar, 
  useTheme, 
  alpha,
  IconButton,
  Paper
} from '@mui/material';
import { 
  AddCircle, 
  Search, 
  Notifications, 
  TrendingUp, 
  House, 
  People, 
  ReceiptLong, 
  CheckCircle,
  WarningAmber
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        let data;
        try {
          data = await response.json();
        } catch (e) {
          throw new Error('Invalid dashboard response');
        }

        if (!response.ok) {
          const detail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
          throw new Error(detail || 'Failed to load profile');
        }
        setProfile(data);
      } catch (err: any) {
        console.error('Dashboard Fetch Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [navigate]);

  const stats = [
    { label: 'Active Listings', value: '12', icon: <House color="primary" />, color: theme.palette.primary.main },
    { label: 'Total Views', value: '1.2k', icon: <TrendingUp color="secondary" />, color: theme.palette.secondary.main },
    { label: 'Applications', value: '48', icon: <People color="success" />, color: theme.palette.success.main },
    { label: 'Pending Rent', value: '₹45k', icon: <ReceiptLong color="error" />, color: theme.palette.error.main },
  ];

  if (loading) return null;

  return (
    <Box sx={{ py: 2 }}>
      {/* Header Section */}
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 5 
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            {profile?.role === 'owner' ? 'Owner Dashboard' : 'Tenant Dashboard'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Welcome back, {profile?.full_name || 'User'}! Here's what's happening today.
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
           <IconButton sx={{ border: `1px solid ${theme.palette.divider}` }}>
             <Notifications fontSize="small" />
           </IconButton>
           <Avatar sx={{ bgcolor: theme.palette.primary.main, width: 40, height: 40 }}>
             {profile?.full_name?.[0] || 'U'}
           </Avatar>
        </Box>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} mb={5}>
        {stats.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Paper 
                sx={{ 
                  p: 3, 
                  borderRadius: 4, 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 2,
                  border: `1px solid ${alpha(stat.color, 0.1)}`,
                  background: `linear-gradient(135deg, ${alpha(stat.color, 0.05)} 0%, transparent 100%)`
                }}
              >
                <Box 
                  sx={{ 
                    bgcolor: alpha(stat.color, 0.1), 
                    p: 1.5, 
                    borderRadius: 3,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {stat.icon}
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>{stat.value}</Typography>
                  <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
                </Box>
              </Paper>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Main Content Area */}
      <Grid container spacing={4}>
        {/* Left Column - Actions & Status */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Quick Actions</Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Card 
                onClick={() => navigate('/create')}
                sx={{ 
                  cursor: 'pointer',
                  height: '100%',
                  '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) }
                }}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', mb: 2, mx: 'auto' }}>
                    <AddCircle />
                  </Avatar>
                  <Typography variant="h6" fontWeight={700}>Post a New Property</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Reach millions of potential tenants in seconds.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Card 
                onClick={() => navigate('/listings')}
                sx={{ 
                  cursor: 'pointer',
                  height: '100%',
                  '&:hover': { bgcolor: alpha(theme.palette.secondary.main, 0.02) }
                }}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main', mb: 2, mx: 'auto' }}>
                    <Search />
                  </Avatar>
                  <Typography variant="h6" fontWeight={700}>Manage Your Listings</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    View performance and manage inquiries.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Right Column - KYC & Sidebar Info */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Verification Status</Typography>
          <Paper 
            sx={{ 
              p: 3, 
              borderRadius: 4, 
              bgcolor: profile?.kyc_status === 'verified' ? alpha(theme.palette.success.main, 0.05) : alpha(theme.palette.warning.main, 0.05),
              border: `1px solid ${profile?.kyc_status === 'verified' ? alpha(theme.palette.success.main, 0.2) : alpha(theme.palette.warning.main, 0.2)}`
            }}
          >
            <Box display="flex" alignItems="center" gap={1.5} mb={2}>
              {profile?.kyc_status === 'verified' ? (
                <CheckCircle sx={{ color: theme.palette.success.main }} />
              ) : (
                <WarningAmber sx={{ color: theme.palette.warning.main }} />
              )}
              <Typography variant="subtitle1" fontWeight={700}>
                KYC Status: {profile?.kyc_status?.toUpperCase() || 'NOT STARTED'}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {profile?.kyc_status === 'verified' 
                ? 'Your account is fully verified. You can now post and manage unlimited properties.'
                : 'Complete your KYC verification to list properties and interact with verified tenants.'}
            </Typography>
            {profile?.kyc_status !== 'verified' && (
              <Button 
                variant="contained" 
                color="secondary" 
                fullWidth 
                onClick={() => navigate('/profile')}
              >
                Verify Now
              </Button>
            )}
          </Paper>

          {/* Recent Activity Mini-Feed */}
          <Box sx={{ mt: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight={700}>Recent Activity</Typography>
              <Button size="small" variant="text">See All</Button>
            </Box>
            <Box display="flex" flexDirection="column" gap={2}>
              {[1, 2, 3].map((_, i) => (
                <Box key={i} display="flex" gap={2} alignItems="flex-start">
                  <Avatar sx={{ width: 32, height: 32, fontSize: 14 }}>A</Avatar>
                  <Box flex={1}>
                    <Typography variant="body2" fontWeight={600}>New inquiry for "Sunset Villa"</Typography>
                    <Typography variant="caption" color="text.secondary">2 hours ago</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
