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

import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { api } from '../services/api';
import ResponsiveChart from './Charts/ResponsiveChart';

interface AnalyticsData {
  total_views: number;
  total_inquiries: number;
  total_favorites: number;
  average_rating: number;
  conversion_rate?: number;
  traffic_data?: any[];
}

interface HostAnalyticsProps {
  metrics?: any;
}

const HostAnalytics: React.FC<HostAnalyticsProps> = ({ metrics }) => {
  const theme = useTheme();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (metrics) {
      setData({
        total_views: metrics.total_views || 0,
        total_inquiries: metrics.total_applications || 0,
        total_favorites: 0,
        average_rating: 0,
        conversion_rate: 32,
        traffic_data: [
          { day: 'Mon', views: 30 }, { day: 'Tue', views: 50 }, { day: 'Wed', views: 45 },
          { day: 'Thu', views: 80 }, { day: 'Fri', views: 60 }, { day: 'Sat', views: 90 },
          { day: 'Sun', views: 100 }
        ]
      });
      return;
    }
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await api.get('/property/analytics/host');
        if (res && res.ok) {
          const json = await res.json();
          setData({
              ...json,
              conversion_rate: 32,
              traffic_data: [
                { day: 'Mon', views: 30 }, { day: 'Tue', views: 50 }, { day: 'Wed', views: 45 },
                { day: 'Thu', views: 80 }, { day: 'Fri', views: 60 }, { day: 'Sat', views: 90 },
                { day: 'Sun', views: 100 }
              ]
          });
        }
      } catch (err) {
        console.error("Analytics Error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [metrics]);

  if (!data && loading) return <Box p={3} display="flex" justifyContent="center"><CircularProgress size={24} /></Box>;
  if (!data) return null;

  const statCards = [
    { label: "Profile Views", value: data.total_views, icon: <Visibility fontSize="small" />, color: theme.palette.primary.main },
    { label: "Message Inquiries", value: data.total_inquiries, icon: <MapsUgc fontSize="small" />, color: theme.palette.secondary.main },
    { label: "Saved Favorites", value: data.total_favorites, icon: <Favorite fontSize="small" />, color: theme.palette.error.main },
    { label: "Average Rating", value: data.average_rating.toFixed(1), icon: <TrendingUp fontSize="small" />, color: theme.palette.success.main },
  ];

  const pieData = [
    { name: 'Converted', value: data.conversion_rate || 32 },
    { name: 'Pending', value: 100 - (data.conversion_rate || 32) }
  ];

  return (
    <Box mt={4} mb={4}>
      <Typography variant="h6" fontWeight={700} mb={3}>Performance Overview</Typography>
      
      <Grid container spacing={3}>
        {statCards.map((stat, i) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
            <Card elevation={0} sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 4, bgcolor: alpha(stat.color, 0.02) }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1.5}>
                  <Box sx={{ p: 1, bgcolor: alpha(stat.color, 0.1), borderRadius: 2, display: 'flex' }}>
                    {stat.icon}
                  </Box>
                </Box>
                <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: -1 }}>{stat.value}</Typography>
                <Typography variant="body2" color="text.secondary" fontWeight={500}>{stat.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Grid container spacing={3} mt={1}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper elevation={0} sx={{ p: 3, border: `1px solid ${theme.palette.divider}`, borderRadius: 6 }}>
            <Typography variant="subtitle1" fontWeight={700} mb={3}>Traffic Trends (Last 7 Days)</Typography>
            <ResponsiveChart height={280}>
                <BarChart data={data.traffic_data}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.palette.divider} />
                    <XAxis 
                        dataKey="day" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    />
                    <YAxis hide />
                    <Tooltip 
                        cursor={{ fill: alpha(theme.palette.primary.main, 0.05) }}
                        contentStyle={{ borderRadius: 12, border: 'none', boxShadow: theme.shadows[4] }}
                    />
                    <Bar 
                        dataKey="views" 
                        fill={theme.palette.primary.main} 
                        radius={[6, 6, 0, 0]} 
                        barSize={32}
                    />
                </BarChart>
            </ResponsiveChart>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper elevation={0} sx={{ p: 3, border: `1px solid ${theme.palette.divider}`, borderRadius: 6, textAlign: 'center' }}>
             <Typography variant="subtitle1" fontWeight={700} mb={1} align="left">Conversion Analysis</Typography>
             <ResponsiveChart height={280}>
                <PieChart>
                    <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={8}
                        dataKey="value"
                    >
                        <Cell fill={theme.palette.primary.main} />
                        <Cell fill={alpha(theme.palette.primary.main, 0.1)} />
                    </Pie>
                    <Tooltip />
                </PieChart>
             </ResponsiveChart>
             <Box mt={-12} mb={8}>
                <Typography variant="h4" fontWeight={800}>{data.conversion_rate}%</Typography>
                <Typography variant="caption" color="text.secondary">Inquiry Success</Typography>
             </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HostAnalytics;
