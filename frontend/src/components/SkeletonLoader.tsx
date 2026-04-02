import { 
  Box, 
  Card, 
  CardContent, 
  Skeleton, 
  Grid 
} from '@mui/material';

export const PropertyCardSkeleton = () => (
  <Card sx={{ height: 400, borderRadius: 16 }}>
    <Skeleton variant="rectangular" height={220} animation="wave" />
    <CardContent>
      <Skeleton variant="text" width="60%" sx={{ mb: 1 }} />
      <Skeleton variant="text" width="40%" sx={{ mb: 2 }} />
      <Box display="flex" gap={1}>
        <Skeleton variant="rectangular" width={60} height={20} />
        <Skeleton variant="rectangular" width={60} height={20} />
        <Skeleton variant="rectangular" width={60} height={20} />
      </Box>
    </CardContent>
  </Card>
);

export const PropertyGridSkeleton = ({ count = 6 }) => (
  <Grid container spacing={3}>
    {Array.from({ length: count }).map((_, i) => (
      <Grid key={i} size={{ xs: 12, sm: 6, md: 4 }}>
        <PropertyCardSkeleton />
      </Grid>
    ))}
  </Grid>
);

export const ProfileSkeleton = () => (
  <Box sx={{ p: 4, bgcolor: 'background.paper', borderRadius: 16 }}>
    <Box display="flex" alignItems="center" gap={3} mb={4}>
      <Skeleton variant="circular" width={80} height={80} />
      <Box flex={1}>
        <Skeleton variant="text" width="40%" height={40} />
        <Skeleton variant="text" width="30%" />
      </Box>
    </Box>
    <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 12, mb: 4 }} />
    <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 12 }} />
  </Box>
);
