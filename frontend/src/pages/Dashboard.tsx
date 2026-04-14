import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  useTheme, 
  CircularProgress,
  Alert
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

import TenantDashboard from '../components/dashboards/TenantDashboard';
import OwnerDashboard from '../components/dashboards/OwnerDashboard';
import AdminDashboard from '../components/dashboards/AdminDashboard';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch Profile
        try {
          const profResp = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (!profResp.ok) throw new Error('Profile service unavailable');
          const profData = await profResp.json();
          setProfile(profData);
          
          // Ensure role persists
          const activeRole = localStorage.getItem('role') || 'tenant';
          profData.role = activeRole;
        } catch (pErr) {
          console.error('Profile fetch failed:', pErr);
          setError('Could not load profile details. Dashboard might be limited.');
        }

        // Fetch Agreements
        try {
          const agResp = await fetch(`${import.meta.env.VITE_API_URL}/property/agreements/user/list`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (agResp.ok) setAgreements(await agResp.json());
        } catch (aErr) {
          console.error('Agreements fetch failed:', aErr);
        }

        // Fetch Metrics
        try {
          const metResp = await fetch(`${import.meta.env.VITE_API_URL}/property/metrics`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (metResp.ok) setMetrics(await metResp.json());
          else console.warn('Metrics service responded with error');
        } catch (mErr) {
          console.error('Metrics fetch failed:', mErr);
        }
      } catch (err: any) {
        console.error('Core Dashboard Error:', err);
        setError('Dashboard failed to load essential data. Please refresh.');

      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [navigate]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box py={5}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const renderDashboard = () => {
    switch (profile?.role) {
      case 'admin':
        return <AdminDashboard agreements={agreements} metrics={metrics} />;
      case 'owner':
        return <OwnerDashboard agreements={agreements} metrics={metrics} />;
      case 'tenant':
      default:
        return <TenantDashboard agreements={agreements} metrics={metrics} />;
    }
  };

  return (
    <Box sx={{ py: 2 }}>
      {/* Header Section */}
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 5 
        }}
      >
        <Box>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5, letterSpacing: -1 }}>
              {profile?.role === 'admin' ? 'Admin Control Center' : profile?.role === 'owner' ? 'Owner Dashboard' : 'Tenant Dashboard'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back, <span style={{ fontWeight: 700, color: theme.palette.text.primary }}>{profile?.full_name || 'User'}</span>! 
              Here's your summary for today.
            </Typography>
          </motion.div>
        </Box>
      </Box>



      {/* Role-Specific Dashboard Content */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        {renderDashboard()}
      </motion.div>
    </Box>
  );
};

export default Dashboard;
