import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Card, CardContent, Chip, Avatar, Button, useTheme, alpha } from '@mui/material';
import { Assignment, CheckCircle } from '@mui/icons-material';

interface OnboardingStatusCardProps { role?: string; }

const OnboardingStatusCard: React.FC<OnboardingStatusCardProps> = ({ role = 'tenant' }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch(`${API}/onboarding/stats`, { headers: { Authorization: `Bearer ${token}` } });
        if (resp.ok) { const d = await resp.json(); if (d.total_onboardings > 0 || d.total_agreements > 0) setStats(d); }
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading || !stats) return null;

  return (
    <Card sx={{
      borderRadius: 4,
      border: `1px solid ${alpha(theme.palette.info.main, 0.3)}`,
      background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.02)}, ${alpha(theme.palette.info.main, 0.06)})`,
    }}>
      <CardContent sx={{ p: 2.5 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
          <Box display="flex" alignItems="center" gap={1.5}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.15), color: theme.palette.info.main, width: 36, height: 36 }}>
              <Assignment sx={{ fontSize: 20 }} />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>Onboarding</Typography>
          </Box>
          <Box display="flex" gap={1}>
            {stats.pending_kyc > 0 && <Chip label={`${stats.pending_kyc} KYC Pending`} size="small" sx={{ bgcolor: alpha('#f39c12', 0.1), color: '#f39c12', fontWeight: 700, fontSize: '0.7rem' }} />}
            {stats.pending_signatures > 0 && <Chip label={`${stats.pending_signatures} Sign`} size="small" sx={{ bgcolor: alpha('#8e44ad', 0.1), color: '#8e44ad', fontWeight: 700, fontSize: '0.7rem' }} />}
            {stats.active_agreements > 0 && <Chip icon={<CheckCircle sx={{ fontSize: 12 }} />} label={`${stats.active_agreements} Active`} size="small" sx={{ bgcolor: alpha('#27ae60', 0.1), color: '#27ae60', fontWeight: 700, fontSize: '0.7rem' }} />}
          </Box>
        </Box>
        <Button variant="outlined" fullWidth size="small"
          onClick={() => navigate(role === 'owner' ? '/onboarding/agreements' : '/onboarding/form')}
          sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, fontSize: '0.8rem' }}>
          {role === 'owner' ? 'Manage Agreements' : 'Start Onboarding'}
        </Button>
      </CardContent>
    </Card>
  );
};

export default OnboardingStatusCard;
