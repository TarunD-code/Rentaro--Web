import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  Chip, Divider, Switch, Avatar, useTheme, alpha
} from '@mui/material';
import { AutoMode, Cancel, CreditCard } from '@mui/icons-material';
import { motion } from 'framer-motion';

const AutoPaySetup: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [setting, setSetting] = useState(false);
  const [mandate, setMandate] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    checkExistingMandate();
  }, []);

  const checkExistingMandate = async () => {
    try {
      // Check payment summary which includes autopay status
      const resp = await fetch(`${API}/payment/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.autopay_active) {
          setMandate({ status: 'active', simulated: true });
        }
      }
    } catch {
      // Ignore — may not be running
    } finally {
      setLoading(false);
    }
  };

  const handleSetupAutoPay = async () => {
    setSetting(true);
    setError(null);

    try {
      const resp = await fetch(`${API}/payment/autopay/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tenant_id: localStorage.getItem('email') || 'admin@rentora.com',
          agreement_id: 1,
          property_id: 1,
          max_amount: 30000,
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        // Poll for activation
        await pollMandateStatus(data.id);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Setup failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSetting(false);
    }
  };

  const pollMandateStatus = async (mandateId: number) => {
    // Poll every 2 seconds for up to 10 seconds
    for (let i = 0; i < 5; i++) {
      await new Promise(r => setTimeout(r, 2000));
      try {
        const resp = await fetch(`${API}/payment/autopay/status/${mandateId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (resp.ok) {
          const data = await resp.json();
          setMandate(data);
          if (data.status === 'active') return;
        }
      } catch { /* continue polling */ }
    }
  };

  const handleCancelAutoPay = async () => {
    if (!mandate?.id) return;
    setSetting(true);

    try {
      const resp = await fetch(`${API}/payment/autopay/${mandate.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        setMandate({ ...mandate, status: 'cancelled' });
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSetting(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const isActive = mandate?.status === 'active';
  const isCancelled = mandate?.status === 'cancelled';

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Auto-Pay Setup
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Never miss a rent payment. Set up automatic monthly deductions.
        </Typography>

        {/* Status Card */}
        <Card sx={{ borderRadius: 4, mb: 3, border: `1px solid ${theme.palette.divider}`, overflow: 'visible' }}>
          <CardContent sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar
                  sx={{
                    bgcolor: isActive
                      ? alpha(theme.palette.success.main, 0.1)
                      : alpha(theme.palette.grey[500], 0.1),
                    color: isActive ? 'success.main' : 'text.secondary',
                    width: 56,
                    height: 56,
                  }}
                >
                  <AutoMode sx={{ fontSize: 28 }} />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    Auto-Pay
                  </Typography>
                  <Chip
                    size="small"
                    label={isActive ? 'Active' : isCancelled ? 'Cancelled' : 'Not Set Up'}
                    color={isActive ? 'success' : isCancelled ? 'error' : 'default'}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              </Box>
              {isActive && (
                <Switch checked={true} onChange={handleCancelAutoPay} disabled={setting} color="success" />
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Benefits */}
        {!isActive && !isCancelled && (
          <Card sx={{ borderRadius: 4, mb: 3, bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2}>
                Why Auto-Pay?
              </Typography>
              {[
                { icon: '⏰', text: 'Never miss a due date — pay automatically on the 1st' },
                { icon: '🔒', text: 'Secured by Razorpay\'s bank-grade mandate system' },
                { icon: '📱', text: 'Supports UPI, credit/debit cards, and net banking' },
                { icon: '💸', text: 'Cancel anytime — no lock-in or hidden fees' },
              ].map((item, i) => (
                <Box key={i} display="flex" alignItems="center" gap={2} mb={1.5}>
                  <Typography fontSize={20}>{item.icon}</Typography>
                  <Typography variant="body2" color="text.secondary">{item.text}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Active Mandate Details */}
        {isActive && mandate && (
          <Card sx={{ borderRadius: 4, mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2}>Mandate Details</Typography>
              <Divider sx={{ mb: 2 }} />
              {[
                ['Max Amount', `₹${(mandate.max_amount || 30000).toLocaleString()}`],
                ['Frequency', (mandate.frequency || 'monthly').charAt(0).toUpperCase() + (mandate.frequency || 'monthly').slice(1)],
                ['Next Charge', mandate.next_charge_date ? new Date(mandate.next_charge_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : '1st of next month'],
                ['Subscription ID', mandate.razorpay_subscription_id || '—'],
              ].map(([label, value], i) => (
                <Box key={i} display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="body2" fontWeight={600}>{value}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>{error}</Alert>
        )}

        {/* Action */}
        {!isActive && (
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleSetupAutoPay}
            disabled={setting}
            startIcon={setting ? <CircularProgress size={20} /> : <CreditCard />}
            sx={{
              py: 1.8,
              borderRadius: 3,
              fontWeight: 700,
              fontSize: 16,
              textTransform: 'none',
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.3)}`,
            }}
          >
            {setting ? 'Setting Up...' : 'Enable Auto-Pay'}
          </Button>
        )}

        {isActive && (
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              size="large"
              fullWidth
              onClick={() => navigate('/payments/history')}
              sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}
            >
              Payment History
            </Button>
            <Button
              variant="outlined"
              size="large"
              fullWidth
              color="error"
              onClick={handleCancelAutoPay}
              disabled={setting}
              startIcon={<Cancel />}
              sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}
            >
              Cancel Auto-Pay
            </Button>
          </Box>
        )}
      </motion.div>
    </Box>
  );
};

export default AutoPaySetup;
