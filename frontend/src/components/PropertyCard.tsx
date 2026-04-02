import React from 'react';
import { 
  Card, 
  CardMedia, 
  CardContent, 
  Typography, 
  Box, 
  Chip, 
  IconButton, 
  alpha,
  useTheme
} from '@mui/material';
import { 
  LocationOn, 
  Favorite, 
  FavoriteBorder, 
  Star, 
  HomeWork
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

interface Property {
  id: string;
  title: string;
  price: string | number;
  address: string;
  amenities: string | string[];
  thumbnail_url?: string;
  rating?: number;
}

interface PropertyCardProps {
  property: Property;
  onLike?: () => void;
  isLiked?: boolean;
}

const PropertyCard: React.FC<PropertyCardProps> = ({ 
  property, 
  onLike, 
  isLiked = false 
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const amenitiesList = Array.isArray(property.amenities) 
    ? property.amenities 
    : property.amenities.split(',').map(a => a.trim()).filter(a => a);

  const priceFormatted = typeof property.price === 'number' 
    ? property.price.toLocaleString('en-IN') 
    : property.price;

  const imageUrl = property.thumbnail_url 
    ? `${import.meta.env.VITE_API_URL}${property.thumbnail_url}`
    : null;

  return (
    <motion.div
      whileHover={{ y: -8 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      <Card 
        onClick={() => {
          console.log(`[Analytics] Event: View_Property_Click_${property.id}`);
          navigate(`/listings/${property.id}`);
        }}
        sx={{ 
          position: 'relative', 
          overflow: 'hidden',
          maxWidth: 400,
          margin: 'auto',
          cursor: 'pointer'
        }}
      >
        <Box sx={{ position: 'relative', height: 220, overflow: 'hidden' }}>
          {imageUrl ? (
            <CardMedia
              component="img"
              height="220"
              image={imageUrl}
              alt={property.title}
              sx={{ 
                transition: 'transform 0.5s ease',
                '&:hover': { transform: 'scale(1.1)' }
              }}
            />
          ) : (
            <Box 
              sx={{ 
                height: '100%', 
                bgcolor: alpha(theme.palette.primary.main, 0.05),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: theme.palette.primary.main
              }}
            >
              <HomeWork sx={{ fontSize: 60, opacity: 0.3 }} />
            </Box>
          )}

          {/* Overlays */}
          <Box 
            sx={{ 
              position: 'absolute', 
              top: 12, 
              left: 12, 
              zIndex: 1,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(8px)',
              padding: '4px 12px',
              borderRadius: '20px',
              border: '1px solid rgba(255,255,255,0.2)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              gap: 0.5
            }}
          >
            <Star sx={{ color: '#FFD700', fontSize: 16 }} />
            <Typography variant="caption" fontWeight="bold">
              {property.rating || '4.5'}
            </Typography>
          </Box>

          <IconButton 
            onClick={(e) => { e.stopPropagation(); onLike && onLike(); }}
            sx={{ 
              position: 'absolute', 
              top: 10, 
              right: 10, 
              zIndex: 1,
              bgcolor: 'rgba(255,255,255,0.7)',
              '&:hover': { bgcolor: '#fff' }
            }}
          >
            {isLiked ? <Favorite color="error" fontSize="small" /> : <FavoriteBorder fontSize="small" />}
          </IconButton>

          <Box 
            sx={{ 
              position: 'absolute', 
              bottom: 0, 
              left: 0, 
              right: 0, 
              padding: '24px 16px 12px',
              background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%)',
              color: '#fff'
            }}
          >
            <Typography variant="h6" className="mono" sx={{ fontWeight: 700 }}>
              ₹ {priceFormatted}<Typography component="span" variant="caption">/mo</Typography>
            </Typography>
          </Box>
        </Box>

        <CardContent sx={{ pb: 3 }}>
          <Typography 
            variant="h6" 
            noWrap 
            gutterBottom 
            sx={{ 
              fontWeight: 600,
              fontSize: '1.1rem',
              color: theme.palette.text.primary
            }}
          >
            {property.title}
          </Typography>

          <Box display="flex" alignItems="center" gap={0.5} mb={2}>
            <LocationOn sx={{ color: theme.palette.text.secondary, fontSize: 16 }} />
            <Typography 
              variant="body2" 
              color="text.secondary" 
              noWrap
              sx={{ opacity: 0.8 }}
            >
              {property.address}
            </Typography>
          </Box>

          <Box display="flex" flexWrap="wrap" gap={1}>
            {amenitiesList.slice(0, 3).map((amenity, index) => (
              <Chip 
                key={index} 
                label={amenity} 
                size="small"
                variant="outlined"
                sx={{ 
                  borderRadius: '6px',
                  fontSize: '0.65rem',
                  height: 20,
                  borderColor: alpha(theme.palette.primary.main, 0.2),
                  color: theme.palette.primary.main,
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                  fontWeight: 600
                }}
              />
            ))}
            {amenitiesList.length > 3 && (
              <Typography variant="caption" sx={{ alignSelf: 'center', ml: 0.5, fontWeight: 700, color: 'text.secondary' }}>
                + {amenitiesList.length - 3} more
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default PropertyCard;
