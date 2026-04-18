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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress
} from '@mui/material';
import { 
  Star, 
  CheckCircle, 
  FlashOn, 
  WorkspacePremium,
  AccountBalanceWallet
} from '@mui/icons-material';

const FeaturedListings: React.FC = () => {
    const theme = useTheme();
    const [products, setProducts] = useState<any[]>([]);
    const [properties, setProperties] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedProduct, setSelectedProduct] = useState<any>(null);
    const [openSelectProperty, setOpenSelectProperty] = useState(false);
    const [purchasing, setPurchasing] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            
            const [prodRes, propRes] = await Promise.all([
                fetch(`${import.meta.env.VITE_API_URL}/billing/products`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                }),
                fetch(`${import.meta.env.VITE_API_URL}/property/`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
            ]);

            const prodData = await prodRes.json();
            const propData = await propRes.json();
            
            if (prodRes.ok) setProducts(prodData);
            // Only show properties owned by current user
            if (propRes.ok) setProperties(propData.filter((p: any) => p.owner_id === user.user_identifier));
        } catch (err) {
            console.error("Failed to fetch data", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handlePurchase = async (propertyId: number) => {
        setPurchasing(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/billing/checkout`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: selectedProduct.id,
                    property_id: propertyId
                })
            });
            
            if (response.ok) {
                const purchase = await response.json();
                alert(`Order Created: ${purchase.razorpay_order_id}. In production, this would redirect to Razorpay.`);
                // In sandbox, we "complete" it manually for demo purposes
                alert("Simulating successful payment...");
                window.location.reload();
            }
        } catch (err) {
            alert("Checkout failed");
        } finally {
            setPurchasing(false);
            setOpenSelectProperty(false);
        }
    };

    if (loading) return <Box display="flex" justifyContent="center" height="50vh" alignItems="center"><CircularProgress /></Box>;

    return (
        <Box sx={{ py: 6, maxWidth: 1200, mx: 'auto', px: 2 }}>
            <Box textAlign="center" mb={8}>
                <Typography variant="h3" fontWeight={900} gutterBottom>
                    Reach More Tenants
                </Typography>
                <Typography variant="h6" color="text.secondary">
                    Boost your property's visibility by featuring it at the top of search results.
                </Typography>
            </Box>

            <Grid container spacing={4} justifyContent="center">
                {products.map((product) => (
                    <Grid item xs={12} md={4} key={product.id}>
                        <Card sx={{ 
                            height: '100%', 
                            display: 'flex', 
                            flexDirection: 'column',
                            borderRadius: 6,
                            transition: 'all 0.3s ease',
                            border: product.name === 'Gold' ? `2px solid ${theme.palette.secondary.main}` : `1px solid ${theme.palette.divider}`,
                            '&:hover': { transform: 'translateY(-10px)', boxShadow: theme.shadows[20] }
                        }}>
                            <Box sx={{ p: 4, textAlign: 'center', bgcolor: alpha(theme.palette.primary.main, 0.03) }}>
                                {product.name === 'Bronze' && <FlashOn color="action" sx={{ fontSize: 40 }} />}
                                {product.name === 'Silver' && <Star color="primary" sx={{ fontSize: 40 }} />}
                                {product.name === 'Gold' && <WorkspacePremium color="secondary" sx={{ fontSize: 40 }} />}
                                <Typography variant="h5" fontWeight={800} mt={2}>{product.name}</Typography>
                                <Typography variant="h3" fontWeight={900} color="primary" sx={{ my: 2 }}>
                                    ₹{product.price_inr}
                                </Typography>
                                <Chip label={`${product.duration_days} Days`} size="small" />
                            </Box>
                            <CardContent sx={{ flexGrow: 1, p: 4 }}>
                                <List dense>
                                    <ListItem disableGutters>
                                        <ListItemIcon sx={{ minWidth: 36 }}><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                                        <ListItemText primary="Priority indexing" />
                                    </ListItem>
                                    <ListItem disableGutters>
                                        <ListItemIcon sx={{ minWidth: 36 }}><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                                        <ListItemText primary={`${product.priority === 3 ? 'Ultra High' : 'Standard'} visibility`} />
                                    </ListItem>
                                    <ListItem disableGutters>
                                        <ListItemIcon sx={{ minWidth: 36 }}><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                                        <ListItemText primary="Featured badge on card" />
                                    </ListItem>
                                </List>
                            </CardContent>
                            <Box sx={{ p: 4, pt: 0 }}>
                                <Button 
                                    fullWidth 
                                    variant={product.name === 'Gold' ? "contained" : "outlined"}
                                    color={product.name === 'Gold' ? "secondary" : "primary"}
                                    size="large"
                                    sx={{ borderRadius: 3, fontWeight: 700 }}
                                    onClick={() => {
                                        setSelectedProduct(product);
                                        setOpenSelectProperty(true);
                                    }}
                                >
                                    Choose Plan
                                </Button>
                            </Box>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            <Dialog open={openSelectProperty} onClose={() => setOpenSelectProperty(false)} fullWidth maxWidth="sm">
                <DialogTitle sx={{ fontWeight: 800 }}>Select Property to Feature</DialogTitle>
                <DialogContent sx={{ p: 0 }}>
                    <List sx={{ pt: 0 }}>
                        {properties.map((prop) => (
                            <ListItem 
                                key={prop.id} 
                                button 
                                onClick={() => handlePurchase(prop.id)}
                                disabled={purchasing}
                                sx={{ px: 3, py: 2 }}
                            >
                                <ListItemIcon>
                                    <Home />
                                </ListItemIcon>
                                <ListItemText 
                                    primary={prop.title} 
                                    secondary={prop.address} 
                                />
                                {purchasing ? <CircularProgress size={20} /> : <AccountBalanceWallet />}
                            </ListItem>
                        ))}
                        {properties.length === 0 && (
                            <Box p={4} textAlign="center">
                                <Typography color="text.secondary">No eligible properties found.</Typography>
                            </Box>
                        )}
                    </List>
                </DialogContent>
            </Dialog>
        </Box>
    );
};

export default FeaturedListings;
