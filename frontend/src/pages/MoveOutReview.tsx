import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  TextField, MenuItem, useTheme, alpha,
  IconButton, LinearProgress
} from '@mui/material';
import { AddCircle, Delete, CheckCircle, Send } from '@mui/icons-material';
import { motion } from 'framer-motion';

interface DeductionItem {
  category: string;
  description: string;
  amount: number;
  photo_url?: string;
}

const CATEGORIES = [
  { value: 'cleaning', label: 'Cleaning Charges' },
  { value: 'damages', label: 'Damages / Repairs' },
  { value: 'pending_rent', label: 'Pending Rent' },
  { value: 'other', label: 'Other' },
];

const MoveOutReview: React.FC = () => {
  const { moveoutId } = useParams<{ moveoutId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [_moveout, setMoveout] = useState<any>(null);
  const [deductions, setDeductions] = useState<DeductionItem[]>([]);
  const [pendingRent, setPendingRent] = useState(0);
  const [cleaningCharge, setCleaningCharge] = useState(0);
  const [damageCharge, setDamageCharge] = useState(0);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [settlement, setSettlement] = useState<any>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');
  const depositAmount = 50000; // Would come from agreement

  useEffect(() => {
    fetchMoveout();
  }, [moveoutId]);

  const fetchMoveout = async () => {
    try {
      const resp = await fetch(`${API}/payment/moveout/${moveoutId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        setMoveout(await resp.json());
      }
    } catch {
      setMoveout({ id: Number(moveoutId), agreement_id: 1, tenant_id: 'tenant@rentora.com', owner_id: 'owner@rentora.com', property_id: 1, status: 'notice_period' });
    } finally {
      setLoading(false);
    }
  };

  const addDeduction = () => {
    setDeductions([...deductions, { category: 'other', description: '', amount: 0 }]);
  };

  const removeDeduction = (index: number) => {
    setDeductions(deductions.filter((_, i) => i !== index));
  };

  const updateDeduction = (index: number, field: keyof DeductionItem, value: any) => {
    const updated = [...deductions];
    (updated[index] as any)[field] = value;
    setDeductions(updated);
  };

  const totalDeductions = pendingRent + cleaningCharge + damageCharge + deductions.reduce((s, d) => s + d.amount, 0);
  const refundAmount = Math.max(0, depositAmount - totalDeductions);
  const deductionPercent = Math.min(100, (totalDeductions / depositAmount) * 100);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const resp = await fetch(`${API}/payment/moveout/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          moveout_id: Number(moveoutId),
          deductions,
          pending_rent: pendingRent,
          cleaning_charge: cleaningCharge,
          damage_charge: damageCharge,
          owner_notes: notes || null,
          photo_urls: [],
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setSettlement(data);
        setSubmitted(true);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Review submission failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNoDeductions = async () => {
    setPendingRent(0); setCleaningCharge(0); setDamageCharge(0); setDeductions([]);
    // Submit with zero deductions
    setSubmitting(true);
    try {
      const resp = await fetch(`${API}/payment/moveout/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          moveout_id: Number(moveoutId), deductions: [], pending_rent: 0,
          cleaning_charge: 0, damage_charge: 0, owner_notes: 'No deductions - full refund', photo_urls: [],
        }),
      });
      if (resp.ok) { setSettlement(await resp.json()); setSubmitted(true); }
    } catch (err: any) { setError(err.message); }
    finally { setSubmitting(false); }
  };

  if (loading) {
    return <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh"><CircularProgress /></Box>;
  }

  if (submitted && settlement) {
    return (
      <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Alert icon={<CheckCircle />} severity="success" sx={{ mb: 3, borderRadius: 3, py: 2 }}>
            <Typography fontWeight={700}>Review Submitted Successfully</Typography>
            <Typography variant="body2">
              Refund: Rs.{settlement.refund_amount?.toLocaleString()} | Deductions: Rs.{settlement.total_deductions?.toLocaleString()}
            </Typography>
          </Alert>
          <Box display="flex" gap={2}>
            <Button variant="contained" fullWidth onClick={() => navigate(`/moveout/settlement/${settlement.id}`)}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>
              View Settlement
            </Button>
            <Button variant="outlined" fullWidth onClick={() => navigate('/dashboard')}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>
              Dashboard
            </Button>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Move-Out Review
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={4}>
          Inspect the property and record any deductions from the security deposit.
        </Typography>

        {/* Deposit Bar */}
        <Card sx={{ borderRadius: 4, mb: 3, p: 3 }}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2" fontWeight={700}>Security Deposit</Typography>
            <Typography variant="body2" fontWeight={700}>Rs.{depositAmount.toLocaleString()}</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={deductionPercent}
            sx={{ height: 12, borderRadius: 2, bgcolor: alpha(theme.palette.success.main, 0.15),
              '& .MuiLinearProgress-bar': { bgcolor: deductionPercent > 80 ? 'error.main' : deductionPercent > 50 ? 'warning.main' : 'primary.main', borderRadius: 2 } }}
          />
          <Box display="flex" justifyContent="space-between" mt={1}>
            <Typography variant="caption" color="error.main">Deductions: Rs.{totalDeductions.toLocaleString()}</Typography>
            <Typography variant="caption" color="success.main">Refund: Rs.{refundAmount.toLocaleString()}</Typography>
          </Box>
        </Card>

        {/* Quick Charges */}
        <Card sx={{ borderRadius: 4, mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="subtitle1" fontWeight={700} mb={2}>Standard Charges</Typography>
            <Box display="flex" gap={2} mb={2}>
              <TextField type="number" label="Pending Rent" value={pendingRent} fullWidth size="small"
                onChange={(e) => setPendingRent(Math.max(0, Number(e.target.value)))}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField type="number" label="Cleaning" value={cleaningCharge} fullWidth size="small"
                onChange={(e) => setCleaningCharge(Math.max(0, Number(e.target.value)))}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField type="number" label="Damages" value={damageCharge} fullWidth size="small"
                onChange={(e) => setDamageCharge(Math.max(0, Number(e.target.value)))}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
          </CardContent>
        </Card>

        {/* Custom Deductions */}
        <Card sx={{ borderRadius: 4, mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1" fontWeight={700}>Additional Deductions</Typography>
              <Button startIcon={<AddCircle />} onClick={addDeduction} size="small"
                sx={{ textTransform: 'none', fontWeight: 600 }}>
                Add Item
              </Button>
            </Box>
            {deductions.map((d, i) => (
              <Box key={i} display="flex" gap={1} mb={2} alignItems="center">
                <TextField select value={d.category} size="small" sx={{ minWidth: 140, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                  onChange={(e) => updateDeduction(i, 'category', e.target.value)}>
                  {CATEGORIES.map(c => <MenuItem key={c.value} value={c.value}>{c.label}</MenuItem>)}
                </TextField>
                <TextField placeholder="Description" value={d.description} size="small" fullWidth
                  onChange={(e) => updateDeduction(i, 'description', e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
                <TextField type="number" placeholder="Amount" value={d.amount} size="small" sx={{ width: 120, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                  onChange={(e) => updateDeduction(i, 'amount', Math.max(0, Number(e.target.value)))} />
                <IconButton onClick={() => removeDeduction(i)} color="error" size="small"><Delete /></IconButton>
              </Box>
            ))}
            {deductions.length === 0 && (
              <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                No additional deductions. Click "Add Item" to add one.
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* Notes */}
        <TextField fullWidth multiline rows={2} label="Owner Notes (optional)" value={notes}
          onChange={(e) => setNotes(e.target.value)} sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 3 } }} />

        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>{error}</Alert>}

        {/* Actions */}
        <Box display="flex" gap={2}>
          <Button variant="contained" size="large" fullWidth onClick={handleSubmit} disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : <Send />}
            sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, fontSize: 16, textTransform: 'none',
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.3)}` }}>
            Submit Review
          </Button>
          <Button variant="outlined" size="large" onClick={handleNoDeductions} disabled={submitting}
            color="success" sx={{ py: 1.8, borderRadius: 3, fontWeight: 700, textTransform: 'none', whiteSpace: 'nowrap' }}>
            No Deductions
          </Button>
        </Box>
      </motion.div>
    </Box>
  );
};

export default MoveOutReview;
