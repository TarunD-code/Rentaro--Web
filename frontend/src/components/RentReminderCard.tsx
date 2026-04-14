import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Chip, Avatar,
  useTheme, alpha, Divider, Switch, Tooltip
} from '@mui/material';
import { Payment, AutoMode, CalendarMonth, ArrowForward } from '@mui/icons-material';

interface PaymentSummary {
  total_paid: number;
  total_pending: number;
  next_due_date: string | null;
  next_due_amount: number;
  autopay_active: boolean;
}

const RentReminderCard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [summary, setSummary] = useState<PaymentSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const resp = await fetch(`${API}/payment/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        setSummary(await resp.json());
      }
    } catch {
      // Use mock data
      setSummary({
        total_paid: 100000,
        total_pending: 25000,
        next_due_date: new Date(Date.now() + 7 * 86400000).toISOString(),
        next_due_amount: 25000,
        autopay_active: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) return null;

  const dueDate = summary.next_due_date ? new Date(summary.next_due_date) : null;
  const daysUntilDue = dueDate
    ? Math.ceil((dueDate.getTime() - Date.now()) / 86400000)
    : null;

  // Color coding: green > 7 days, amber 3-7, red < 3
  const urgencyColor =
    daysUntilDue === null ? theme.palette.grey[400] :
    daysUntilDue > 7 ? theme.palette.success.main :
    daysUntilDue > 3 ? theme.palette.warning.main :
    theme.palette.error.main;

  return (
    <Card
      sx={{
        borderRadius: 4,
        border: `1px solid ${alpha(urgencyColor, 0.3)}`,
        background: `linear-gradient(135deg, ${alpha(urgencyColor, 0.03)}, ${alpha(urgencyColor, 0.08)})`,
        overflow: 'visible',
        position: 'relative',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1.5}>
            <Avatar sx={{ bgcolor: alpha(urgencyColor, 0.15), color: urgencyColor, width: 40, height: 40 }}>
              <Payment sx={{ fontSize: 22 }} />
            </Avatar>
            <Typography variant="subtitle1" fontWeight={700}>
              Rent Payment
            </Typography>
          </Box>
          {summary.autopay_active && (
            <Chip
              size="small"
              icon={<AutoMode sx={{ fontSize: 14 }} />}
              label="Auto-Pay On"
              color="success"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>

        {/* Amount & Due Date */}
        {summary.next_due_amount > 0 && (
          <Box mb={2}>
            <Typography variant="h4" fontWeight={800} color={urgencyColor} sx={{ lineHeight: 1 }}>
              ₹{summary.next_due_amount.toLocaleString()}
            </Typography>
            {dueDate && (
              <Box display="flex" alignItems="center" gap={0.5} mt={1}>
                <CalendarMonth sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  Due {dueDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                </Typography>
                {daysUntilDue !== null && (
                  <Chip
                    size="small"
                    label={daysUntilDue === 0 ? 'Due today' : daysUntilDue < 0 ? 'Overdue' : `${daysUntilDue}d left`}
                    sx={{
                      ml: 1,
                      bgcolor: alpha(urgencyColor, 0.1),
                      color: urgencyColor,
                      fontWeight: 700,
                      fontSize: '0.7rem',
                    }}
                  />
                )}
              </Box>
            )}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Summary Row */}
        <Box display="flex" justifyContent="space-between" mb={2}>
          <Box textAlign="center">
            <Typography variant="caption" color="text.secondary">Total Paid</Typography>
            <Typography variant="body2" fontWeight={700}>₹{summary.total_paid.toLocaleString()}</Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="caption" color="text.secondary">Pending</Typography>
            <Typography variant="body2" fontWeight={700} color="warning.main">₹{summary.total_pending.toLocaleString()}</Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="caption" color="text.secondary">Auto-Pay</Typography>
            <Typography variant="body2" fontWeight={700} color={summary.autopay_active ? 'success.main' : 'text.secondary'}>
              {summary.autopay_active ? 'Active' : 'Off'}
            </Typography>
          </Box>
        </Box>

        {/* Actions */}
        <Box display="flex" gap={1.5}>
          {summary.next_due_amount > 0 && !summary.autopay_active && (
            <Button
              variant="contained"
              size="small"
              onClick={() => navigate('/payments/deposit/1')}
              startIcon={<Payment />}
              sx={{
                flex: 1,
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 600,
                py: 1,
                background: `linear-gradient(135deg, ${urgencyColor}, ${alpha(urgencyColor, 0.8)})`,
              }}
            >
              Pay Now
            </Button>
          )}
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate('/payments/history')}
            endIcon={<ArrowForward />}
            sx={{ flex: 1, borderRadius: 2, textTransform: 'none', fontWeight: 600, py: 1 }}
          >
            History
          </Button>
          {!summary.autopay_active && (
            <Tooltip title="Set up automatic payments">
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/payments/autopay')}
                startIcon={<AutoMode />}
                sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, py: 1 }}
              >
                Auto-Pay
              </Button>
            </Tooltip>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default RentReminderCard;
