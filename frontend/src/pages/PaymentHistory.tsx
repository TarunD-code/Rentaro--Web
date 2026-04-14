import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, CircularProgress, Paper, TextField,
  MenuItem, useTheme, alpha, Avatar, Pagination, IconButton, Tooltip
} from '@mui/material';
import { Receipt, Download, FilterList, CalendarMonth } from '@mui/icons-material';
import { motion } from 'framer-motion';

interface Transaction {
  id: number;
  transaction_type: string;
  amount: number;
  status: string;
  payment_method: string | null;
  paid_at: string | null;
  due_date: string | null;
  created_at: string;
  razorpay_payment_id: string | null;
  property_id: number | null;
  receipt_url: string | null;
}

const statusColors: Record<string, 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  captured: 'success',
  failed: 'error',
  created: 'warning',
  authorized: 'info',
  refunded: 'default',
};

const typeLabels: Record<string, string> = {
  deposit: '🏠 Deposit',
  rent: '💰 Rent',
  refund: '↩️ Refund',
};

const PaymentHistory: React.FC = () => {
  const theme = useTheme();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const perPage = 10;

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchHistory();
  }, [typeFilter, statusFilter]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (typeFilter) params.set('transaction_type', typeFilter);
      if (statusFilter) params.set('status', statusFilter);
      params.set('limit', '50');

      const resp = await fetch(`${API}/payment/history?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        setTransactions(await resp.json());
      }
    } catch {
      // Use empty list
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    const headers = ['ID', 'Type', 'Amount', 'Status', 'Method', 'Date'];
    const rows = transactions.map(t => [
      `TXN-${String(t.id).padStart(6, '0')}`,
      t.transaction_type,
      t.amount,
      t.status,
      t.payment_method || '—',
      t.paid_at || t.created_at,
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rentora_payments_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const paginated = transactions.slice((page - 1) * perPage, page * perPage);
  const totalPages = Math.ceil(transactions.length / perPage);

  return (
    <Box sx={{ py: 3 }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: -1 }}>
              Payment History
            </Typography>
            <Typography variant="body1" color="text.secondary">
              All your transactions in one place.
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={exportCSV}
            sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 600 }}
          >
            Export CSV
          </Button>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 2, borderRadius: 3, mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
          <FilterList color="action" />
          <TextField
            select
            label="Type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="deposit">Deposit</MenuItem>
            <MenuItem value="rent">Rent</MenuItem>
            <MenuItem value="refund">Refund</MenuItem>
          </TextField>
          <TextField
            select
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="captured">Captured</MenuItem>
            <MenuItem value="created">Pending</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="refunded">Refunded</MenuItem>
          </TextField>
          <Chip
            label={`${transactions.length} transactions`}
            size="small"
            sx={{ ml: 'auto' }}
          />
        </Paper>

        {/* Table */}
        {loading ? (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        ) : transactions.length === 0 ? (
          <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 4 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, width: 64, height: 64, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
              <Receipt sx={{ fontSize: 32, color: 'primary.main' }} />
            </Avatar>
            <Typography variant="h6" fontWeight={700} mb={1}>No transactions yet</Typography>
            <Typography color="text.secondary">Your payment history will appear here.</Typography>
          </Paper>
        ) : (
          <>
            <TableContainer component={Paper} sx={{ borderRadius: 3, overflow: 'hidden' }}>
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                    <TableCell sx={{ fontWeight: 700 }}>Transaction</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 700 }} align="right">Amount</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }} align="center">Receipt</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginated.map((txn) => (
                    <TableRow
                      key={txn.id}
                      hover
                      sx={{ '&:last-child td': { border: 0 } }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={600} fontFamily="monospace">
                          TXN-{String(txn.id).padStart(6, '0')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {typeLabels[txn.transaction_type] || txn.transaction_type}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={700}>
                          ₹{txn.amount.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={txn.status.charAt(0).toUpperCase() + txn.status.slice(1)}
                          size="small"
                          color={statusColors[txn.status] || 'default'}
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" textTransform="uppercase" fontSize={12}>
                          {txn.payment_method || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <CalendarMonth sx={{ fontSize: 14, color: 'text.secondary' }} />
                          <Typography variant="body2" color="text.secondary">
                            {new Date(txn.paid_at || txn.created_at).toLocaleDateString('en-IN', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                            })}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        {txn.status === 'captured' && (
                          <Tooltip title="View Receipt">
                            <IconButton size="small" color="primary">
                              <Receipt fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {totalPages > 1 && (
              <Box display="flex" justifyContent="center" mt={3}>
                <Pagination
                  count={totalPages}
                  page={page}
                  onChange={(_, p) => setPage(p)}
                  color="primary"
                />
              </Box>
            )}
          </>
        )}
      </motion.div>
    </Box>
  );
};

export default PaymentHistory;
