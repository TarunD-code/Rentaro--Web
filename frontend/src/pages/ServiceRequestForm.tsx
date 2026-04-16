import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Button, Alert, CircularProgress,
  TextField, MenuItem, Chip, useTheme, alpha
} from '@mui/material';
import {
  Build, Plumbing, ElectricalServices, CleaningServices,
  BugReport, Carpenter, FormatPaint, MoreHoriz, Send, CheckCircle
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const CATEGORIES = [
  { value: 'plumbing', label: 'Plumbing', icon: <Plumbing />, color: '#2980b9' },
  { value: 'electrical', label: 'Electrical', icon: <ElectricalServices />, color: '#f39c12' },
  { value: 'cleaning', label: 'Cleaning', icon: <CleaningServices />, color: '#27ae60' },
  { value: 'appliance', label: 'Appliance', icon: <Build />, color: '#8e44ad' },
  { value: 'pest_control', label: 'Pest Control', icon: <BugReport />, color: '#e74c3c' },
  { value: 'carpentry', label: 'Carpentry', icon: <Carpenter />, color: '#d35400' },
  { value: 'painting', label: 'Painting', icon: <FormatPaint />, color: '#1abc9c' },
  { value: 'other', label: 'Other', icon: <MoreHoriz />, color: '#7f8c8d' },
];

const PRIORITIES = [
  { value: 'low', label: 'Low', color: '#27ae60' },
  { value: 'medium', label: 'Medium', color: '#f39c12' },
  { value: 'high', label: 'High', color: '#e67e22' },
  { value: 'urgent', label: 'Urgent', color: '#e74c3c' },
];

const ServiceRequestForm: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const [category, setCategory] = useState('');
  const [priority, setPriority] = useState('medium');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdRequest, setCreatedRequest] = useState<any>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  const handleSubmit = async () => {
    if (!category || !title.trim()) {
      setError('Please select a category and provide a title.');
      return;
    }
    setSubmitting(true);
    setError(null);

    try {
      const resp = await fetch(`${API}/maintenance/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          property_id: 1,
          tenant_id: localStorage.getItem('email') || 'admin@rentora.com',
          owner_id: 'owner@rentora.com',
          category, title,
          description: description || null,
          photo_urls: [],
          priority,
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setCreatedRequest(data);
        setSubmitted(true);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to submit request');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted && createdRequest) {
    return (
      <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <Alert icon={<CheckCircle />} severity="success" sx={{ mb: 3, borderRadius: 3, py: 2 }}>
            <Typography fontWeight={700}>Service Request Submitted!</Typography>
            <Typography variant="body2">
              Request #{createdRequest.id} — {createdRequest.category.replace('_', ' ')} ({createdRequest.priority} priority)
            </Typography>
          </Alert>
          <Box display="flex" gap={2}>
            <Button variant="contained" fullWidth onClick={() => navigate('/dashboard')}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>Dashboard</Button>
            <Button variant="outlined" fullWidth onClick={() => navigate('/maintenance/history')}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>View History</Button>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>
          Raise Service Request
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={4}>
          Report a maintenance issue and we'll get it resolved.
        </Typography>

        {/* Category Selection */}
        <Typography variant="subtitle1" fontWeight={700} mb={2}>Select Category</Typography>
        <Box display="flex" flexWrap="wrap" gap={1.5} mb={3}>
          {CATEGORIES.map(c => (
            <Chip
              key={c.value}
              icon={c.icon}
              label={c.label}
              onClick={() => setCategory(c.value)}
              variant={category === c.value ? 'filled' : 'outlined'}
              sx={{
                py: 2.5, px: 1, fontSize: '0.85rem', fontWeight: 600,
                borderRadius: 3, cursor: 'pointer',
                ...(category === c.value ? {
                  bgcolor: alpha(c.color, 0.15), color: c.color,
                  border: `2px solid ${c.color}`, '& .MuiChip-icon': { color: c.color },
                } : {}),
              }}
            />
          ))}
        </Box>

        {/* Priority */}
        <TextField select fullWidth label="Priority" value={priority}
          onChange={(e) => setPriority(e.target.value)}
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 3 } }}>
          {PRIORITIES.map(p => (
            <MenuItem key={p.value} value={p.value}>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: p.color }} />
                {p.label}
              </Box>
            </MenuItem>
          ))}
        </TextField>

        {/* Title & Description */}
        <TextField fullWidth label="Issue Title" value={title}
          onChange={(e) => setTitle(e.target.value)} placeholder="e.g., Kitchen tap leaking"
          sx={{ mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 3 } }} />

        <TextField fullWidth multiline rows={4} label="Describe the issue"
          value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="Please provide details about the issue, when it started, and any relevant context..."
          sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 3 } }} />

        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>{error}</Alert>}

        <Button variant="contained" size="large" fullWidth onClick={handleSubmit}
          disabled={submitting || !category || !title.trim()}
          startIcon={submitting ? <CircularProgress size={20} /> : <Send />}
          sx={{
            py: 1.8, borderRadius: 3, fontWeight: 700, fontSize: 16, textTransform: 'none',
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
            boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.3)}`,
          }}>
          {submitting ? 'Submitting...' : 'Submit Request'}
        </Button>
      </motion.div>
    </Box>
  );
};

export default ServiceRequestForm;
