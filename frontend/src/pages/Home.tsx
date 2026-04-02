import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Grid, 
  Card, 
  CardContent, 
  useTheme, 
  alpha,
  Button
} from '@mui/material';
import { 
  VerifiedUser, 
  Speed, 
  HighQuality, 
  ArrowForward 
} from '@mui/icons-material';
import { fetchFeatured } from '../api/properties';
import FeaturedCarousel from '../components/FeaturedCarousel';
import HeroSearch from '../components/HeroSearch';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet-async';

const Home: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [featured, setFeatured] = useState<any[]>([]);

  useEffect(() => {
    let mounted = true;
    fetchFeatured(6).then(data => { 
      if (mounted) {
        setFeatured(data);
      }
    });
    
    // Analytics: Page View
    console.log('[Analytics] Page View: Home');
    
    return () => { mounted = false; };
  }, []);

  const valueProps = [
    { title: 'Verified Hosts', desc: 'Secure and trusted rental process with 100% verified owners.', icon: <VerifiedUser color="primary" fontSize="large" /> },
    { title: 'Fast Approval', desc: 'Get your rental application approved in under 24 hours.', icon: <Speed color="secondary" fontSize="large" /> },
    { title: 'Premium Units', desc: 'Curated selection of high-end homes and apartments.', icon: <HighQuality color="success" fontSize="large" /> },
  ];

  return (
    <Box sx={{ overflow: 'hidden' }}>
      <Helmet>
        <title>Rentora | Premium Property Rentals</title>
        <meta name="description" content="Find verified luxury apartments and homes across India's top cities. Rentora simplifies your digital rental journey." />
      </Helmet>
      {/* Structured Data JSON-LD */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "WebSite",
          "name": "Rentora",
          "url": window.location.origin,
          "potentialAction": {
            "@type": "SearchAction",
            "target": `${window.location.origin}/listings?q={search_term_string}`,
            "query-input": "required name=search_term_string"
          }
        })}
      </script>

      {/* Hero Section */}
      <Box 
        sx={{ 
          pt: { xs: 10, md: 15 }, 
          pb: { xs: 8, md: 12 }, 
          textAlign: 'center',
          background: `radial-gradient(circle at top right, ${alpha(theme.palette.primary.main, 0.1)} 0%, transparent 40%)`,
          position: 'relative'
        }}
      >
        <Container maxWidth="lg">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Typography 
              variant="h1" 
              sx={{ 
                fontSize: { xs: '2.5rem', md: '4rem' }, 
                fontWeight: 800, 
                mb: 2,
                background: `linear-gradient(135deg, ${theme.palette.text.primary} 0%, ${alpha(theme.palette.text.primary, 0.6)} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Premium Living, <br />Simplified for Everyone.
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'text.secondary', 
                mb: 6, 
                maxWidth: 600, 
                mx: 'auto',
                fontWeight: 500,
                lineHeight: 1.6
              }}
            >
              Rentora connects you with verified premium properties across Indias major hubs. Experience a seamless and secure digital rental journey.
            </Typography>
            
            <Box display="flex" justifyContent="center">
               <HeroSearch />
            </Box>

            <Box mt={4} display="flex" justifyContent="center" gap={3} flexWrap="wrap">
               <Button 
                 variant="text" 
                 endIcon={<ArrowForward />} 
                 sx={{ fontWeight: 600, color: 'primary.main' }}
                 onClick={() => {
                   console.log('[Analytics] Event: CTA_Explore_All');
                   window.location.href = '/listings';
                 }}
               >
                 Explore All Listings
               </Button>
            </Box>
          </motion.div>
        </Container>
      </Box>

      {/* Value Props Section */}
      <Container sx={{ mb: 12 }}>
        <Grid container spacing={4}>
          {valueProps.map((prop, i) => (
            <Grid key={i} size={{ xs: 12, md: 4 }}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
              >
                <Card 
                  sx={{ 
                    height: '100%', 
                    p: 2, 
                    borderRadius: 6, 
                    border: `1px solid ${theme.palette.divider}`,
                    bgcolor: alpha(theme.palette.background.paper, 0.4),
                    backdropFilter: 'blur(10px)',
                    transition: 'transform 0.3s ease',
                    '&:hover': { transform: 'scale(1.02)' }
                  }}
                >
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Box sx={{ mb: 3, p: 2, bgcolor: alpha(theme.palette.background.default, 0.8), borderRadius: '50%', display: 'inline-block' }}>
                      {prop.icon}
                    </Box>
                    <Typography variant="h6" fontWeight={700} gutterBottom>{prop.title}</Typography>
                    <Typography variant="body2" color="text.secondary">{prop.desc}</Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Featured Section */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), py: 10 }}>
        <Container>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Box>
              <Typography variant="h4" fontWeight={800}>{t('browse_listings')}</Typography>
              <Typography variant="body2" color="text.secondary">Hand-picked premium listings for you.</Typography>
            </Box>
            <Button variant="outlined" sx={{ borderRadius: 4 }}>View All</Button>
          </Box>
          
          <FeaturedCarousel items={featured} />
        </Container>
      </Box>

      {/* SEO Footer text for crawlers */}
      <Box sx={{ py: 6, opacity: 0.6, borderTop: `1px solid ${theme.palette.divider}`, textAlign: 'center' }}>
        <Container>
          <Typography variant="caption">
            Rentora is the leading marketplace for luxury apartments in Mumbai, Delhi, Bengaluru, and beyond. Find your next dream home with our verified property listings.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Home;
