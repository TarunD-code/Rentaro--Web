import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, CircularProgress,
  Chip, Divider, Avatar, useTheme, alpha, Paper, Stepper, Step, StepLabel
} from '@mui/material';
import { Receipt, Download, CheckCircle, ArrowBack } from '@mui/icons-material';
import { motion } from 'framer-motion';

const SettlementPage: React.FC = () => {
  const { settlementId } = useParams<{ settlementId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [settlement, setSettlement] = useState<any>(null);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchSettlement(); }, [settlementId]);

  const fetchSettlement = async () => {
    try {
      const resp = await fetch(`${API}/payment/moveout/settlement/${settlementId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setSettlement(await resp.json());
      else throw new Error('Not found');
    } catch {
      setSettlement({
        id: Number(settlementId), moveout_id: 1, agreement_id: 1,
        tenant_id: 'tenant@rentora.com', owner_id: 'owner@rentora.com',
        deposit_amount: 50000, pending_rent: 0, cleaning_charge: 3000,
        damage_charge: 5000, total_deductions: 8000, refund_amount: 42000,
        status: 'draft', deductions_json: '[]', owner_notes: null,
      });
    } finally { setLoading(false); }
  };

  const handleFinalize = async () => {
    setFinalizing(true);
    try {
      const resp = await fetch(`${API}/payment/moveout/settlement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ moveout_id: settlement.moveout_id }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setSettlement(data);
      }
    } catch (e: any) { setError(e.message); }
    finally { setFinalizing(false); }
  };

  const handleDownload = () => {
    if (settlement?.settlement_pdf_url) {
      window.open(`${API}${settlement.settlement_pdf_url}`, '_blank');
    }
  };

  if (loading) {
    return <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh"><CircularProgress /></Box>;
  }

  if (!settlement) {
    return <Box py={6} textAlign="center"><Typography>Settlement not found.</Typography></Box>;
  }

  const deductions = (() => {
    try { return JSON.parse(settlement.deductions_json || '[]'); } catch { return []; }
  })();

  const isFinalized = settlement.status === 'finalized' || settlement.status === 'paid';

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Button startIcon={<ArrowBack />} onClick={() => navigate('/dashboard')}
            sx={{ textTransform: 'none', fontWeight: 600 }}>Back</Button>
        </Box>

        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Settlement Statement
        </Typography>
        <Box display="flex" alignItems="center" gap={1} mb={4}>
          <Chip label={`STL-${String(settlement.id).padStart(6, '0')}`} size="small" sx={{ fontFamily: 'monospace', fontWeight: 700 }} />
          <Chip label={settlement.status.toUpperCase()} size="small"
            color={isFinalized ? 'success' : 'warning'} sx={{ fontWeight: 700 }} />
        </Box>

        {/* Settlement Breakdown */}
        <Card sx={{ borderRadius: 4, mb: 3, overflow: 'hidden' }}>
          <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04), p: 3 }}>
            <Typography variant="subtitle1" fontWeight={700}>Deposit Breakdown</Typography>
          </Box>
          <CardContent sx={{ p: 3 }}>
            {/* Deposit */}
            <Box display="flex" justifyContent="space-between" mb={1.5}>
              <Typography>Security Deposit</Typography>
              <Typography fontWeight={700} color="success.main">Rs.{settlement.deposit_amount?.toLocaleString()}</Typography>
            </Box>
            <Divider sx={{ my: 1.5 }} />

            {/* Deductions */}
            {settlement.pending_rent > 0 && (
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Pending Rent</Typography>
                <Typography variant="body2" color="error.main" fontWeight={600}>- Rs.{settlement.pending_rent?.toLocaleString()}</Typography>
              </Box>
            )}
            {settlement.cleaning_charge > 0 && (
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Cleaning Charges</Typography>
                <Typography variant="body2" color="error.main" fontWeight={600}>- Rs.{settlement.cleaning_charge?.toLocaleString()}</Typography>
              </Box>
            )}
            {settlement.damage_charge > 0 && (
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Damage Charges</Typography>
                <Typography variant="body2" color="error.main" fontWeight={600}>- Rs.{settlement.damage_charge?.toLocaleString()}</Typography>
              </Box>
            )}

            {/* Custom deductions */}
            {deductions.map((d: any, i: number) => (
              <Box key={i} display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  {d.category?.replace('_', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}: {d.description}
                </Typography>
                <Typography variant="body2" color="error.main" fontWeight={600}>- Rs.{d.amount?.toLocaleString()}</Typography>
              </Box>
            ))}

            <Divider sx={{ my: 2 }} />

            {/* Total */}
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography fontWeight={700}>Total Deductions</Typography>
              <Typography fontWeight={700} color="error.main">- Rs.{settlement.total_deductions?.toLocaleString()}</Typography>
            </Box>

            {/* Refund */}
            <Paper sx={{
              mt: 2, p: 2.5, borderRadius: 3, textAlign: 'center',
              bgcolor: settlement.refund_amount > 0 ? alpha(theme.palette.success.main, 0.08) : alpha(theme.palette.error.main, 0.08),
              border: `2px solid ${settlement.refund_amount > 0 ? theme.palette.success.main : theme.palette.error.main}`,
            }}>
              <Typography variant="caption" color="text.secondary" textTransform="uppercase" letterSpacing={1}>
                {settlement.refund_amount > 0 ? 'Refund to Tenant' : 'Amount Due'}
              </Typography>
              <Typography variant="h4" fontWeight={800}
                color={settlement.refund_amount > 0 ? 'success.main' : 'error.main'}>
                Rs.{Math.abs(settlement.refund_amount)?.toLocaleString()}
              </Typography>
            </Paper>
          </CardContent>
        </Card>

        {/* Owner Notes */}
        {settlement.owner_notes && (
          <Card sx={{ borderRadius: 4, mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" fontWeight={700} mb={1}>Owner Notes</Typography>
              <Typography variant="body2" color="text.secondary">{settlement.owner_notes}</Typography>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <Box display="flex" gap={2}>
          {!isFinalized && (
            <Button variant="contained" size="large" fullWidth onClick={handleFinalize}
              disabled={finalizing} startIcon={finalizing ? <CircularProgress size={20} /> : <CheckCircle />}
              sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, fontSize: 16, textTransform: 'none',
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})` }}>
              {finalizing ? 'Finalizing...' : 'Finalize Settlement'}
            </Button>
          )}
          {isFinalized && (
            <Button variant="contained" size="large" fullWidth onClick={handleDownload}
              startIcon={<Download />}
              sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, fontSize: 16, textTransform: 'none' }}>
              Download Settlement PDF
            </Button>
          )}
        </Box>

        {error && <Typography color="error" mt={2} textAlign="center">{error}</Typography>}
      </motion.div>
    </Box>
  );
};

export default SettlementPage;
