import React, { useState, useEffect, useRef } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { ResponsiveContainer } from 'recharts';

interface ResponsiveChartProps {
  children: React.ReactElement;
  height?: number | string;
  minHeight?: number;
  loading?: boolean;
}

/**
 * ResponsiveChart Wrapper
 * Fixes Recharts "0x0" sizing bug in flex/grid layouts.
 * Only renders the chart when the parent container has valid dimensions.
 */
const ResponsiveChart: React.FC<ResponsiveChartProps> = ({ 
  children, 
  height = 350, 
  minHeight = 300,
  loading = false 
}) => {
  const [isReady, setIsReady] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Small delay to ensure layout has settled
    const timer = setTimeout(() => {
      if (containerRef.current && containerRef.current.offsetWidth > 0) {
        setIsReady(true);
      }
    }, 100);

    const handleResize = () => {
      if (containerRef.current && containerRef.current.offsetWidth > 0) {
        setIsReady(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <Box 
      ref={containerRef} 
      sx={{ 
        width: '100%', 
        height: height, 
        minHeight: minHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {loading ? (
        <CircularProgress size={30} thickness={4} />
      ) : isReady ? (
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      ) : null}
    </Box>
  );
};

export default ResponsiveChart;
