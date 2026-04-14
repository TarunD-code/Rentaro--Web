import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Paper, 
  Typography, 
  Button, 
  Stepper, 
  Step, 
  StepLabel,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, Description, History } from '@mui/icons-material';

const steps = ['Draft Generated', 'Signatures Pending', 'Agreement Active'];

const AgreementWorkflow: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [agreement, setAgreement] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);

  const fetchAgreement = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/property/agreements/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setAgreement(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgreement();
  }, [id]);

  const handleSign = async () => {
    setSigning(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/property/agreements/${id}/sign`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const updated = await res.json();
        setAgreement(updated);
        alert(`Signed successfully! Session ID: ${updated.signnow_id}`);
      } else {
        alert("Failed to sign. Are you authorized?");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSigning(false);
    }
  };


  if (loading) return <Box p={10} textAlign="center"><CircularProgress /></Box>;
  if (!agreement) return <Alert severity="error">Agreement not found</Alert>;

  const activeStep = agreement.status === 'draft' ? 0 : agreement.status === 'pending_signatures' ? 1 : 2;

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Typography variant="h4" fontWeight={800} gutterBottom>
        Rental Agreement Workflow
      </Typography>
      
      <Stepper activeStep={activeStep} sx={{ my: 6 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper elevation={0} sx={{ p: 4, borderRadius: 6, border: '1px solid #eee' }}>
        <Box display="flex" alignItems="center" gap={2} mb={4}>
          <Description color="primary" sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h6">Agreement ID: #{agreement.id}</Typography>
            <Typography variant="caption" color="text.secondary">
              Generated on {new Date(agreement.created_at).toLocaleDateString()}
            </Typography>
          </Box>
        </Box>

        <Alert severity="info" sx={{ mb: 4, borderRadius: 3 }}>
          Status: <strong>{agreement.status.replace('_', ' ').toUpperCase()}</strong>
        </Alert>

        <Divider sx={{ my: 4 }} />

        <Box display="flex" gap={2}>
            <Button 
                variant="outlined" 
                href={`${import.meta.env.VITE_API_URL}/property/agreements/${id}/download`} 
                target="_blank"
                startIcon={<Description />}
                sx={{ borderRadius: 3 }}
            >
              Download PDF ({agreement.status})
            </Button>

          
          {agreement.status !== 'active' && (
            <Button 
              variant="contained" 
              onClick={handleSign}
              disabled={signing}
              sx={{ borderRadius: 3, px: 4 }}
            >
              {signing ? 'Connecting...' : 'Sign with E-Sign'}
            </Button>
          )}
        </Box>

        {agreement.status === 'signed' && (
          <Box mt={4} p={3} bgcolor="#f0fdf4" borderRadius={3} display="flex" alignItems="center" gap={2}>
            <CheckCircle color="success" />
            <Box>
                <Typography variant="body2" color="success.main" fontWeight={700}>
                  This agreement is legally active and signed by both parties.
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    Cryptographic Checksum: {agreement.document_hash}
                </Typography>
            </Box>
          </Box>
        )}
      </Paper>

      <Box mt={4}>
        <Button startIcon={<History />} onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default AgreementWorkflow;
