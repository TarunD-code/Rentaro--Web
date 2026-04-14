import { Box, Typography, Grid, Card, CardContent, Avatar, useTheme, alpha, Button, Paper } from '@mui/material';
import { AddCircle, Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HostAnalytics from '../HostAnalytics';
import MoveOutStatusCard from '../MoveOutStatusCard';
import MaintenanceStatusCard from '../MaintenanceStatusCard';
import OnboardingStatusCard from '../OnboardingStatusCard';

interface OwnerDashboardProps {
  agreements: any[];
  metrics?: any;
}

const OwnerDashboard: React.FC<OwnerDashboardProps> = ({ agreements, metrics }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <Box>
      <HostAnalytics metrics={metrics} />

      {/* Move-Out Review Alert */}
      <Box mb={2}>
        <MoveOutStatusCard role="owner" />
      </Box>

      {/* Maintenance Requests */}
      <Box mb={2}>
        <MaintenanceStatusCard role="owner" />
      </Box>

      {/* Onboarding & Agreements */}
      <Box mb={3}>
        <OnboardingStatusCard role="owner" />
      </Box>

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>{t('quick_actions') || 'Property Management'}</Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Card 
            onClick={() => navigate('/create')}
            sx={{ 
              cursor: 'pointer',
              height: '100%',
              borderRadius: 4,
              '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.05), borderColor: theme.palette.primary.main, border: `1px solid ${theme.palette.primary.main}` }
            }}
          >
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', mb: 2, mx: 'auto' }}>
                <AddCircle />
              </Avatar>
              <Typography variant="h6" fontWeight={700}>{t('add_property') || 'Post a New Property'}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Reach millions of potential tenants in seconds.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Card 
            onClick={() => navigate('/listings')}
            sx={{ 
              cursor: 'pointer',
              height: '100%',
              borderRadius: 4,
              '&:hover': { bgcolor: alpha(theme.palette.secondary.main, 0.05), borderColor: theme.palette.secondary.main, border: `1px solid ${theme.palette.secondary.main}` }
            }}
          >
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main', mb: 2, mx: 'auto' }}>
                <Search />
              </Avatar>
              <Typography variant="h6" fontWeight={700}>{t('browse_listings') || 'Manage Your Listings'}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                View performance and manage inquiries.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {agreements.length > 0 && (
        <Box mt={5}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>{t('digital_agreements') || 'Recent Agreements'}</Typography>
            <Button size="small" variant="text" onClick={() => navigate('/agreements')}>{t('see_all') || 'See All'}</Button>
          </Box>
          <Grid container spacing={2}>
            {agreements.slice(0, 3).map((ag) => (
              <Grid size={{ xs: 12 }} key={ag.id}>
                <Paper 
                  onClick={() => navigate(`/agreements/${ag.id}`)}
                  sx={{ p: 2, borderRadius: 3, border: `1px solid ${theme.palette.divider}`, cursor: 'pointer', '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) } }}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body2" fontWeight={700}>Agreement #{ag.id}</Typography>
                      <Typography variant="caption" color="text.secondary">Property ID: {ag.property_id}</Typography>
                    </Box>
                    <Box sx={{ px: 1.5, py: 0.5, borderRadius: 1, bgcolor: ag.status === 'active' ? 'success.main' : 'warning.main', color: '#fff', fontSize: '0.7rem', fontWeight: 700 }}>
                      {ag.status.toUpperCase()}
                    </Box>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default OwnerDashboard;
