import { Box, Typography, Grid, Card, CardContent, Avatar, useTheme, alpha, Paper } from '@mui/material';
import { House, ReceiptLong, CheckCircle, Search, Receipt, ExitToApp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import RentReminderCard from '../RentReminderCard';
import MoveOutStatusCard from '../MoveOutStatusCard';
import MaintenanceStatusCard from '../MaintenanceStatusCard';
import OnboardingStatusCard from '../OnboardingStatusCard';

interface TenantDashboardProps {
  agreements: any[];
  metrics?: any;
}

const TenantDashboard: React.FC<TenantDashboardProps> = ({ agreements, metrics }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <Box>
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>{t('quick_actions') || 'Active Leases & Payments'}</Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, textAlign: 'center', height: '100%', bgcolor: alpha(theme.palette.primary.main, 0.02), borderRadius: 4 }}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', mb: 2, mx: 'auto' }}>
              <House />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>{metrics?.total_applications || 0} {t('applications') || 'Active Applications'}</Typography>
            <Typography variant="caption" color="text.secondary">Interested properties</Typography>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, textAlign: 'center', height: '100%', bgcolor: alpha(theme.palette.error.main, 0.02), borderRadius: 4 }}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.error.main, 0.1), color: 'error.main', mb: 2, mx: 'auto' }}>
              <ReceiptLong />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>₹ {(metrics?.pending_rent || 0).toLocaleString()}</Typography>
            <Typography variant="caption" color="text.secondary">{t('monthly_rent')}: Due shortly</Typography>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, textAlign: 'center', height: '100%', bgcolor: alpha(theme.palette.success.main, 0.02), borderRadius: 4 }}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.main', mb: 2, mx: 'auto' }}>
              <CheckCircle />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>{metrics?.total_views || 0}</Typography>
            <Typography variant="caption" color="text.secondary">{t('saved_items') || 'Saved Favorites'}</Typography>
          </Card>
        </Grid>
      </Grid>

      {/* Move-Out Status (if active) */}
      <Box mt={3}>
        <MoveOutStatusCard role="tenant" />
      </Box>

      {/* Maintenance Status */}
      <Box mt={2}>
        <MaintenanceStatusCard role="tenant" />
      </Box>

      {/* Onboarding Status */}
      <Box mt={2}>
        <OnboardingStatusCard role="tenant" />
      </Box>

      {/* Rent Reminder & Payment Section */}
      <Box mt={3}>
        <RentReminderCard />
      </Box>

      {/* Payment History Quick Access */}
      <Box mt={3}>
        <Card 
          onClick={() => navigate('/payments/history')}
          sx={{ 
            cursor: 'pointer',
            borderRadius: 4,
            border: `1px dashed ${theme.palette.divider}`,
            '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02), borderColor: theme.palette.primary.main }
          }}
        >
          <CardContent sx={{ textAlign: 'center', py: 2.5 }}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', mb: 1, mx: 'auto', width: 32, height: 32 }}>
              <Receipt sx={{ fontSize: 20 }} />
            </Avatar>
            <Typography variant="subtitle2" fontWeight={700}>Payment History</Typography>
            <Typography variant="caption" color="text.secondary">View all transactions and receipts.</Typography>
          </CardContent>
        </Card>
      </Box>

      <Box mt={4}>
        <Card 
          onClick={() => navigate('/listings')}
          sx={{ 
            cursor: 'pointer',
            borderRadius: 4,
            border: `1px dashed ${theme.palette.divider}`,
            '&:hover': { bgcolor: alpha(theme.palette.secondary.main, 0.02), borderColor: theme.palette.secondary.main }
          }}
        >
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main', mb: 1, mx: 'auto', width: 32, height: 32 }}>
              <Search sx={{ fontSize: 20 }} />
            </Avatar>
            <Typography variant="subtitle2" fontWeight={700}>{t('find_home')}</Typography>
            <Typography variant="caption" color="text.secondary">Explore thousands of verified listings.</Typography>
          </CardContent>
        </Card>
      </Box>

      {agreements.length > 0 && (
        <Box mt={5}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>{t('digital_agreements') || 'Digital Agreements'}</Typography>
          <Grid container spacing={2}>
            {agreements.map((ag) => (
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
                  {ag.status === 'active' && (
                    <Button
                      size="small"
                      color="error"
                      startIcon={<ExitToApp sx={{ fontSize: 14 }} />}
                      onClick={(e) => { e.stopPropagation(); navigate(`/moveout/initiate/${ag.id}`); }}
                      sx={{ mt: 1, textTransform: 'none', fontSize: '0.75rem', fontWeight: 600 }}
                    >
                      Initiate Move-Out
                    </Button>
                  )}
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default TenantDashboard;
