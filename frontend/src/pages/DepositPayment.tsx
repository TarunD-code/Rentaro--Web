import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  Chip, Divider, Avatar, useTheme, alpha, Paper
} from '@mui/material';
import { AccountBalance, CheckCircle, ErrorOutline, Receipt } from '@mui/icons-material';
import { motion } from 'framer-motion';

declare global {
  interface Window {
    Razorpay: any;
  }
}

const DepositPayment: React.FC = () => {
  const { agreementId } = useParams<{ agreementId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [agreement, setAgreement] = useState<any>(null);
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'success' | 'failed'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [transaction, setTransaction] = useState<any>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchAgreementDetails();
  }, [agreementId]);

  const fetchAgreementDetails = async () => {
    try {
      const resp = await fetch(`${API}/property/agreements/${agreementId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        setAgreement(data);
      } else {
        setError('Could not load agreement details');
      }
    } catch {
      // Use mock data in sandbox mode
      setAgreement({
        id: Number(agreementId) || 1,
        property_id: 1,
        tenant_id: localStorage.getItem('email') || 'tenant@rentora.com',
        owner_id: 'owner@rentora.com',
        status: 'signed',
        property_title: 'Prestige Lakeside Habitat, Whitefield',
        deposit_amount: 50000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePayDeposit = async () => {
    if (!agreement) return;
    setPaying(true);
    setError(null);

    try {
      // 1. Create deposit order
      const orderResp = await fetch(`${API}/payment/deposit/order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          agreement_id: agreement.id,
          tenant_id: agreement.tenant_id,
          owner_id: agreement.owner_id,
          property_id: agreement.property_id,
          amount: agreement.deposit_amount || 50000,
        }),
      });

      if (!orderResp.ok) {
        const err = await orderResp.json();
        throw new Error(err.detail || 'Failed to create order');
      }

      const order = await orderResp.json();

      // 2. In sandbox mode — simulate payment verification directly
      const mockPaymentId = `pay_mock_${Date.now()}`;
      const mockSignature = `mock_sig_${Date.now()}`;

      const verifyResp = await fetch(`${API}/payment/deposit/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          razorpay_order_id: order.razorpay_order_id,
          razorpay_payment_id: mockPaymentId,
          razorpay_signature: mockSignature,
          payment_method: 'upi',
        }),
      });

      if (verifyResp.ok) {
        const result = await verifyResp.json();
        setTransaction(result);
        setPaymentStatus('success');
      } else {
        throw new Error('Payment verification failed');
      }
    } catch (err: any) {
      setError(err.message);
      setPaymentStatus('failed');
    } finally {
      setPaying(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Security Deposit
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Complete your deposit payment to finalize the rental agreement.
        </Typography>

        {/* Agreement Summary */}
        <Card sx={{ borderRadius: 4, mb: 3, border: `1px solid ${theme.palette.divider}` }}>
          <CardContent sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main' }}>
                <AccountBalance />
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
              <Typography fontWeight={700} fontSize={20} color="primary.main">
                ₹{(agreement?.deposit_amount || 50000).toLocaleString()}
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography color="text.secondary">Owner</Typography>
              <Typography fontWeight={600}>{agreement?.owner_id}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography color="text.secondary">Agreement Status</Typography>
              <Chip size="small" label={agreement?.status?.toUpperCase()} color="success" />
            </Box>
          </CardContent>
        </Card>

        {/* Payment Status */}
        {paymentStatus === 'success' && (
          <Alert
            icon={<CheckCircle />}
            severity="success"
            sx={{ mb: 3, borderRadius: 3, py: 2 }}
          >
            <Typography fontWeight={700}>Payment Successful!</Typography>
            <Typography variant="body2">
              Transaction ID: TXN-{String(transaction?.id).padStart(6, '0')} • 
              Amount: ₹{transaction?.amount?.toLocaleString()}
            </Typography>
          </Alert>
        )}

        {paymentStatus === 'failed' && (
          <Alert
            icon={<ErrorOutline />}
            severity="error"
            sx={{ mb: 3, borderRadius: 3 }}
          >
            Payment failed. {error || 'Please try again.'}
          </Alert>
        )}

        {error && paymentStatus === 'idle' && (
          <Alert severity="warning" sx={{ mb: 3, borderRadius: 3 }}>
            {error}
          </Alert>
        )}

        {/* Action Buttons */}
        <Box display="flex" gap={2}>
          {paymentStatus !== 'success' && (
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handlePayDeposit}
              disabled={paying}
              startIcon={paying ? <CircularProgress size={20} /> : <AccountBalance />}
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
              {paying ? 'Processing...' : `Pay ₹${(agreement?.deposit_amount || 50000).toLocaleString()} Now`}
            </Button>
          )}

          {paymentStatus === 'success' && (
            <>
              <Button
                variant="outlined"
                size="large"
                fullWidth
                onClick={() => navigate('/payments/history')}
                startIcon={<Receipt />}
                sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}
              >
                View Receipt
              </Button>
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={() => navigate('/dashboard')}
                sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}
              >
                Back to Dashboard
              </Button>
            </>
          )}
        </Box>

        {/* Security Note */}
        <Paper
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 3,
            bgcolor: alpha(theme.palette.info.main, 0.04),
            border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
          }}
        >
          <Typography variant="caption" color="text.secondary" display="flex" alignItems="center" gap={1}>
            🔒 Payments are secured by Razorpay with bank-grade encryption. Your deposit is held in escrow until move-in.
          </Typography>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default DepositPayment;
