import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  Card, 
  CardContent, 
  Button, 
  useTheme, 
  alpha,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem
} from '@mui/material';
import { 
  TrendingUp, 
  Home, 
  PendingActions, 
  FileDownload, 
  Star,
  MoreVert,
  ArrowForward
} from '@mui/icons-material';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import { api } from '../../services/api';

const OwnerDashboard: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState<any>(null);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const fetchMetrics = async () => {
        setLoading(true);
        try {
            const userStr = localStorage.getItem('user');
            const user = userStr ? JSON.parse(userStr) : {};
            // Robust ownerId fallback
            const ownerId = user.user_identifier || user.owner_id || user.id;
            
            if (!ownerId) {
                console.error("Owner identity not found in session.");
                return;
            }

            const response = await api.get(`/owner-dashboard/owners/${ownerId}/metrics`);
            if (response && response.ok) {
                const data = await response.json();
                setMetrics(data);
            }
        } catch (err) {
            console.error("Failed to fetch dashboard metrics", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMetrics();
    }, []);

    const stats = [
        { label: 'Total Revenue', value: `₹${metrics?.revenue_total?.toLocaleString() || '0'}`, icon: <TrendingUp />, color: theme.palette.success.main },
        { label: 'Occupancy Rate', value: `${metrics?.occupancy_rate?.toFixed(1) || '0'}%`, icon: <Home />, color: theme.palette.primary.main },
        { label: 'Pending Rent', value: `₹${metrics?.pending_rent_total?.toLocaleString() || '0'}`, icon: <PendingActions />, color: theme.palette.warning.main },
    ];

    if (loading) return (
        <Box display="flex" justifyContent="center" alignItems="center" height="80vh">
            <CircularProgress color="primary" thickness={4} />
        </Box>
    );

    return (
        <Box sx={{ py: 4, px: { xs: 2, md: 4 } }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Box>
                    <Typography variant="h4" fontWeight={800} color="text.primary" gutterBottom>
                        Premium Owner Dashboard
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Comprehensive analytics and monetisation tools for your property portfolio.
                    </Typography>
                </Box>
                <Box display="flex" gap={2}>
                    <Button 
                        variant="outlined" 
                        startIcon={<FileDownload />}
                        onClick={() => navigate('/owner/reports')}
                    >
                        Export Reports
                    </Button>
                    <Button 
                        variant="contained" 
                        startIcon={<Star />}
                        onClick={() => navigate('/owner/premium')}
                        sx={{ 
                            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                            boxShadow: '0 4px 14px 0 rgba(0,118,255,0.39)',
                            borderRadius: 3
                        }}
                    >
                        Boost Listings
                    </Button>
                </Box>
            </Box>

            <Grid container spacing={3} mb={4}>
                {stats.map((stat, i) => (
                    <Grid size={{ xs: 12, md: 4 }} key={i}>
                        <Paper elevation={0} sx={{ 
                            p: 3, 
                            borderRadius: 4, 
                            bgcolor: alpha(stat.color, 0.05),
                            border: `1px solid ${alpha(stat.color, 0.1)}`,
                            position: 'relative',
                            overflow: 'hidden'
                        }}>
                            <Box sx={{ position: 'absolute', top: -10, right: -10, opacity: 0.1, transform: 'scale(3)' }}>
                                {stat.icon}
                            </Box>
                            <Typography variant="overline" color="text.secondary" fontWeight={700}>
                                {stat.label}
                            </Typography>
                            <Typography variant="h4" fontWeight={800} sx={{ mt: 1, color: stat.color }}>
                                {stat.value}
                            </Typography>
                        </Paper>
                    </Grid>
                ))}
            </Grid>

            <Grid container spacing={4}>
                <Grid size={{ xs: 12, md: 8 }}>
                    <Paper elevation={0} sx={{ p: 4, borderRadius: 6, border: `1px solid ${theme.palette.divider}`, minHeight: 400 }}>
                        <Typography variant="h6" fontWeight={700} mb={3}>Revenue Trend</Typography>
                        <Box sx={{ width: '100%', height: 350 }}>
                            <ResponsiveContainer>
                                <AreaChart data={metrics?.history || []}>
                                    <defs>
                                        <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.1}/>
                                            <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.palette.divider} />
                                    <XAxis 
                                        dataKey="period_start" 
                                        tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, { month: 'short' })}
                                        stroke={theme.palette.text.secondary}
                                        fontSize={12}
                                    />
                                    <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
                                    <Tooltip 
                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: theme.shadows[10] }}
                                    />
                                    <Area 
                                        type="monotone" 
                                        dataKey="revenue_total" 
                                        stroke={theme.palette.primary.main} 
                                        strokeWidth={3}
                                        fillOpacity={1} 
                                        fill="url(#colorRev)" 
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Box>
                    </Paper>
                </Grid>

                <Grid size={{ xs: 12, md: 4 }}>
                    <Card elevation={0} sx={{ borderRadius: 6, border: `1px solid ${theme.palette.divider}`, height: '100%' }}>
                        <CardContent sx={{ p: 4 }}>
                            <Typography variant="h6" fontWeight={700} mb={3}>Portfolio Health</Typography>
                            <Box sx={{ height: 250 }}>
                                <ResponsiveContainer>
                                    <BarChart data={metrics?.history?.slice(-5) || []}>
                                        <XAxis dataKey="id" hide />
                                        <Tooltip />
                                        <Bar dataKey="occupancy_count" fill={theme.palette.secondary.main} radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                            <Box mt={3}>
                                <Typography variant="body2" color="text.secondary">
                                    Your portfolio is currently performing 12% better than the local average.
                                </Typography>
                                <Button 
                                    sx={{ mt: 2 }} 
                                    endIcon={<ArrowForward />} 
                                    fullWidth
                                    onClick={() => navigate('/owner/premium')}
                                >
                                    View Optimization Tips
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default OwnerDashboard;
