import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Avatar, 
  TextField, 
  useTheme, 
  alpha,
  Divider,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  IconButton,
  Alert,
  Chip,
  Card,
  Button
} from '@mui/material';
import { 
  CloudUpload, 
  CheckCircle, 
  Pending, 
  ArrowBack, 
  VerifiedUser,
  AccountCircle
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

const Profile: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [kycStep, setKycStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }
        const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        let data;
        try {
          data = await response.json();
        } catch (e) {
          throw new Error('Invalid profile response');
        }

        if (response.ok) {
          setProfile(data);
          if (data.kyc_status === 'verified') setKycStep(3);
          else if (data.kyc_status === 'pending_review') setKycStep(2);
          else if (data.kyc_status === 'draft') setKycStep(1);
          else setKycStep(0);
        } else {
          navigate('/login');
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [navigate]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/upload-doc`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error('Invalid upload response');
      }

      if (!response.ok) {
        const detail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        throw new Error(detail || 'Upload failed');
      }
      
      setProfile({ ...profile, kyc_status: 'draft' });
      setKycStep(1);
      setSuccess('Document uploaded successfully! You can submit for review now.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitKyc = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/submit-kyc`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const detail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        throw new Error(detail || 'Submission failed');
      }
      
      setProfile({ ...profile, kyc_status: 'pending_review' });
      setKycStep(2);
      setSuccess('KYC submitted for review.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyKyc = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/verify-kyc`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const detail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        throw new Error(detail || 'Verification request failed');
      }
      // Mock instant verification for this demo
      setTimeout(() => {
        setProfile({ ...profile, kyc_status: 'verified' });
        setKycStep(3);
        setLoading(false);
      }, 1500);
    } catch (err) {
      setError('Verification trigger failed');
      setLoading(false);
    }
  };

  if (loading && !profile) return null;

  return (
    <Box sx={{ py: 2 }}>
      {/* Profile Header */}
      <Box display="flex" alignItems="center" gap={3} mb={5}>
        <IconButton onClick={() => navigate('/dashboard')} sx={{ bgcolor: alpha(theme.palette.text.primary, 0.05) }}>
          <ArrowBack fontSize="small" />
        </IconButton>
        <Typography variant="h4" fontWeight={700}>Account Settings</Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Left Column - Personal Info */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card sx={{ p: 4, textAlign: 'center', height: '100%', borderRadius: 6 }}>
            <Box position="relative" width={100} height={100} mx="auto" mb={3}>
              <Avatar 
                sx={{ width: 100, height: 100, bgcolor: theme.palette.primary.main, fontSize: 32 }}
              >
                {profile?.full_name?.[0] || <AccountCircle fontSize="large" />}
              </Avatar>
              {profile?.kyc_status === 'verified' && (
                <VerifiedUser 
                   sx={{ 
                     position: 'absolute', 
                     bottom: -4, 
                     right: -4, 
                     color: 'success.main', 
                     bgcolor: 'background.paper', 
                     borderRadius: '50%', 
                     p: 0.2, 
                     fontSize: 28 
                   }} 
                />
              )}
            </Box>
            <Typography variant="h5" fontWeight={700}>{profile?.full_name || 'Set Full Name'}</Typography>
            <Typography variant="body2" color="text.secondary" mb={4}>{profile?.email_or_phone}</Typography>
            
            <Divider sx={{ my: 3 }} />

          <Box display="flex" flexDirection="column" gap={3} textAlign="left">
               <TextField 
                 label="Full Name" 
                 defaultValue={profile?.full_name} 
                 variant="filled" 
                 fullWidth 
                 disabled={profile?.kyc_status === 'pending_review' || profile?.kyc_status === 'verified'} 
               />
               <TextField 
                 label="Email / Phone" 
                 defaultValue={profile?.email_or_phone} 
                 variant="filled" 
                 fullWidth 
                 disabled={profile?.kyc_status === 'pending_review' || profile?.kyc_status === 'verified'} 
               />
               <TextField 
                 label="Role" 
                 defaultValue={profile?.role?.toUpperCase()} 
                 variant="filled" 
                 fullWidth 
                 disabled 
               />
               <Button 
                 variant="outlined" 
                 fullWidth 
                 sx={{ mt: 2 }}
                 disabled={profile?.kyc_status === 'pending_review' || profile?.kyc_status === 'verified'}
               >
                 Update Settings
               </Button>
            </Box>
          </Card>
        </Grid>

        {/* Right Column - KYC Verification */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card sx={{ p: 4, height: '100%', borderRadius: 6 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
              <Typography variant="h6" fontWeight={700}>KYC Verification</Typography>
              <Chip 
                label={profile?.kyc_status?.toUpperCase() || 'UNVERIFIED'} 
                color={profile?.kyc_status === 'verified' ? 'success' : 'warning'} 
                size="small" 
                variant="outlined" 
              />
            </Box>

            <AnimatePresence>
               {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
               {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
            </AnimatePresence>

            <Stepper activeStep={kycStep} orientation="vertical">
              <Step>
                <StepLabel>
                  <Typography variant="subtitle2" fontWeight={700}>Upload ID Proof</Typography>
                </StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Please upload a valid government-issued ID (Passport, Aadhaar Card, DL).
                  </Typography>
                  <Box 
                    sx={{ 
                      p: 4, 
                      border: `2px dashed ${theme.palette.divider}`, 
                      borderRadius: 4, 
                      textAlign: 'center',
                      bgcolor: alpha(theme.palette.primary.main, 0.02),
                      '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.05), cursor: 'pointer' }
                    }}
                    component="label"
                  >
                    <input type="file" hidden onChange={handleFileUpload} />
                    <CloudUpload sx={{ mb: 2, fontSize: 40, color: 'primary.main' }} />
                    <Typography variant="body2" fontWeight={600}>Click to upload your ID document</Typography>
                    <Typography variant="caption" color="text.secondary">PNG, JPG or PDF up to 5MB</Typography>
                  </Box>
                  {profile?.kyc_status === 'draft' && (
                    <Button 
                       variant="contained" 
                       sx={{ mt: 2 }} 
                       onClick={handleSubmitKyc} 
                       fullWidth
                    >
                       Submit for Review
                    </Button>
                  )}
                </StepContent>
              </Step>

              <Step>
                <StepLabel>
                  <Typography variant="subtitle2" fontWeight={700}>Under Review</Typography>
                </StepLabel>
                <StepContent>
                  <Box display="flex" alignItems="center" gap={1.5} sx={{ mb: 3 }}>
                    <Pending color="warning" />
                    <Typography variant="body2">Our team is reviewing your documents. This usually takes 24 hours.</Typography>
                  </Box>
                  <Button variant="contained" size="small" onClick={handleVerifyKyc}>Mock Approve (Admin Bypass)</Button>
                </StepContent>
              </Step>

              <Step>
                <StepLabel>
                  <Typography variant="subtitle2" fontWeight={700}>Verified</Typography>
                </StepLabel>
                <StepContent>
                   <Box display="flex" alignItems="center" gap={1.5}>
                     <CheckCircle color="success" />
                     <Typography variant="body2">Verification complete! You have access to all premium features.</Typography>
                   </Box>
                </StepContent>
              </Step>
            </Stepper>

            {profile?.kyc_status === 'verified' && (
              <Box mt={4} p={3} bgcolor={alpha(theme.palette.success.main, 0.1)} borderRadius={4} textAlign="center">
                <CheckCircle sx={{ fontSize: 48, mb: 1.5, color: 'success.main' }} />
                <Typography variant="h6" fontWeight={700}>You're all set!</Typography>
                <Typography variant="body2">Thank you for helping us keep Rentora safe and trusted.</Typography>
              </Box>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Profile;
