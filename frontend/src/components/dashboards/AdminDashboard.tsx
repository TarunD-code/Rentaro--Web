import React from 'react';
import { Box, Typography, Grid, Paper, useTheme, alpha, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material';
import { AdminPanelSettings, Analytics, People, VerifiedUser, Warning, Gavel } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HostAnalytics from '../HostAnalytics';

interface AdminDashboardProps {
  agreements: any[];
  metrics?: any;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ agreements, metrics }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  useTranslation();

  const adminStats = [
    { label: 'Total Properties', value: metrics?.total_active_listings || '0', icon: <People color="primary" />, color: theme.palette.primary.main },
    { label: 'Total Views', value: metrics?.total_views || '0', icon: <VerifiedUser color="success" />, color: theme.palette.success.main },
    { label: 'Pending Applications', value: metrics?.total_applications || '0', icon: <Warning color="warning" />, color: theme.palette.warning.main },
    { label: 'Est. Revenue', value: `₹${(metrics?.pending_rent || 0).toLocaleString()}`, icon: <Gavel color="error" />, color: theme.palette.error.main },
  ];

  return (
    <Box>
       {/* Global Stats */}
      <Grid container spacing={3} mb={5}>
        {adminStats.map((stat, i) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
            <Paper 
              sx={{ 
                p: 2.5, 
                borderRadius: 4, 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2,
                border: `1px solid ${alpha(stat.color, 0.1)}`,
                bgcolor: alpha(stat.color, 0.02)
              }}
            >
              <Box sx={{ p: 1, bgcolor: alpha(stat.color, 0.1), borderRadius: 2, display: 'flex' }}>
                {stat.icon}
              </Box>
              <Box>
                <Typography variant="h6" fontWeight={700}>{stat.value}</Typography>
                <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Global Market Performance</Typography>
      <HostAnalytics />

      <Typography variant="h6" sx={{ fontWeight: 700, mt: 5, mb: 3 }}>System-Wide Agreements</Typography>
      <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
        <Table>
          <TableHead sx={{ bgcolor: alpha(theme.palette.background.default, 0.5) }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>ID</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Tenant</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Owner</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Property</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
             {agreements.length > 0 ? (
               agreements.slice(0, 10).map((ag) => (
                <TableRow key={ag.id} hover onClick={() => navigate(`/agreements/${ag.id}`)} sx={{ cursor: 'pointer' }}>
                  <TableCell>#{ag.id}</TableCell>
                  <TableCell>{ag.tenant_id.split('@')[0]}</TableCell>
                  <TableCell>{ag.owner_id.split('@')[0]}</TableCell>
                  <TableCell>{ag.property_id}</TableCell>
                  <TableCell>
                    <Chip 
                      label={ag.status.toUpperCase()} 
                      size="small" 
                      color={ag.status === 'active' ? 'success' : 'warning'} 
                      sx={{ fontWeight: 700, fontSize: '0.65rem' }} 
                    />
                  </TableCell>
                </TableRow>
              ))
             ) : (
               <TableRow>
                 <TableCell colSpan={5} align="center">No agreements found in the system.</TableCell>
               </TableRow>
             )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 5, display: 'flex', gap: 2 }}>
        <Button variant="contained" startIcon={<AdminPanelSettings />} sx={{ borderRadius: 3 }}>User Management</Button>
        <Button variant="outlined" startIcon={<Analytics />} sx={{ borderRadius: 3 }}>Export Global Data</Button>
      </Box>
    </Box>
  );
};

export default AdminDashboard;
