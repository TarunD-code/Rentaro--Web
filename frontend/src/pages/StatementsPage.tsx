import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Grid, Button, 
  Select, MenuItem, FormControl, InputLabel, Alert 
} from '@mui/material';
import { Download, AccountBalance, History } from '@mui/icons-material';
import { isFeatureEnabled } from '../config/featureFlags';

const StatementsPage: React.FC = () => {
  const [selectedMonth, setSelectedMonth] = useState('2026-04');
  const [loading, setLoading] = useState(false);

  // Generate last 6 months for UI
  const getMonths = () => {
    const list = [];
    const date = new Date();
    for (let i = 0; i < 6; i++) {
        const m = (date.getMonth() + 1).toString().padStart(2, '0');
        const y = date.getFullYear();
        list.push({ val: `${y}-${m}`, label: date.toLocaleString('default', { month: 'long', year: 'numeric' }) });
        date.setMonth(date.getMonth() - 1);
    }
    return list;
  };
  const months = getMonths();

  const handleDownload = async () => {
    setLoading(true);
    try {
        const token = localStorage.getItem('token');
        const ownerId = localStorage.getItem('userId');
        
        // Simulating the /owners/me/statements GET request
        // In real backend, returning the generated WeasyPrint statement PDF blob
        
        alert(`Requesting statement generation for ${selectedMonth} via Payment Service...`);
        // e.g. window.open(...) or objectURL
    } catch(err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  if (!isFeatureEnabled('epic7_sprint14_payouts_v1')) {
    return <Alert severity="warning">Statements module is rolling out soon.</Alert>;
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" mb={4} fontWeight="bold">Monthly Statements</Typography>
      
      <Paper elevation={3} sx={{ p: 4, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" mb={1} display="flex" alignItems="center" gap={1}>
            <History color="primary" /> Select Period
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={4}>
            Statements are generated on the 1st of every month summarizing all ledger entries, fees, and rent collected.
        </Typography>
        
        <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} sm={8}>
                <FormControl fullWidth size="medium">
                    <InputLabel>Month</InputLabel>
                    <Select
                        value={selectedMonth}
                        label="Month"
                        onChange={(e) => setSelectedMonth(e.target.value as string)}
                    >
                        {months.map(m => (
                            <MenuItem key={m.val} value={m.val}>{m.label}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
                <Button 
                    variant="contained" 
                    fullWidth 
                    size="large"
                    startIcon={<Download />}
                    onClick={handleDownload}
                    disabled={loading}
                    sx={{ p: 1.5 }}
                >
                    Download PDF
                </Button>
            </Grid>
        </Grid>
      </Paper>
      
      <Alert severity="info" icon={<AccountBalance />}>
        All statements map directly to your <b>Platform Ledger</b> activity. Discrepancies should be reported to standard Rentora admin support within 15 days of generation. By default, Rentora charges a standardized 5% platform fee plus 18% GST.
      </Alert>

    </Box>
  );
};

export default StatementsPage;
