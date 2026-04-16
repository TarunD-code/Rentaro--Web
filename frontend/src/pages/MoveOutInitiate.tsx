import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  TextField, Chip, Divider, Avatar, useTheme, alpha, Dialog,
  DialogTitle, DialogContent, DialogActions, Stepper, Step, StepLabel
} from '@mui/material';
import { ExitToApp, Warning, CalendarMonth } from '@mui/icons-material';
import { motion } from 'framer-motion';

const STEPS = ['Initiate', 'Notice Period', 'Owner Review', 'Settlement', 'Complete'];

const MoveOutInitiate: React.FC = () => {
  const { agreementId } = useParams<{ agreementId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [agreement, setAgreement] = useState<any>(null);
  const [reason, setReason] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [existingMoveout, setExistingMoveout] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchData();
  }, [agreementId]);

  const fetchData = async () => {
    try {
      // Check for existing moveout
      const moveoutResp = await fetch(`${API}/payment/moveout/active/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (moveoutResp.ok) {
        const data = await moveoutResp.json();
        if (data) setExistingMoveout(data);
      }

      // Get agreement details
      const agResp = await fetch(`${API}/property/agreements/${agreementId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (agResp.ok) {
        setAgreement(await agResp.json());
      }
    } catch {
      setAgreement({
        id: Number(agreementId) || 1,
        property_id: 1,
        tenant_id: localStorage.getItem('email') || 'tenant@rentora.com',
        owner_id: 'owner@rentora.com',
        status: 'active',
        property_title: 'Prestige Lakeside Habitat, Whitefield',
        deposit_amount: 50000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    setConfirmOpen(false);

    try {
      const resp = await fetch(`${API}/payment/moveout/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          agreement_id: agreement?.id || Number(agreementId),
          tenant_id: agreement?.tenant_id || localStorage.getItem('email'),
          owner_id: agreement?.owner_id || 'owner@rentora.com',
          property_id: agreement?.property_id || 1,
          reason: reason || null,
          notice_period_days: 30,
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setExistingMoveout(data);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to initiate move-out');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const getActiveStep = (status: string) => {
    const map: Record<string, number> = {
      initiated: 0, notice_period: 1, owner_review: 2,
      settlement_pending: 3, completed: 4,
    };
    return map[status] ?? 0;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  // Show status tracker if move-out already exists
  if (existingMoveout) {
    const vacateDate = new Date(existingMoveout.expected_vacate_date);
    const daysLeft = Math.max(0, Math.ceil((vacateDate.getTime() - Date.now()) / 86400000));

    return (
      <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
            Move-Out Status
          </Typography>
          <Typography variant="body1" color="text.secondary" mb={4}>
            Track your move-out progress.
          </Typography>

          <Stepper activeStep={getActiveStep(existingMoveout.status)} alternativeLabel sx={{ mb: 4 }}>
            {STEPS.map((label) => (
              <Step key={label}><StepLabel>{label}</StepLabel></Step>
            ))}
          </Stepper>

          <Card sx={{ borderRadius: 4, mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight={700}>Notice Period</Typography>
                <Chip
                  label={daysLeft > 0 ? `${daysLeft} days left` : 'Expired'}
                  color={daysLeft > 7 ? 'success' : daysLeft > 0 ? 'warning' : 'error'}
                  sx={{ fontWeight: 700 }}
                />
              </Box>
              <Divider sx={{ mb: 2 }} />
              {[
                ['Expected Vacate Date', vacateDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })],
                ['Agreement', `#${existingMoveout.agreement_id}`],
                ['Status', existingMoveout.status.replace('_', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())],
                ['Reason', existingMoveout.reason || 'Not specified'],
              ].map(([label, value], i) => (
                <Box key={i} display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="body2" fontWeight={600}>{value}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          <Button
            variant="outlined"
            fullWidth
            onClick={() => navigate('/dashboard')}
            sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 600, py: 1.5 }}
          >
            Back to Dashboard
          </Button>
        </motion.div>
      </Box>
    );
  }

  // Not yet initiated — show initiation form
  const vacatePreview = new Date(Date.now() + 30 * 86400000);

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Initiate Move-Out
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={4}>
          Begin the move-out process for your rental agreement.
        </Typography>

        {/* Notice Period Info */}
        <Alert severity="info" sx={{ mb: 3, borderRadius: 3 }} icon={<CalendarMonth />}>
          <Typography fontWeight={700}>30-Day Notice Period</Typography>
          <Typography variant="body2">
            Your expected vacate date will be <strong>{vacatePreview.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</strong>.
            You must continue paying rent during the notice period.
          </Typography>
        </Alert>

        {/* Agreement Summary */}
        <Card sx={{ borderRadius: 4, mb: 3, border: `1px solid ${theme.palette.divider}` }}>
          <CardContent sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Avatar sx={{ bgcolor: alpha(theme.palette.error.main, 0.1), color: 'error.main' }}>
                <ExitToApp />
              </Avatar>
              <Box>
                <Typography variant="subtitle1" fontWeight={700}>
                  {agreement?.property_title || `Property #${agreement?.property_id}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Agreement #{agreement?.id}
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography color="text.secondary">Deposit Amount</Typography>
              <Typography fontWeight={700}>Rs.{(agreement?.deposit_amount || 50000).toLocaleString()}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography color="text.secondary">Notice Period</Typography>
              <Typography fontWeight={600}>30 days</Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Reason */}
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Reason for moving out (optional)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
        />

        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>{error}</Alert>}

        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={() => setConfirmOpen(true)}
          disabled={submitting}
          color="error"
          startIcon={submitting ? <CircularProgress size={20} /> : <ExitToApp />}
          sx={{
            py: 1.8, borderRadius: 3, fontWeight: 700, fontSize: 16, textTransform: 'none',
            boxShadow: `0 4px 14px ${alpha(theme.palette.error.main, 0.3)}`,
          }}
        >
          {submitting ? 'Processing...' : 'Initiate Move-Out'}
        </Button>

        {/* Confirmation Dialog */}
        <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)} PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
          <DialogTitle sx={{ fontWeight: 700 }}>
            <Box display="flex" alignItems="center" gap={1}>
              <Warning color="warning" /> Confirm Move-Out
            </Box>
          </DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary">
              By initiating move-out, you agree to a <strong>30-day notice period</strong>. 
              Rent continues during this period. Your deposit will be refunded after the owner 
              inspects the property and deducts any applicable charges.
            </Typography>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setConfirmOpen(false)} sx={{ textTransform: 'none' }}>Cancel</Button>
            <Button onClick={handleSubmit} variant="contained" color="error" sx={{ textTransform: 'none', fontWeight: 700 }}>
              Confirm Move-Out
            </Button>
          </DialogActions>
        </Dialog>
      </motion.div>
    </Box>
  );
};

export default MoveOutInitiate;
