import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Button, Stack, Alert, CircularProgress 
} from '@mui/material';
import { UploadFile, PublishedWithChanges } from '@mui/icons-material';
import { isFeatureEnabled } from '../config/featureFlags';

const ReconciliationAdmin: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    
    try {
      const token = localStorage.getItem('token');
      // Read as base64 or text
      const textParams = await file.text();
      
      const res = await fetch(`${import.meta.env.VITE_API_URL}/payment/payouts/reconcile`, {
          method: 'POST',
          headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ csv_data: textParams })
      });
      
      if (!res.ok) throw new Error("Upload mapping failed");
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
        alert("Upload error: " + err.message);
    } finally {
        setUploading(false);
    }
  };

  if (!isFeatureEnabled('epic7_sprint14_payouts_v1')) {
    return <Alert severity="error">Reconciliation system offline.</Alert>;
  }

  return (
    <Box sx={{ p: 4, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" mb={2} fontWeight="bold">Ledger Reconciliation (Admin)</Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        Upload Razorpay Payouts settlement CSVs to align pending ledger debits with actual bank deposits.
      </Typography>

      <Paper sx={{ p: 4, border: '2px dashed #ccc', textAlign: 'center', mb: 3 }}>
        <input
            accept=".csv"
            style={{ display: 'none' }}
            id="raised-button-file"
            type="file"
            onChange={handleFileChange}
        />
        <label htmlFor="raised-button-file">
            <Button variant="outlined" component="span" startIcon={<UploadFile />}>
            Select Settlement CSV
            </Button>
        </label>
        
        {file && (
            <Typography variant="body2" sx={{ mt: 2, fontWeight: 'bold' }}>
                Selected: {file.name}
            </Typography>
        )}
      </Paper>
      
      <Stack direction="row" justifyContent="center">
          <Button 
            variant="contained" 
            color="primary" 
            size="large"
            disabled={!file || uploading} 
            onClick={handleUpload}
            startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <PublishedWithChanges />}
            sx={{ px: 5 }}
          >
            {uploading ? 'Processing Reconciliation...' : 'Run Reconciliation Engine'}
          </Button>
      </Stack>
      
      {result && (
        <Alert severity="success" sx={{ mt: 4 }}>
            <b>Success!</b> {result.message}
        </Alert>
      )}
    </Box>
  );
};

export default ReconciliationAdmin;
