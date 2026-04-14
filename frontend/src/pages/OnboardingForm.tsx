import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Button, TextField, Alert, CircularProgress,
  Stepper, Step, StepLabel, Card, CardContent, Chip, useTheme, alpha, MenuItem
} from '@mui/material';
import { PersonAdd, Upload, CheckCircle, Send } from '@mui/icons-material';
import { motion } from 'framer-motion';

const STEPS = ['Personal Details', 'KYC Documents', 'Review & Submit'];

const KYC_TYPES = [
  { value: 'aadhaar', label: 'Aadhaar Card' },
  { value: 'pan', label: 'PAN Card' },
  { value: 'passport', label: 'Passport' },
  { value: 'voter_id', label: 'Voter ID' },
  { value: 'driving_licence', label: 'Driving Licence' },
];

const OnboardingForm: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Personal details
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState(localStorage.getItem('email') || '');
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('');
  const [address, setAddress] = useState('');
  const [emergencyContact, setEmergencyContact] = useState('');
  const [occupation, setOccupation] = useState('');
  const [employer, setEmployer] = useState('');

  // KYC
  const [kycType, setKycType] = useState('aadhaar');
  const [kycNumber, setKycNumber] = useState('');
  const [onboardingId, setOnboardingId] = useState<number | null>(null);

  const API = import.meta.env.VITE_API_URL;
  const token = localStorage.getItem('token');

  const handleInitiate = async () => {
    if (!fullName.trim() || !email.trim() || !phone.trim()) {
      setError('Name, email, and phone are required.'); return;
    }
    setSubmitting(true); setError(null);
    try {
      const resp = await fetch(`${API}/onboarding/onboarding/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          tenant_id: email, full_name: fullName, email, phone,
          date_of_birth: dob || null, permanent_address: address || null,
          emergency_contact: emergencyContact || null,
          occupation: occupation || null, employer: employer || null,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setOnboardingId(data.id);
        setStep(1);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to initiate onboarding');
      }
    } catch (e: any) { setError(e.message); }
    finally { setSubmitting(false); }
  };

  const handleKYCUpload = async () => {
    if (!kycNumber.trim()) { setError('Document number required.'); return; }
    setSubmitting(true); setError(null);
    try {
      const resp = await fetch(`${API}/onboarding/onboarding/kyc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          onboarding_id: onboardingId, document_type: kycType,
          document_number: kycNumber, file_url: `/uploads/kyc/${kycType}_${onboardingId}.pdf`,
        }),
      });
      if (resp.ok) { setStep(2); }
      else { const err = await resp.json(); throw new Error(err.detail || 'Failed'); }
    } catch (e: any) { setError(e.message); }
    finally { setSubmitting(false); }
  };

  const handleFinalSubmit = () => { setSubmitted(true); };

  if (submitted) {
    return (
      <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <Alert icon={<CheckCircle />} severity="success" sx={{ mb: 3, borderRadius: 3, py: 2 }}>
            <Typography fontWeight={700}>Onboarding Submitted!</Typography>
            <Typography variant="body2">Your KYC documents are under review. We'll notify you once verified.</Typography>
          </Alert>
          <Box display="flex" gap={2}>
            <Button variant="contained" fullWidth onClick={() => navigate('/dashboard')}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>Dashboard</Button>
            <Button variant="outlined" fullWidth onClick={() => navigate('/onboarding/agreements')}
              sx={{ borderRadius: 3, textTransform: 'none', fontWeight: 700, py: 1.5 }}>View Agreements</Button>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3, maxWidth: 700, mx: 'auto' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -1 }}>Tenant Onboarding</Typography>
        <Typography variant="body1" color="text.secondary" mb={3}>Complete your profile to get started.</Typography>

        <Stepper activeStep={step} alternativeLabel sx={{ mb: 4 }}>
          {STEPS.map(l => <Step key={l}><StepLabel>{l}</StepLabel></Step>)}
        </Stepper>

        {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 3 }}>{error}</Alert>}

        {/* Step 0: Personal Details */}
        {step === 0 && (
          <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2}>Personal Information</Typography>
              <Box display="flex" gap={2} mb={2}>
                <TextField fullWidth label="Full Name *" value={fullName} onChange={e => setFullName(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
                <TextField fullWidth label="Phone *" value={phone} onChange={e => setPhone(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              </Box>
              <Box display="flex" gap={2} mb={2}>
                <TextField fullWidth label="Email *" value={email} onChange={e => setEmail(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
                <TextField fullWidth label="Date of Birth" type="date" value={dob} onChange={e => setDob(e.target.value)}
                  InputLabelProps={{ shrink: true }} sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              </Box>
              <TextField fullWidth label="Permanent Address" value={address} onChange={e => setAddress(e.target.value)}
                multiline rows={2} sx={{ mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <Box display="flex" gap={2} mb={2}>
                <TextField fullWidth label="Occupation" value={occupation} onChange={e => setOccupation(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
                <TextField fullWidth label="Employer" value={employer} onChange={e => setEmployer(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              </Box>
              <TextField fullWidth label="Emergency Contact" value={emergencyContact} onChange={e => setEmergencyContact(e.target.value)}
                sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <Button variant="contained" fullWidth onClick={handleInitiate} disabled={submitting}
                startIcon={submitting ? <CircularProgress size={20} /> : <PersonAdd />}
                sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}>
                {submitting ? 'Saving...' : 'Continue to KYC'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 1: KYC Upload */}
        {step === 1 && (
          <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2}>Upload ID Proof</Typography>
              <TextField select fullWidth label="Document Type" value={kycType} onChange={e => setKycType(e.target.value)}
                sx={{ mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}>
                {KYC_TYPES.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
              </TextField>
              <TextField fullWidth label="Document Number" value={kycNumber} onChange={e => setKycNumber(e.target.value)}
                placeholder="e.g., ABCDE1234F" sx={{ mb: 2, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
              <Button variant="outlined" fullWidth startIcon={<Upload />}
                sx={{ mb: 3, py: 4, borderRadius: 3, borderStyle: 'dashed', textTransform: 'none', fontWeight: 600 }}>
                Upload Document (PDF/Image)
              </Button>
              <Button variant="contained" fullWidth onClick={handleKYCUpload} disabled={submitting}
                sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}>
                {submitting ? 'Uploading...' : 'Submit KYC'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Review */}
        {step === 2 && (
          <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2}>Review & Submit</Typography>
              <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.03), p: 2, borderRadius: 2, mb: 2 }}>
                <Typography variant="body2"><strong>Name:</strong> {fullName}</Typography>
                <Typography variant="body2"><strong>Email:</strong> {email}</Typography>
                <Typography variant="body2"><strong>Phone:</strong> {phone}</Typography>
                {occupation && <Typography variant="body2"><strong>Occupation:</strong> {occupation}</Typography>}
                <Typography variant="body2"><strong>KYC:</strong> {KYC_TYPES.find(t => t.value === kycType)?.label} — {kycNumber}</Typography>
              </Box>
              <Alert severity="info" sx={{ mb: 2, borderRadius: 2 }}>
                Your documents will be reviewed by an admin. You'll be notified once verified.
              </Alert>
              <Button variant="contained" fullWidth color="success" onClick={handleFinalSubmit}
                startIcon={<Send />}
                sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}>
                Complete Onboarding
              </Button>
            </CardContent>
          </Card>
        )}
      </motion.div>
    </Box>
  );
};

export default OnboardingForm;
