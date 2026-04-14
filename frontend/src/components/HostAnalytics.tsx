import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper, alpha, useTheme, Card, CardContent } from '@mui/material';
import { TrendingUp, Visibility, Favorite, MapsUgc } from '@mui/icons-material';

interface AnalyticsData {
  total_views: number;
  total_inquiries: number;
  total_favorites: number;
  average_rating: number;
}

interface HostAnalyticsProps {
  metrics?: any;
}

const HostAnalytics: React.FC<HostAnalyticsProps> = ({ metrics }) => {
  const theme = useTheme();
  const [data, setData] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    if (metrics) {
      setData({
        total_views: metrics.total_views || 0,
        total_inquiries: metrics.total_applications || 0,
        total_favorites: 0,
        average_rating: 0
      });
      return;
    }
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const res = await fetch(`${import.meta.env.VITE_API_URL}/property/analytics/host`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error("Analytics Error", err);
      }
    };
    fetchData();
  }, []);

  if (!data) return <Box p={3}><Typography>Loading analytics...</Typography></Box>;

  const statCards = [
    { label: "Profile Views", value: data.total_views, icon: <Visibility color="primary" />, color: theme.palette.primary.main },
    { label: "Message Inquiries", value: data.total_inquiries, icon: <MapsUgc color="secondary" />, color: theme.palette.secondary.main },
    { label: "Saved Favorites", value: data.total_favorites, icon: <Favorite color="error" />, color: theme.palette.error.main },
    { label: "Average Rating", value: data.average_rating.toFixed(1), icon: <TrendingUp color="success" />, color: theme.palette.success.main },
  ];

  return (
    <Box mt={4} mb={4}>
      <Typography variant="h6" fontWeight={700} mb={3}>Performance Overview</Typography>
      
      <Grid container spacing={3}>
        {statCards.map((stat, i) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
            <Card elevation={0} sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 4 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box sx={{ p: 1, bgcolor: alpha(stat.color, 0.1), borderRadius: 2, display: 'flex' }}>
                    {stat.icon}
                  </Box>
                </Box>
                <Typography variant="h4" fontWeight={800}>{stat.value}</Typography>
                <Typography variant="body2" color="text.secondary">{stat.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Grid container spacing={3} mt={1}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper elevation={0} sx={{ p: 3, border: `1px solid ${theme.palette.divider}`, borderRadius: 4, height: 300, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle1" fontWeight={700} mb={2}>Traffic Mockup (Last 30 Days)</Typography>
            <Box flex={1} display="flex" alignItems="flex-end" gap={1}>
               {/* Pure CSS Bar Chart Mockup */}
               {[30, 50, 45, 80, 60, 90, 100].map((h, i) => (
                 <Box key={i} sx={{ flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                    <Box sx={{ width: '60%', height: `${h}%`, bgcolor: alpha(theme.palette.primary.main, 0.7), borderRadius: '4px 4px 0 0', '&:hover': { bgcolor: theme.palette.primary.main } }} />
                 </Box>
               ))}
            </Box>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper elevation={0} sx={{ p: 3, border: `1px solid ${theme.palette.divider}`, borderRadius: 4, height: 300 }}>
             <Typography variant="subtitle1" fontWeight={700} mb={2}>Conversion Rate</Typography>
             <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="80%">
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                   {/* CSS circular progress mockup */}
                   <svg width="120" height="120" style={{ transform: 'rotate(-90deg)' }}>
                      <circle cx="60" cy="60" r="50" fill="transparent" stroke={alpha(theme.palette.primary.main, 0.1)} strokeWidth="10" />
                      <circle cx="60" cy="60" r="50" fill="transparent" stroke={theme.palette.primary.main} strokeWidth="10" strokeDasharray="314" strokeDashoffset="220" strokeLinecap="round" />
                   </svg>
                   <Box sx={{ top: 0, left: 0, bottom: 0, right: 0, position: 'absolute', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Typography variant="h5" fontWeight={700}>32%</Typography>
                   </Box>
                </Box>
                <Typography variant="caption" color="text.secondary" mt={2}>Inquiry to Conversion</Typography>
             </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HostAnalytics;
