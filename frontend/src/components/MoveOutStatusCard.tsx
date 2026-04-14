import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Chip, Avatar, useTheme, alpha,
  Button, Stepper, Step, StepLabel, Divider
} from '@mui/material';
import { ExitToApp, RateReview, CalendarMonth } from '@mui/icons-material';

const STEPS = ['Initiated', 'Notice', 'Review', 'Settlement', 'Done'];

interface MoveOutStatusCardProps {
  role?: string;
}

const MoveOutStatusCard: React.FC<MoveOutStatusCardProps> = ({ role = 'tenant' }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [moveout, setMoveout] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchActive(); }, []);

  const fetchActive = async () => {
    try {
      const resp = await fetch(`${API}/payment/moveout/active/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data) setMoveout(data);
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  if (loading || !moveout) return null;

  const stepMap: Record<string, number> = {
    initiated: 0, notice_period: 1, owner_review: 2,
    settlement_pending: 3, completed: 4,
  };
  const activeStep = stepMap[moveout.status] ?? 0;

  const vacateDate = new Date(moveout.expected_vacate_date);
  const daysLeft = Math.max(0, Math.ceil((vacateDate.getTime() - Date.now()) / 86400000));

  const urgencyColor = daysLeft > 7 ? theme.palette.info.main
    : daysLeft > 3 ? theme.palette.warning.main : theme.palette.error.main;

  return (
    <Card sx={{
      borderRadius: 4,
      border: `1px solid ${alpha(urgencyColor, 0.3)}`,
      background: `linear-gradient(135deg, ${alpha(urgencyColor, 0.02)}, ${alpha(urgencyColor, 0.06)})`,
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1.5}>
            <Avatar sx={{ bgcolor: alpha(urgencyColor, 0.15), color: urgencyColor, width: 40, height: 40 }}>
              <ExitToApp sx={{ fontSize: 22 }} />
            </Avatar>
            <Box>
              <Typography variant="subtitle1" fontWeight={700}>Move-Out in Progress</Typography>
              <Typography variant="caption" color="text.secondary">Agreement #{moveout.agreement_id}</Typography>
            </Box>
          </Box>
          <Chip
            size="small"
            label={daysLeft > 0 ? `${daysLeft}d left` : 'Expired'}
            sx={{ bgcolor: alpha(urgencyColor, 0.1), color: urgencyColor, fontWeight: 700 }}
          />
        </Box>

        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 2, '& .MuiStepLabel-label': { fontSize: '0.7rem' } }}>
          {STEPS.map((label) => (
            <Step key={label}><StepLabel>{label}</StepLabel></Step>
          ))}
        </Stepper>

        <Divider sx={{ my: 2 }} />

        <Box display="flex" alignItems="center" gap={0.5} mb={2}>
          <CalendarMonth sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            Vacate by {vacateDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
          </Typography>
        </Box>

        {/* Role-specific actions */}
        {role === 'tenant' && (
          <Button variant="outlined" fullWidth size="small"
            onClick={() => navigate(`/moveout/initiate/${moveout.agreement_id}`)}
            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}>
            View Status
          </Button>
        )}
        {role === 'owner' && moveout.status === 'notice_period' && (
          <Button variant="contained" fullWidth size="small" startIcon={<RateReview />}
            onClick={() => navigate(`/moveout/review/${moveout.id}`)}
            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}>
            Review & Deductions
          </Button>
        )}
        {role === 'owner' && moveout.status === 'settlement_pending' && (
          <Button variant="contained" fullWidth size="small" color="success"
            onClick={() => navigate(`/moveout/review/${moveout.id}`)}
            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}>
            View Settlement
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default MoveOutStatusCard;
