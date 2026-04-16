import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Chip, CircularProgress,
  TextField, MenuItem, useTheme, alpha, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper
} from '@mui/material';
import { Download } from '@mui/icons-material';
import { motion } from 'framer-motion';

const STATUS_COLORS: Record<string, string> = {
  open: '#e74c3c', assigned: '#2980b9', in_progress: '#f39c12',
  resolved: '#27ae60', closed: '#95a5a6', cancelled: '#7f8c8d',
};

const MaintenanceHistory: React.FC = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<any[]>([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try {
      const resp = await fetch(`${API}/maintenance/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setHistory(await resp.json());
    } catch {
      setHistory([
        { id: 1, category: 'plumbing', title: 'Kitchen tap leaking', priority: 'high', status: 'resolved', created_at: '2026-03-15T10:00:00', resolved_at: '2026-03-17T14:00:00', resolution_notes: 'Replaced washer' },
        { id: 2, category: 'electrical', title: 'Light fixture flickering', priority: 'medium', status: 'closed', created_at: '2026-02-20T09:00:00', resolved_at: '2026-02-21T11:00:00', resolution_notes: 'Replaced bulb and starter' },
        { id: 3, category: 'cleaning', title: 'Deep cleaning before move-in', priority: 'low', status: 'open', created_at: '2026-04-10T08:00:00', resolved_at: null, resolution_notes: null },
      ]);
    } finally { setLoading(false); }
  };

  const handleExport = async () => {
    try {
      const resp = await fetch(`${API}/maintenance/history/export`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'maintenance_history.csv'; a.click();
        URL.revokeObjectURL(url);
      }
    } catch { /* ignore */ }
  };

  const filtered = history.filter(h =>
    (!categoryFilter || h.category === categoryFilter) &&
    (!statusFilter || h.status === statusFilter)
  );

  if (loading) {
    return <Box display="flex" justifyContent="center" minHeight="60vh"><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ py: 3, maxWidth: 900, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: -1 }}>
              Maintenance History
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {filtered.length} request{filtered.length !== 1 ? 's' : ''}
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<Download />} onClick={handleExport}
            sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 2 }}>
            Export CSV
          </Button>
        </Box>

        {/* Filters */}
        <Box display="flex" gap={2} mb={3}>
          <TextField select label="Category" value={categoryFilter} size="small"
            onChange={(e) => setCategoryFilter(e.target.value)}
            sx={{ minWidth: 150, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}>
            <MenuItem value="">All</MenuItem>
            {['plumbing', 'electrical', 'cleaning', 'appliance', 'pest_control', 'carpentry', 'painting', 'other'].map(c => (
              <MenuItem key={c} value={c}>{c.replace('_', ' ')}</MenuItem>
            ))}
          </TextField>
          <TextField select label="Status" value={statusFilter} size="small"
            onChange={(e) => setStatusFilter(e.target.value)}
            sx={{ minWidth: 140, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}>
            <MenuItem value="">All</MenuItem>
            {['open', 'assigned', 'in_progress', 'resolved', 'closed'].map(s => (
              <MenuItem key={s} value={s}>{s.replace('_', ' ')}</MenuItem>
            ))}
          </TextField>
        </Box>

        {/* Table */}
        <TableContainer component={Paper} sx={{ borderRadius: 3, border: `1px solid ${theme.palette.divider}` }}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.03) }}>
                <TableCell sx={{ fontWeight: 700 }}>#</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Issue</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Priority</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Created</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Resolved</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No records found.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map(h => (
                  <TableRow key={h.id} hover sx={{ cursor: 'default' }}>
                    <TableCell>{h.id}</TableCell>
                    <TableCell>
                      <Chip label={h.category.replace('_', ' ')} size="small"
                        sx={{ textTransform: 'capitalize', fontWeight: 600, fontSize: '0.7rem' }} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>{h.title}</Typography>
                      {h.resolution_notes && (
                        <Typography variant="caption" color="text.secondary">
                          {h.resolution_notes}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{
                        color: h.priority === 'urgent' ? '#e74c3c' : h.priority === 'high' ? '#e67e22' : '#666',
                        fontWeight: 600, textTransform: 'capitalize',
                      }}>{h.priority}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={h.status.replace('_', ' ')} size="small"
                        sx={{
                          bgcolor: alpha(STATUS_COLORS[h.status] || '#999', 0.1),
                          color: STATUS_COLORS[h.status], fontWeight: 700,
                          fontSize: '0.7rem', textTransform: 'capitalize',
                        }} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {h.created_at ? new Date(h.created_at).toLocaleDateString('en-IN') : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {h.resolved_at ? new Date(h.resolved_at).toLocaleDateString('en-IN') : '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </motion.div>
    </Box>
  );
};

export default MaintenanceHistory;
