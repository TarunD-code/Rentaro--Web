import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import AdminDashboard from '../../components/dashboards/AdminDashboard';

const AdminDashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const agResp = await api.get('/property/agreements/user/list');
        if (agResp && agResp.ok) setAgreements(await agResp.json());

        const metResp = await api.get('/property/metrics');
        if (metResp && metResp.ok) setMetrics(await metResp.json());
      } catch (err: any) {
        console.error('Admin Dashboard Error:', err);
        setError(err.message || 'Connection failed. Please ensure the API Gateway and services are running.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <Box display="flex" justifyContent="center" py={10}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Box sx={{ py: 2 }}>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" fontWeight={800} mb={4}>Admin Control Center</Typography>
        <AdminDashboard agreements={agreements} metrics={metrics} />
      </motion.div>
    </Box>
  );
};

export default AdminDashboardPage;
