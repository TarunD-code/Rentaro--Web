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
  Button,
  Skeleton
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
  const [formData, setFormData] = useState<any>({});

  const isEditable = profile?.kyc_status === 'not_submitted' || profile?.kyc_status === 'verified' || profile?.kyc_status === 'draft';

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
          setFormData({
            first_name: data.first_name || '',
            last_name: data.last_name || '',
            email: data.email || '',
            full_name: data.full_name || '',
            date_of_birth: data.date_of_birth || '',
            age: data.age || '',
            phone_number: data.phone_number || '',
            address: data.address || '',
            permanent_address: data.permanent_address || '',
            city: data.city || '',
            state: data.state || '',
            pincode: data.pincode || '',
          });
          if (data.kyc_status === 'verified') setKycStep(3);
          else if (data.kyc_status === 'pending_review') setKycStep(2);
          else if (data.kyc_status === 'draft') setKycStep(1);
          else setKycStep(0);
        } else {
          setError('Unable to fetch profile data. Please try again.');
        }
      } catch (err) {
        console.error('Profile connection error:', err);
        setError('Connection to profile service failed. Please try again or log in again.');

      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [navigate]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)) {
      setError('Only JPG, PNG or PDF format is allowed.');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/upload-doc?document_type=ID_PROOF`, {
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
      
      // Fetch profile again to update document list
      const profResp = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (profResp.ok) setProfile(await profResp.json());
      
      setKycStep(1);
      setSuccess('Document uploaded successfully! You can submit for review now.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setError('Only JPG or PNG format is allowed for profile photo.');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/upload-photo`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      
      if (!response.ok) throw new Error('Photo upload failed');
      
      const data = await response.json();
      setProfile({ ...profile, photo_url: data.photo_url });
      setSuccess('Profile photo updated!');
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

  const handleUpdateProfile = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setSuccess('Profile updated successfully!');
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  if (loading && !profile) return <Typography padding={5}>Loading profile data...</Typography>;
  if (error && !profile) return <Alert severity="error" sx={{ m: 5 }}>{error}</Alert>;

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
            <Box position="relative" width={120} height={120} mx="auto" mb={3}>
              <Avatar 
                src={profile?.photo_url}
                sx={{ width: 120, height: 120, bgcolor: theme.palette.primary.main, fontSize: 40 }}
              >
                {profile?.full_name?.[0] || <AccountCircle sx={{ fontSize: 80 }} />}
              </Avatar>
              <Box 
                sx={{ 
                  position: 'absolute', 
                  bottom: 0, 
                  right: 0,
                  bgcolor: 'background.paper',
                  borderRadius: '50%',
                  boxShadow: 2
                }}
              >
                <IconButton 
                  component="label" 
                  size="small"
                  sx={{ color: 'primary.main', p: 0.5 }}
                >
                  <input type="file" hidden accept="image/*" onChange={handlePhotoUpload} />
                  <CloudUpload fontSize="small" />
                </IconButton>
              </Box>
              {profile?.kyc_status === 'verified' && (
                <VerifiedUser 
                   sx={{ 
                     position: 'absolute', 
                     top: 0, 
                     right: 0, 
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
            <Typography variant="body2" color="text.secondary" mb={4}>{profile?.email || profile?.phone_number || 'No contact details set'}</Typography>
            
            <Divider sx={{ my: 3 }} />

            <Box display="flex" flexDirection="column" gap={3} textAlign="left">
               {loading && !profile ? (
                 <>
                   <Skeleton variant="rounded" height={56} />
                   <Skeleton variant="rounded" height={56} />
                   <Skeleton variant="rounded" height={56} />
                 </>
               ) : !profile?.full_name ? (
                 <Box py={3} textAlign="center">
                    <AccountCircle sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" fontWeight={700}>Profile not set up yet</Typography>
                    <Typography variant="body2" color="text.secondary" mb={3}>Please fill in your basic details below to start using all features.</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box display="flex" gap={2} mb={2}>
                      <TextField label="First Name" name="first_name" value={formData.first_name || ''} onChange={handleFormChange} variant="filled" fullWidth />
                      <TextField label="Last Name" name="last_name" value={formData.last_name || ''} onChange={handleFormChange} variant="filled" fullWidth />
                    </Box>
                    <TextField label="Email Address" name="email" value={formData.email || ''} onChange={handleFormChange} variant="filled" fullWidth sx={{ mb: 2 }} />
                    <Button variant="contained" fullWidth onClick={handleUpdateProfile}>Setup Profile</Button>
                 </Box>
               ) : (
                 <>
                   <Box display="flex" gap={2}>
                     <TextField label="First Name" name="first_name" value={formData.first_name || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                     <TextField label="Last Name" name="last_name" value={formData.last_name || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   </Box>
                   <TextField label="Email Address" name="email" value={formData.email || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   <Box display="flex" gap={2}>
                     <TextField label="Age" name="age" type="number" value={formData.age || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                     <TextField label="Phone Number" name="phone_number" value={formData.phone_number || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   </Box>
                   <TextField label="Current Address" name="address" value={formData.address || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   <TextField label="Permanent Address" name="permanent_address" value={formData.permanent_address || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   <Box display="flex" gap={2}>
                     <TextField label="City" name="city" value={formData.city || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                     <TextField label="State" name="state" value={formData.state || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                     <TextField label="Pincode" name="pincode" value={formData.pincode || ''} onChange={handleFormChange} variant="filled" fullWidth disabled={!isEditable} />
                   </Box>
                   <Button 
                     variant="contained" 
                     fullWidth 
                     sx={{ mt: 2, py: 1.5, borderRadius: 3 }}
                     disabled={!isEditable || loading}
                     onClick={handleUpdateProfile}
                   >
                     Update Profile Settings
                   </Button>
                 </>
               )}
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
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: alpha(theme.palette.primary.main, 0.02),
                      transition: 'all 0.2s',
                      '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.05), cursor: 'pointer' }
                    }}
                    component="label"
                  >
                    <input type="file" hidden accept=".png,.jpg,.jpeg,.pdf" onChange={handleFileUpload} />
                    <CloudUpload sx={{ mb: 2, fontSize: 48, color: 'primary.main' }} />
                    <Typography variant="body2" fontWeight={700}>Click to upload your ID document</Typography>
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
