import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Chip, Avatar, useTheme, alpha, Button
} from '@mui/material';
import { Build } from '@mui/icons-material';

interface MaintenanceStatusCardProps {
  role?: string;
}

const MaintenanceStatusCard: React.FC<MaintenanceStatusCardProps> = ({ role = 'tenant' }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchStats(); }, []);

  const fetchStats = async () => {
    try {
      const resp = await fetch(`${API}/maintenance/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.total > 0) setStats(data);
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  if (loading || !stats) return null;

  return (
    <Card sx={{
      borderRadius: 4,
      border: `1px solid ${alpha(theme.palette.warning.main, 0.3)}`,
      background: `linear-gradient(135deg, ${alpha(theme.palette.warning.main, 0.02)}, ${alpha(theme.palette.warning.main, 0.06)})`,
    }}>
      <CardContent sx={{ p: 2.5 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
          <Box display="flex" alignItems="center" gap={1.5}>
            <Avatar sx={{ bgcolor: alpha(theme.palette.warning.main, 0.15), color: theme.palette.warning.main, width: 36, height: 36 }}>
              <Build sx={{ fontSize: 20 }} />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>Maintenance</Typography>
          </Box>
          <Box display="flex" gap={1}>
            {stats.open > 0 && <Chip label={`${stats.open} Open`} size="small" sx={{ bgcolor: alpha('#e74c3c', 0.1), color: '#e74c3c', fontWeight: 700, fontSize: '0.7rem' }} />}
            {stats.in_progress > 0 && <Chip label={`${stats.in_progress} Active`} size="small" sx={{ bgcolor: alpha('#f39c12', 0.1), color: '#f39c12', fontWeight: 700, fontSize: '0.7rem' }} />}
          </Box>
        </Box>

        <Button variant="outlined" fullWidth size="small"
          onClick={() => navigate(role === 'owner' ? '/maintenance/assign' : role === 'tenant' ? '/maintenance/request' : '/maintenance/tasks')}
          sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, fontSize: '0.8rem' }}>
          {role === 'owner' ? 'Review Requests' : role === 'tenant' ? 'Raise Request' : 'View Tasks'}
        </Button>
      </CardContent>
    </Card>
  );
};

export default MaintenanceStatusCard;
