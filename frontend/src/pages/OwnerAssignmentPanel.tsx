import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, CircularProgress,
  TextField, Chip, Divider, Avatar, useTheme, alpha, Dialog,
  DialogTitle, DialogContent, DialogActions, MenuItem
} from '@mui/material';
import { PersonAdd, CheckCircle, Build } from '@mui/icons-material';
import { motion } from 'framer-motion';

const PRIORITY_COLORS: Record<string, string> = {
  low: '#27ae60', medium: '#f39c12', high: '#e67e22', urgent: '#e74c3c',
};

const STATUS_COLORS: Record<string, string> = {
  open: '#e74c3c', assigned: '#2980b9', in_progress: '#f39c12',
  resolved: '#27ae60', closed: '#95a5a6',
};

const OwnerAssignmentPanel: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<any[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedReq, setSelectedReq] = useState<any>(null);
  const [vendorName, setVendorName] = useState('');
  const [vendorPhone, setVendorPhone] = useState('');
  const [vendorEmail, setVendorEmail] = useState('');
  const [vendorType, setVendorType] = useState('');
  const [costEstimate, setCostEstimate] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchRequests(); }, []);

  const fetchRequests = async () => {
    try {
      const resp = await fetch(`${API}/maintenance/requests`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setRequests(await resp.json());
    } catch {
      setRequests([
        { id: 1, category: 'plumbing', title: 'Kitchen tap leaking', priority: 'high', status: 'open', tenant_id: 'tenant@rentora.com', created_at: new Date().toISOString() },
        { id: 2, category: 'electrical', title: 'Light not working in bedroom', priority: 'medium', status: 'assigned', tenant_id: 'tenant@rentora.com', created_at: new Date().toISOString() },
      ]);
    } finally { setLoading(false); }
  };

  const handleAssign = async () => {
    if (!vendorName.trim()) return;
    setSubmitting(true);

    try {
      const resp = await fetch(`${API}/maintenance/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          request_id: selectedReq.id,
          vendor_name: vendorName,
          vendor_phone: vendorPhone || null,
          vendor_email: vendorEmail || null,
          vendor_type: vendorType || null,
          cost_estimate: costEstimate ? Number(costEstimate) : null,
        }),
      });

      if (resp.ok) {
        setDialogOpen(false);
        setVendorName(''); setVendorPhone(''); setVendorEmail('');
        fetchRequests();
      }
    } catch { /* ignore */ }
    finally { setSubmitting(false); }
  };

  if (loading) {
    return <Box display="flex" justifyContent="center" minHeight="60vh"><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ py: 3, maxWidth: 800, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Maintenance Requests
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={4}>
          Review tenant requests and assign vendors.
        </Typography>

        {requests.length === 0 ? (
          <Card sx={{ p: 4, textAlign: 'center', borderRadius: 4 }}>
            <Build sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">No pending requests.</Typography>
          </Card>
        ) : (
          requests.map((req) => (
            <Card key={req.id} sx={{ mb: 2, borderRadius: 3, border: `1px solid ${theme.palette.divider}`, '&:hover': { borderColor: alpha(theme.palette.primary.main, 0.3) } }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box flex={1}>
                    <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                      <Typography variant="subtitle1" fontWeight={700}>#{req.id} — {req.title}</Typography>
                    </Box>
                    <Box display="flex" gap={1} mb={1}>
                      <Chip label={req.category.replace('_', ' ')} size="small"
                        sx={{ textTransform: 'capitalize', fontWeight: 600, fontSize: '0.7rem' }} />
                      <Chip label={req.priority} size="small"
                        sx={{ bgcolor: alpha(PRIORITY_COLORS[req.priority] || '#999', 0.1),
                          color: PRIORITY_COLORS[req.priority], fontWeight: 700, fontSize: '0.7rem' }} />
                      <Chip label={req.status.replace('_', ' ')} size="small"
                        sx={{ bgcolor: alpha(STATUS_COLORS[req.status] || '#999', 0.1),
                          color: STATUS_COLORS[req.status], fontWeight: 700, fontSize: '0.7rem', textTransform: 'capitalize' }} />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      From: {req.tenant_id} | {new Date(req.created_at).toLocaleDateString('en-IN')}
                    </Typography>
                  </Box>
                  {(req.status === 'open' || req.status === 'assigned') && (
                    <Button size="small" variant="contained" startIcon={<PersonAdd sx={{ fontSize: 16 }} />}
                      onClick={() => { setSelectedReq(req); setDialogOpen(true); }}
                      sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2, whiteSpace: 'nowrap' }}>
                      Assign
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          ))
        )}

        {/* Assignment Dialog */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth
          PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
          <DialogTitle sx={{ fontWeight: 700 }}>Assign Vendor to #{selectedReq?.id}</DialogTitle>
          <DialogContent>
            <TextField fullWidth label="Vendor Name *" value={vendorName} onChange={(e) => setVendorName(e.target.value)}
              sx={{ mb: 2, mt: 1, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            <Box display="flex" gap={2} mb={2}>
              <TextField fullWidth label="Phone" value={vendorPhone} onChange={(e) => setVendorPhone(e.target.value)}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField fullWidth label="Email" value={vendorEmail} onChange={(e) => setVendorEmail(e.target.value)}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
            <Box display="flex" gap={2}>
              <TextField fullWidth label="Vendor Type" value={vendorType} onChange={(e) => setVendorType(e.target.value)}
                placeholder="e.g., Plumber, Electrician"
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <TextField fullWidth label="Cost Estimate (Rs.)" value={costEstimate} type="number"
                onChange={(e) => setCostEstimate(e.target.value)}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setDialogOpen(false)} sx={{ textTransform: 'none' }}>Cancel</Button>
            <Button variant="contained" onClick={handleAssign} disabled={submitting || !vendorName.trim()}
              sx={{ textTransform: 'none', fontWeight: 700 }}>
              {submitting ? 'Assigning...' : 'Assign Vendor'}
            </Button>
          </DialogActions>
        </Dialog>
      </motion.div>
    </Box>
  );
};

export default OwnerAssignmentPanel;
