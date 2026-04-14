import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions,
  useTheme, alpha, Divider
} from '@mui/material';
import { Description, Send, CheckCircle, Schedule } from '@mui/icons-material';
import { motion } from 'framer-motion';

const STATUS_COLORS: Record<string, string> = {
  draft: '#95a5a6', generated: '#8e44ad', sent_for_signing: '#f39c12',
  tenant_signed: '#2980b9', owner_signed: '#2980b9',
  fully_signed: '#27ae60', active: '#27ae60', expired: '#e74c3c',
};

const AgreementPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Create form
  const [tenantId, setTenantId] = useState('');
  const [propertyId, setPropertyId] = useState('1');
  const [monthlyRent, setMonthlyRent] = useState('15000');
  const [deposit, setDeposit] = useState('45000');
  const [startDate, setStartDate] = useState('2026-05-01');
  const [endDate, setEndDate] = useState('2027-04-30');

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');
  const email = localStorage.getItem('email') || '';

  useEffect(() => { fetchAgreements(); }, []);

  const fetchAgreements = async () => {
    try {
      const resp = await fetch(`${API}/onboarding/agreements`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setAgreements(await resp.json());
    } catch {
      setAgreements([
        { id: 1, tenant_id: 'tenant@rentora.com', owner_id: 'owner@rentora.com', property_id: 1, monthly_rent: 15000, security_deposit: 45000, status: 'fully_signed', start_date: '2026-01-01', end_date: '2026-12-31', created_at: new Date().toISOString() },
      ]);
    } finally { setLoading(false); }
  };

  const handleCreate = async () => {
    setSubmitting(true);
    try {
      const resp = await fetch(`${API}/onboarding/agreements/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          property_id: Number(propertyId), tenant_id: tenantId || 'tenant@rentora.com',
          owner_id: email, start_date: startDate, end_date: endDate,
          monthly_rent: Number(monthlyRent), security_deposit: Number(deposit),
        }),
      });
      if (resp.ok) { setCreateOpen(false); fetchAgreements(); }
    } catch { /* ignore */ }
    finally { setSubmitting(false); }
  };

  const handleSendForSigning = async (agreementId: number) => {
    try {
      await fetch(`${API}/onboarding/agreements/sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ agreement_id: agreementId }),
      });
      fetchAgreements();
    } catch { /* ignore */ }
  };

  const handleSign = async (agreementId: number, role: string) => {
    try {
      await fetch(`${API}/onboarding/agreements/${agreementId}/sign/${role}`, {
        method: 'POST', headers: { Authorization: `Bearer ${token}` },
      });
      fetchAgreements();
    } catch { /* ignore */ }
  };

  if (loading) return <Box display="flex" justifyContent="center" minHeight="60vh"><CircularProgress /></Box>;

  return (
    <Box sx={{ py: 3, maxWidth: 800, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: -1 }}>Digital Agreements</Typography>
            <Typography variant="body1" color="text.secondary">{agreements.length} agreement{agreements.length !== 1 ? 's' : ''}</Typography>
          </Box>
          <Button variant="contained" startIcon={<Description />} onClick={() => setCreateOpen(true)}
            sx={{ textTransform: 'none', fontWeight: 700, borderRadius: 3 }}>New Agreement</Button>
        </Box>

        {agreements.length === 0 ? (
          <Card sx={{ p: 4, textAlign: 'center', borderRadius: 4 }}>
            <Description sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">No agreements yet.</Typography>
          </Card>
        ) : (
          agreements.map(ag => (
            <Card key={ag.id} sx={{ mb: 2, borderRadius: 3, border: `1px solid ${theme.palette.divider}` }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="subtitle1" fontWeight={700}>AGR-{String(ag.id).padStart(4, '0')}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {ag.tenant_id} ↔ {ag.owner_id} | Property #{ag.property_id}
                    </Typography>
                    <Box display="flex" gap={1} mt={1}>
                      <Chip label={`Rs.${Number(ag.monthly_rent).toLocaleString()}/mo`} size="small" sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                      <Chip label={ag.status.replace(/_/g, ' ')} size="small"
                        sx={{ bgcolor: alpha(STATUS_COLORS[ag.status] || '#999', 0.1),
                          color: STATUS_COLORS[ag.status], fontWeight: 700, fontSize: '0.7rem', textTransform: 'capitalize' }} />
                    </Box>
                  </Box>
                  <Box display="flex" gap={1} flexDirection="column" alignItems="flex-end">
                    {ag.status === 'generated' && (
                      <Button size="small" variant="contained" startIcon={<Send sx={{ fontSize: 14 }} />}
                        onClick={() => handleSendForSigning(ag.id)}
                        sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, fontSize: '0.75rem' }}>Send for Signing</Button>
                    )}
                    {ag.status === 'sent_for_signing' && (
                      <>
                        <Button size="small" variant="outlined" color="primary" onClick={() => handleSign(ag.id, 'tenant')}
                          sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, fontSize: '0.75rem' }}>Sign as Tenant</Button>
                        <Button size="small" variant="outlined" color="secondary" onClick={() => handleSign(ag.id, 'owner')}
                          sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, fontSize: '0.75rem' }}>Sign as Owner</Button>
                      </>
                    )}
                    {ag.status === 'tenant_signed' && (
                      <Button size="small" variant="contained" color="success" onClick={() => handleSign(ag.id, 'owner')}
                        sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, fontSize: '0.75rem' }}>Owner Sign</Button>
                    )}
                    {ag.status === 'owner_signed' && (
                      <Button size="small" variant="contained" color="success" onClick={() => handleSign(ag.id, 'tenant')}
                        sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, fontSize: '0.75rem' }}>Tenant Sign</Button>
                    )}
                    {(ag.status === 'fully_signed' || ag.status === 'active') && (
                      <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label="Signed" color="success" size="small" sx={{ fontWeight: 700 }} />
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))
        )}

        {/* Create Dialog */}
        <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth
          PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
          <DialogTitle sx={{ fontWeight: 700 }}>Create Agreement</DialogTitle>
          <DialogContent>
            <Box display="flex" gap={2} mb={2} mt={1}>
              <TextField fullWidth label="Tenant Email" value={tenantId} onChange={e => setTenantId(e.target.value)}
                placeholder="tenant@rentora.com" sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField fullWidth label="Property ID" value={propertyId} onChange={e => setPropertyId(e.target.value)}
                type="number" sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
            <Box display="flex" gap={2} mb={2}>
              <TextField fullWidth label="Monthly Rent (Rs.)" value={monthlyRent} onChange={e => setMonthlyRent(e.target.value)}
                type="number" sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField fullWidth label="Security Deposit (Rs.)" value={deposit} onChange={e => setDeposit(e.target.value)}
                type="number" sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
            <Box display="flex" gap={2}>
              <TextField fullWidth label="Start Date" type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }} sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField fullWidth label="End Date" type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                InputLabelProps={{ shrink: true }} sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setCreateOpen(false)} sx={{ textTransform: 'none' }}>Cancel</Button>
            <Button variant="contained" onClick={handleCreate} disabled={submitting}
              sx={{ textTransform: 'none', fontWeight: 700 }}>{submitting ? 'Creating...' : 'Create Agreement'}</Button>
          </DialogActions>
        </Dialog>
      </motion.div>
    </Box>
  );
};

export default AgreementPage;
