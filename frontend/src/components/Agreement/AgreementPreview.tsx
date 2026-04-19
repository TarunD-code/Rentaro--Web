import React from 'react';
import { Box, Typography, Paper, Divider, Grid, alpha, useTheme } from '@mui/material';
import { Clause } from './AgreementTemplates';

interface AgreementPreviewProps {
  clauses: Clause[];
  financials: {
    rent: number;
    deposit: number;
    bondWeightage: number;
  };
  property?: any;
  tenant?: any;
  owner?: any;
}

const AgreementPreview: React.FC<AgreementPreviewProps> = ({ 
  clauses, 
  financials,
  property,
  tenant,
  owner
}) => {
  const theme = useTheme();
  const date = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 6, 
        minHeight: '800px', 
        bgcolor: '#fff', 
        color: '#333',
        fontFamily: '"Times New Roman", Times, serif',
        border: '1px solid #ddd',
        boxShadow: '0 0 20px rgba(0,0,0,0.05)',
        lineHeight: 1.6
      }}
    >
      <Box textAlign="center" mb={6}>
        <Typography variant="h5" sx={{ fontWeight: 800, textDecoration: 'underline', mb: 1, color: '#000' }}>
          RENTAL AGREEMENT
        </Typography>
        <Typography variant="body2">This agreement is made on this day, {date}</Typography>
      </Box>

      <Box mb={4}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>BETWEEN:</Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>THE OWNER:</strong> {owner?.full_name || '__________________________'}, residing at {owner?.address || '__________________________'}.
        </Typography>
        <Typography variant="body2">
          <strong>AND THE TENANT:</strong> {tenant?.full_name || '__________________________'}, residing at {tenant?.address || '__________________________'}.
        </Typography>
      </Box>

      <Box mb={4}>
        <Typography variant="body2">
          WHEREAS the Owner is the absolute owner of the property situated at <strong>{property?.address || '____________________________________________________'}</strong>.
        </Typography>
      </Box>

      <Divider sx={{ my: 4 }} />

      <Box mb={4}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>CLAUSES & TERMS:</Typography>
        {clauses.filter(c => c.defaultChecked).map((clause, idx) => (
          <Box key={clause.id} sx={{ mb: 2, display: 'flex', gap: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>{idx + 1}.</Typography>
            <Typography variant="body2">{clause.text}</Typography>
          </Box>
        ))}
      </Box>

      <Box mb={4}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>FINANCIAL CONSIDERATIONS:</Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2">Monthly Rent: <strong>₹{financials.rent.toLocaleString()}</strong></Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2">Refundable Deposit: <strong>₹{financials.deposit.toLocaleString()}</strong></Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2">Rentora Bond Coverage: <strong>{financials.bondWeightage}%</strong></Typography>
          </Grid>
        </Grid>
      </Box>

      <Box mt={15} display="flex" justifyContent="space-between">
        <Box textAlign="center">
          <Typography variant="body2">_________________________</Typography>
          <Typography variant="body2" sx={{ fontWeight: 700 }}>Signature of Owner</Typography>
        </Box>
        <Box textAlign="center">
          <Typography variant="body2">_________________________</Typography>
          <Typography variant="body2" sx={{ fontWeight: 700 }}>Signature of Tenant</Typography>
        </Box>
      </Box>

      <Box mt={10} textAlign="center" sx={{ opacity: 0.5 }}>
        <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
          This is a system-generated preview. Final branded PDF will be issued after verification.
        </Typography>
      </Box>
    </Paper>
  );
};

export default AgreementPreview;
