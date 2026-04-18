import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  useTheme, 
  alpha,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  CircularProgress,
  Stack
} from '@mui/material';
import { 
  CheckCircle, 
  WorkspacePremium, 
  SupportAgent, 
  LocationOn,
  VerifiedUser,
  NavigateNext
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const SubscriptionLanding: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [subscription, setSubscription] = useState<any>(null);
    const [purchasing, setPurchasing] = useState(false);

    const fetchSubscription = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/subscriptions/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (response.ok) setSubscription(data);
        } catch (err) {
            console.error("Failed to fetch subscription status", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSubscription();
    }, []);

    const handleSubscribe = async (plan: string) => {
        setPurchasing(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/subscriptions/checkout`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ plan_key: plan })
            });

            if (response.ok) {
                const sub = await response.json();
                alert(`Subscription Activated: ${sub.provider_subscription_id}. In production, this would open Razorpay.`);
                window.location.reload();
            }
        } catch (err) {
            alert("Subscription failed");
        } finally {
            setPurchasing(false);
        }
    };

    if (loading) return <Box display="flex" justifyContent="center" py={10}><CircularProgress /></Box>;

    return (
        <Box sx={{ py: 8, px: { xs: 2, md: 8 }, maxWidth: 1400, mx: 'auto' }}>
            <Box textAlign="center" mb={10}>
                <Typography variant="overline" color="primary" fontWeight={800} sx={{ letterSpacing: 2 }}>
                    Premium Tenant Experience
                </Typography>
                <Typography variant="h2" fontWeight={900} mt={1} gutterBottom>
                    Rentora VIP
                </Typography>
                <Typography variant="h6" color="text.secondary" maxWidth={800} mx="auto">
                    Unlock exclusive properties, concierge assistance, and priority support to make your move effortless.
                </Typography>
            </Box>

            <Grid container spacing={4} justifyContent="center" mb={10}>
                {/* Standard Plan */}
                <Grid item xs={12} md={5}>
                    <Card variant="outlined" sx={{ height: '100%', borderRadius: 6, p: 2 }}>
                        <CardContent>
                            <Typography variant="h5" fontWeight={800}>Standard</Typography>
                            <Box display="flex" alignItems="baseline" my={3}>
                                <Typography variant="h3" fontWeight={900}>₹0</Typography>
                                <Typography variant="subtitle1" color="text.secondary">/mo</Typography>
                            </Box>
                            <List sx={{ mb: 4 }}>
                                {[
                                    'Standard search results',
                                    'Basic property visits',
                                    'Shared support tickets',
                                    'Standard move-in assistance'
                                ].map((item, i) => (
                                    <ListItem key={i} disableGutters>
                                        <ListItemIcon sx={{ minWidth: 36 }}><CheckCircle color="disabled" fontSize="small" /></ListItemIcon>
                                        <ListItemText primary={item} />
                                    </ListItem>
                                ))}
                            </List>
                            <Button fullWidth variant="outlined" size="large" sx={{ borderRadius: 3 }} disabled>
                                Current Plan
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Premium Plan */}
                <Grid item xs={12} md={5}>
                    <Card sx={{ 
                        height: '100%', 
                        borderRadius: 6, 
                        p: 2,
                        position: 'relative',
                        border: `2px solid ${theme.palette.primary.main}`,
                        boxShadow: `0 20px 40px ${alpha(theme.palette.primary.main, 0.15)}`
                    }}>
                        <Box sx={{ 
                            position: 'absolute', top: 16, right: 16, 
                            bgcolor: 'primary.main', color: 'white', 
                            px: 1.5, py: 0.5, borderRadius: 2, fontSize: 12, fontWeight: 800 
                        }}>
                            POPULAR
                        </Box>
                        <CardContent>
                            <Typography variant="h5" fontWeight={800} color="primary">VIP Premium</Typography>
                            <Box display="flex" alignItems="baseline" my={3}>
                                <Typography variant="h3" fontWeight={900}>₹999</Typography>
                                <Typography variant="subtitle1" color="text.secondary">/mo</Typography>
                            </Box>
                            <List sx={{ mb: 4 }}>
                                {[
                                    'Verified-only property filters',
                                    'Priority Support (4h SLA)',
                                    'Personal Concierge Assistance',
                                    'Early access to new listings',
                                    'Digital agreement waivers'
                                ].map((item, i) => (
                                    <ListItem key={i} disableGutters>
                                        <ListItemIcon sx={{ minWidth: 36 }}><CheckCircle color="primary" fontSize="small" /></ListItemIcon>
                                        <ListItemText primary={item} sx={{ fontWeight: 600 }} />
                                    </ListItem>
                                ))}
                            </List>
                            <Button 
                                fullWidth 
                                variant="contained" 
                                size="large" 
                                sx={{ borderRadius: 3, fontWeight: 800 }}
                                onClick={() => handleSubscribe('premium')}
                                disabled={subscription?.status === 'active' || purchasing}
                            >
                                {subscription?.status === 'active' ? 'Active Subscription' : 'Upgrade to VIP'}
                                {purchasing && <CircularProgress size={20} sx={{ ml: 1, color: 'white' }} />}
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Premium Features Breakdown */}
            <Typography variant="h4" fontWeight={900} textAlign="center" mb={6}>Benefits of Premium</Typography>
            <Grid container spacing={4}>
                <Grid item xs={12} md={4}>
                    <Stack spacing={2} alignItems="center" textAlign="center">
                        <Box sx={{ p: 2, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 4 }}>
                            <SupportAgent color="info" fontSize="large" />
                        </Box>
                        <Typography variant="h6" fontWeight={800}>Priority Support</Typography>
                        <Typography color="text.secondary">Jump the queue with dedicated support agents available 24/7 for VIP tenants.</Typography>
                    </Stack>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Stack spacing={2} alignItems="center" textAlign="center">
                        <Box sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.1), borderRadius: 4 }}>
                            <VerifiedUser color="success" fontSize="large" />
                        </Box>
                        <Typography variant="h6" fontWeight={800}>Verified Listings</Typography>
                        <Typography color="text.secondary">Access properties that have been physically inspected and owner-verified by Rentora.</Typography>
                    </Stack>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Stack spacing={2} alignItems="center" textAlign="center">
                        <Box sx={{ p: 2, bgcolor: alpha(theme.palette.warning.main, 0.1), borderRadius: 4 }}>
                            <NavigateNext color="warning" fontSize="large" />
                        </Box>
                        <Typography variant="h6" fontWeight={800}>Concierge Desk</Typography>
                        <Typography color="text.secondary">Let us handle the coordination. We shortlist, book visits, and negotiate on your behalf.</Typography>
                    </Stack>
                </Grid>
            </Grid>
        </Box>
    );
};

export default SubscriptionLanding;
