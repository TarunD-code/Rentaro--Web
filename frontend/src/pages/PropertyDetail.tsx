import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Grid, 
  Paper, 
  Button, 
  alpha, 
  useTheme, 
  Divider,
  Card,
  Avatar,
  IconButton
} from '@mui/material';
import { 
  LocationOn, 
  Verified, 
  Star, 
  Share, 
  FavoriteBorder, 
  EmojiObjects,
  ChevronLeft
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { getPropertyById } from '../api/properties';
import type { PropertyDetail as PropertyType } from '../api/properties';
import { Helmet } from 'react-helmet-async';

// Mock Child Components for first pass
const Gallery: React.FC<{ media: any[] }> = ({ media }) => {
  const theme = useTheme();
  const [active, setActive] = useState(0);
  
  if (!media || media.length === 0) return null;
  
  return (
    <Box sx={{ position: 'relative', borderRadius: 6, overflow: 'hidden', height: { xs: 300, md: 500 } }}>
       <img 
         src={media[active].url} 
         alt="Property" 
         style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
         loading="lazy"
       />
       <Box 
         sx={{ 
           position: 'absolute', 
           bottom: 20, 
           left: 20, 
           display: 'flex', 
           gap: 1.5, 
           p: 1, 
           bgcolor: 'rgba(0,0,0,0.4)', 
           backdropFilter: 'blur(10px)', 
           borderRadius: 4 
         }}
       >
         {media.map((m, i) => (
           <Box 
             key={i} 
             onClick={() => setActive(i)}
             sx={{ 
               width: 60, 
               height: 60, 
               borderRadius: 2, 
               overflow: 'hidden', 
               cursor: 'pointer',
               border: active === i ? `2px solid ${theme.palette.primary.main}` : 'none',
               opacity: active === i ? 1 : 0.6
             }}
           >
             <img src={m.thumbnailUrl || m.url} alt="Thumb" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
           </Box>
         ))}
       </Box>
    </Box>
  );
};

const HostCard: React.FC<{ host: any }> = ({ host }) => {
  const theme = useTheme();
  return (
    <Card 
       elevation={0}
       sx={{ 
         p: 3, 
         borderRadius: 6, 
         border: `1px solid ${theme.palette.divider}`,
         bgcolor: alpha(theme.palette.background.paper, 0.4),
         backdropFilter: 'blur(10px)'
       }}
    >
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <Avatar sx={{ width: 56, height: 56, bgcolor: theme.palette.primary.main }}>{host.name[0]}</Avatar>
        <Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Typography variant="h6" fontWeight={700}>{host.name}</Typography>
            {host.verified && <Verified sx={{ color: 'primary.main', fontSize: 18 }} />}
          </Box>
          <Typography variant="caption" color="text.secondary">Response time: {host.responseTime}</Typography>
        </Box>
      </Box>
      <Button variant="outlined" fullWidth sx={{ borderRadius: 3 }}>View Profile</Button>
    </Card>
  );
};

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const theme = useTheme();
  const navigate = useNavigate();
  const [property, setProperty] = useState<PropertyType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      getPropertyById(id).then(data => {
        setProperty(data);
        setLoading(false);
      });
    }
  }, [id]);

  if (loading || !property) {
    return (
      <Container sx={{ py: 10, textAlign: 'center' }}>
        <Typography>Loading premium details...</Typography>
      </Container>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Helmet>
        <title>{`${property.title} | Rentora`}</title>
        <meta name="description" content={property.description.substring(0, 160)} />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Accommodation",
            "name": property.title,
            "description": property.description,
            "address": {
              "@type": "PostalAddress",
              "addressLocality": property.address.city,
              "addressRegion": property.address.state
            },
            "offers": {
              "@type": "Offer",
              "price": property.price,
              "priceCurrency": property.currency
            }
          })}
        </script>
      </Helmet>
      
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
           <IconButton onClick={() => navigate(-1)} sx={{ bgcolor: alpha(theme.palette.text.primary, 0.05) }}>
              <ChevronLeft />
           </IconButton>
           <Box display="flex" gap={2}>
              <IconButton sx={{ border: `1px solid ${theme.palette.divider}` }}><Share /></IconButton>
              <IconButton sx={{ border: `1px solid ${theme.palette.divider}` }}><FavoriteBorder /></IconButton>
           </Box>
        </Box>

        <Grid container spacing={5}>
          {/* Main Info */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Gallery media={property.media} />
            
            <Box mt={5} mb={3}>
              <Typography variant="h3" fontWeight={800} gutterBottom>{property.title}</Typography>
              <Box display="flex" alignItems="center" gap={1} color="text.secondary">
                <LocationOn fontSize="small" />
                <Typography variant="body1">{property.address.city}, {property.address.state}</Typography>
              </Box>
            </Box>

            <Divider sx={{ my: 4 }} />

            <Box mb={5}>
              <Typography variant="h5" fontWeight={700} gutterBottom>Description</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                {property.description}
              </Typography>
            </Box>

            <Box mb={5}>
              <Typography variant="h5" fontWeight={700} gutterBottom>Amenities</Typography>
              <Grid container spacing={2}>
                {property.amenities.map((a, i) => (
                  <Grid key={i} size={{ xs: 6, sm: 4 }}>
                    <Box display="flex" alignItems="center" gap={1.5} p={2} border={`1px solid ${theme.palette.divider}`} borderRadius={3}>
                       <EmojiObjects sx={{ color: 'primary.main', fontSize: 20 }} />
                       <Typography variant="body2">{a}</Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Grid>

          {/* Sidebar */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ position: 'sticky', top: 100 }}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 4, 
                  borderRadius: 6, 
                  border: `1px solid ${theme.palette.divider}`,
                  bgcolor: alpha(theme.palette.background.paper, 0.4),
                  backdropFilter: 'blur(20px)',
                  mb: 4
                }}
              >
                <Typography variant="h4" fontWeight={800} color="primary.main" gutterBottom>
                  ₹ {property.price.toLocaleString('en-IN')} <Typography component="span" variant="body1" color="text.secondary">/mo</Typography>
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1} mb={4}>
                   <Star sx={{ color: '#FFB800' }} />
                   <Typography variant="subtitle1" fontWeight={700}>4.8</Typography>
                   <Typography variant="caption" color="text.secondary">(124 reviews)</Typography>
                </Box>

                <Button variant="contained" fullWidth size="large" sx={{ height: 60, borderRadius: 3, mb: 2 }}>
                  Contact Host
                </Button>
                <Button variant="outlined" fullWidth size="large" sx={{ height: 60, borderRadius: 3 }}>
                  Schedule a Visit
                </Button>
                
                <Typography variant="caption" display="block" textAlign="center" mt={2} color="text.secondary">
                   No booking fees for first-time tenants.
                </Typography>
              </Paper>

              <HostCard host={property.host} />
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}
