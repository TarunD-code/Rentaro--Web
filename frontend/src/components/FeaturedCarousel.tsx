import React from 'react';
import { Box, useTheme, IconButton } from '@mui/material';
import { ArrowForward, ArrowBack } from '@mui/icons-material';
import PropertyCard from './PropertyCard';
import { motion } from 'framer-motion';

interface FeaturedCarouselProps {
  items: any[];
}

const FeaturedCarousel: React.FC<FeaturedCarouselProps> = ({ items }) => {
  const theme = useTheme();

  const next = () => { /* Logic handled by CSS scroll for now */ };
  const prev = () => { /* Logic handled by CSS scroll for now */ };

  if (items.length === 0) return null;

  return (
    <Box sx={{ position: 'relative', overflow: 'hidden', py: 4 }}>
      <Box 
        sx={{ 
          display: 'flex', 
          gap: 4, 
          px: 2,
          overflowX: 'auto',
          scrollSnapType: 'x mandatory',
          scrollbarWidth: 'none',
          '&::-webkit-scrollbar': { display: 'none' },
          pb: 4
        }}
      >
        {items.map((item, i) => (
          <Box 
            key={item.id} 
            sx={{ 
              minWidth: { xs: '100%', sm: 400 }, 
              scrollSnapAlign: 'start',
              flex: '0 0 auto'
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              <PropertyCard 
                 property={item} 
                 isLiked={false}
              />
            </motion.div>
          </Box>
        ))}
      </Box>

      {/* Navigation Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
        <IconButton 
          onClick={prev}
          sx={{ border: `1px solid ${theme.palette.divider}`, p: 1 }}
        >
          <ArrowBack fontSize="small" />
        </IconButton>
        <IconButton 
          onClick={next}
          sx={{ border: `1px solid ${theme.palette.divider}`, p: 1 }}
        >
          <ArrowForward fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );
};

export default FeaturedCarousel;
