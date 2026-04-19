import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import TenantDashboard from '../../components/dashboards/TenantDashboard';

const TenantDashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);

import { api } from '../../services/api';

const TenantDashboardPage: React.FC = () => {
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
        setError(err.message || 'Failed to load dashboard data');
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
        <Typography variant="h4" fontWeight={800} mb={4}>Tenant Dashboard</Typography>
        <TenantDashboard agreements={agreements} metrics={metrics} />
      </motion.div>
    </Box>
  );
};

export default TenantDashboardPage;
