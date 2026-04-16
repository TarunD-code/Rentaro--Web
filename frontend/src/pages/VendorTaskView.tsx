import React, { useState, useEffect } from 'react';

import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  useTheme, alpha, Stepper, Step, StepLabel, Divider, TextField, Dialog,
  DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { CheckCircle, PlayArrow } from '@mui/icons-material';
import { motion } from 'framer-motion';

const TASK_STEPS = ['Assigned', 'Accepted', 'In Progress', 'Completed'];

const VendorTaskView: React.FC = () => {
  const theme = useTheme();

  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<any[]>([]);
  const [updateDialog, setUpdateDialog] = useState(false);
  const [selectedReq, setSelectedReq] = useState<any>(null);
  const [actualCost, setActualCost] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchTasks(); }, []);

  const fetchTasks = async () => {
    try {
      const resp = await fetch(`${API}/maintenance/requests/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setRequests(await resp.json());
    } catch {
      setRequests([
        { id: 1, category: 'plumbing', title: 'Kitchen tap leaking', priority: 'high', status: 'assigned', tenant_id: 'tenant@rentora.com', description: 'Tap dripping continuously', created_at: new Date().toISOString() },
      ]);
    } finally { setLoading(false); }
  };

  const getStepIndex = (status: string) => {
    const map: Record<string, number> = { assigned: 0, accepted: 1, in_progress: 2, resolved: 3, completed: 3 };
    return map[status] ?? 0;
  };

  const handleStatusUpdate = async (reqId: number, newStatus: string) => {
    setSubmitting(true);
    try {
      await fetch(`${API}/maintenance/request/${reqId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: newStatus, resolution_notes: notes || null }),
      });
      setUpdateDialog(false);
      setNotes(''); setActualCost('');
      fetchTasks();
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
          My Tasks
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={4}>
          Assigned maintenance tasks — update status as you work.
        </Typography>

        {requests.length === 0 ? (
          <Card sx={{ p: 4, textAlign: 'center', borderRadius: 4 }}>
            <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
            <Typography color="text.secondary">No active tasks. All caught up!</Typography>
          </Card>
        ) : (
          requests.map((req) => (
            <Card key={req.id} sx={{ mb: 3, borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box>
                    <Typography variant="h6" fontWeight={700}>#{req.id} — {req.title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {req.category.replace('_', ' ')} | {req.tenant_id}
                    </Typography>
                  </Box>
                  <Chip label={req.priority} size="small" sx={{ fontWeight: 700, fontSize: '0.75rem',
                    bgcolor: alpha(req.priority === 'urgent' ? '#e74c3c' : req.priority === 'high' ? '#e67e22' : '#f39c12', 0.1),
                    color: req.priority === 'urgent' ? '#e74c3c' : req.priority === 'high' ? '#e67e22' : '#f39c12' }} />
                </Box>

                {req.description && (
                  <Typography variant="body2" color="text.secondary" mb={2} sx={{ bgcolor: alpha(theme.palette.text.primary, 0.03), p: 1.5, borderRadius: 2 }}>
                    {req.description}
                  </Typography>
                )}

                <Stepper activeStep={getStepIndex(req.status)} alternativeLabel sx={{ mb: 2 }}>
                  {TASK_STEPS.map((label) => (
                    <Step key={label}><StepLabel>{label}</StepLabel></Step>
                  ))}
                </Stepper>

                <Divider sx={{ my: 2 }} />

                <Box display="flex" gap={1.5}>
                  {req.status === 'assigned' && (
                    <Button variant="contained" size="small" onClick={() => handleStatusUpdate(req.id, 'in_progress')}
                      startIcon={<PlayArrow />} sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2 }}>
                      Start Work
                    </Button>
                  )}
                  {(req.status === 'in_progress' || req.status === 'assigned') && (
                    <Button variant="contained" color="success" size="small"
                      onClick={() => { setSelectedReq(req); setUpdateDialog(true); }}
                      startIcon={<CheckCircle />} sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2 }}>
                      Mark Resolved
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          ))
        )}

        {/* Resolution Dialog */}
        <Dialog open={updateDialog} onClose={() => setUpdateDialog(false)} maxWidth="sm" fullWidth
          PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
          <DialogTitle sx={{ fontWeight: 700 }}>Resolve #{selectedReq?.id}</DialogTitle>
          <DialogContent>
            <TextField fullWidth multiline rows={3} label="Resolution Notes" value={notes}
              onChange={(e) => setNotes(e.target.value)} placeholder="What was done to fix the issue..."
              sx={{ mt: 1, mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            <TextField fullWidth label="Actual Cost (Rs.)" value={actualCost} type="number"
              onChange={(e) => setActualCost(e.target.value)}
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setUpdateDialog(false)} sx={{ textTransform: 'none' }}>Cancel</Button>
            <Button variant="contained" color="success" onClick={() => handleStatusUpdate(selectedReq?.id, 'resolved')}
              disabled={submitting} sx={{ textTransform: 'none', fontWeight: 700 }}>
              {submitting ? 'Saving...' : 'Confirm Resolution'}
            </Button>
          </DialogActions>
        </Dialog>
      </motion.div>
    </Box>
  );
};

export default VendorTaskView;
