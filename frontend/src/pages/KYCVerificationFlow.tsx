import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Alert, CircularProgress,
  Divider, Checkbox, FormControlLabel, TextField, Grid, Avatar,
  useTheme, alpha, Stepper, Step, StepLabel,
  Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import {
  VerifiedUser, Security, Fingerprint, CheckCircle, Error as ErrorIcon, ArrowBack,
  Replay, Assignment, Shield, Upload, CameraAlt, Create, Delete
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface FileDropZoneProps {
  label: string;
  file: File | null;
  setFile: (f: File | null) => void;
  accept: string;
  theme: any;
  alpha: any;
}

const FileDropZone: React.FC<FileDropZoneProps> = ({ label, file, setFile, accept, theme, alpha }) => {
  const [dragOver, setDragOver] = useState(false);
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };
  
  const handleDragLeave = () => {
    setDragOver(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };
  
  return (
    <Box
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      sx={{
        border: `2px dashed ${dragOver ? theme.palette.primary.main : theme.palette.divider}`,
        borderRadius: 3,
        p: 2.5,
        textAlign: 'center',
        bgcolor: dragOver ? alpha(theme.palette.primary.main, 0.05) : 'transparent',
        transition: 'all 0.2s',
        cursor: 'pointer',
        display: 'block',
        '&:hover': {
          borderColor: theme.palette.primary.main,
          bgcolor: alpha(theme.palette.primary.main, 0.02)
        }
      }}
      component="label"
    >
      <input type="file" hidden accept={accept} onChange={handleFileChange} />
      {file ? (
        <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
          <CheckCircle color="success" sx={{ fontSize: 32 }} />
          <Typography variant="body2" fontWeight={700}>{file.name}</Typography>
          <Typography variant="caption" color="text.secondary">{(file.size / 1024).toFixed(1)} KB</Typography>
          <Button size="small" color="error" variant="text" onClick={(e) => { e.preventDefault(); setFile(null); }} sx={{ mt: 1, textTransform: 'none' }}>Remove</Button>
        </Box>
      ) : (
        <Box>
          <Upload sx={{ color: 'text.secondary', fontSize: 32, mb: 1 }} />
          <Typography variant="body2" fontWeight={600}>Drag & Drop {label}</Typography>
          <Typography variant="caption" color="text.secondary">or click to browse ({accept})</Typography>
        </Box>
      )}
    </Box>
  );
};

const KYCVerificationFlow: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  // API Configuration
  const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('token');

  // Core State
  const [loading, setLoading] = useState(true);
  const [kycStatus, setKycStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Workflow State
  const [inWorkflow, setInWorkflow] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);

  // Step 1: Consent State
  const [consentChecked, setConsentChecked] = useState(false);

  // Step 2: Document Inputs
  const [aadhaar, setAadhaar] = useState('');
  const [pan, setPan] = useState('');
  const [aadhaarError, setAadhaarError] = useState('');
  const [panError, setPanError] = useState('');

  // Step 3: Session State
  const [transactionToken, setTransactionToken] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<'SUCCESS' | 'FAILED' | null>(null);

  // Webcam & Media States
  const [webcamActive, setWebcamActive] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);

  // File Upload States
  const [aadhaarFile, setAadhaarFile] = useState<File | null>(null);
  const [panFile, setPanFile] = useState<File | null>(null);
  const [signatureFile, setSignatureFile] = useState<File | null>(null);

  // Signature Canvas Sketchpad
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [signatureDataUrl, setSignatureDataUrl] = useState<string | null>(null);
  const [signatureModalOpen, setSignatureModalOpen] = useState(false);
  const pointsRef = React.useRef<{ x: number; y: number }[]>([]);

  useEffect(() => {
    const role = localStorage.getItem('role');
    if (role === 'admin' || role === 'ADMIN') {
      navigate('/admin/dashboard');
      return;
    }
    fetchKycStatus();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [navigate]);
  useEffect(() => {
    if (webcamActive && streamRef.current) {
      const bindStream = () => {
        if (videoRef.current) {
          videoRef.current.srcObject = streamRef.current;
          videoRef.current.play().catch(err => console.error("Error playing video:", err));
        } else {
          requestAnimationFrame(bindStream);
        }
      };
      bindStream();
    }
  }, [webcamActive]);

  const startWebcam = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      streamRef.current = stream;
      setWebcamActive(true);
    } catch (err) {
      console.error("Failed to access webcam:", err);
      setError("Could not access webcam. Please verify camera permissions.");
      setWebcamActive(false);
    }
  };
  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setWebcamActive(false);
  };

  const capturePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0, 640, 480);
        const dataUrl = canvas.toDataURL('image/jpeg');
        setCapturedPhoto(dataUrl);
      }
      stopWebcam();
    }
  };

  const retakePhoto = () => {
    setCapturedPhoto(null);
    startWebcam();
  };

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#00467F'; // Brand-blue for e-signature
    
    const { x, y } = getCanvasCoords(e);
    pointsRef.current = [{ x, y }];
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const p = getCanvasCoords(e);
    pointsRef.current.push(p);
    
    const pts = pointsRef.current;
    ctx.beginPath();
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#00467F';
    
    if (pts.length === 2) {
      ctx.moveTo(pts[0].x, pts[0].y);
      ctx.lineTo(pts[1].x, pts[1].y);
      ctx.stroke();
    } else if (pts.length > 2) {
      const xc_prev = (pts[pts.length - 3].x + pts[pts.length - 2].x) / 2;
      const yc_prev = (pts[pts.length - 3].y + pts[pts.length - 2].y) / 2;
      const xc = (pts[pts.length - 2].x + pts[pts.length - 1].x) / 2;
      const yc = (pts[pts.length - 2].y + pts[pts.length - 1].y) / 2;
      ctx.moveTo(xc_prev, yc_prev);
      ctx.quadraticCurveTo(pts[pts.length - 2].x, pts[pts.length - 2].y, xc, yc);
      ctx.stroke();
    }
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    pointsRef.current = [];
    setSignatureDataUrl(null);
  };

  const saveSignature = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      setSignatureDataUrl(canvas.toDataURL());
    }
    setSignatureModalOpen(false);
  };

  const cancelSignatureDrawing = () => {
    setSignatureModalOpen(false);
  };

  const fetchKycStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await fetch(`${API}/kyc/api/v1/kyc/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setKycStatus(data);
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to fetch KYC status');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Input Formatting & Validation
  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (value.length <= 12) {
      // Format as XXXX XXXX XXXX for readability
      const formatted = value.replace(/(\d{4})/g, '$1 ').trim();
      setAadhaar(formatted);
      setAadhaarError('');
    }
  };

  const handlePanChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    if (value.length <= 10) {
      setPan(value);
      setPanError('');
    }
  };

  const validateInputs = () => {
    let isValid = true;
    const cleanAadhaar = aadhaar.replace(/\s+/g, '');

    if (cleanAadhaar.length !== 12) {
      setAadhaarError('Aadhaar number must be exactly 12 digits');
      isValid = false;
    }

    const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]$/;
    if (!panRegex.test(pan)) {
      setPanError('Enter a valid 10-character PAN (e.g. ABCDE1234F)');
      isValid = false;
    }

    return isValid;
  };

  // API Call: Initiate KYC
  const handleInitiateKYC = async () => {
    if (!validateInputs()) return;

    setActionLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API}/kyc/api/v1/kyc/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });

      if (resp.ok) {
        const data = await resp.json();
        setTransactionToken(data.transaction_token);
        setActiveStep(2); // Go to third step
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'KYC session initiation failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // API Call: Simulate Webhook Success or Failure
  const handleSimulateWebhook = async (status: 'VERIFIED' | 'FAILED') => {
    if (!transactionToken) return;

    setActionLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API}/kyc/api/v1/kyc/simulate-webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          transaction_token: transactionToken,
          status: status,
          aadhaar_number: aadhaar.replace(/\s+/g, ''),
          pan_number: pan,
          facial_score: status === 'VERIFIED' ? 0.965 : 0.231,
          vendor_reference_id: `MOCK-VND-${Math.floor(100000 + Math.random() * 900000)}`
        })
      });

      if (resp.ok) {
        setVerificationResult(status === 'VERIFIED' ? 'SUCCESS' : 'FAILED');
        // Refresh status from the backend
        await fetchKycStatus();
      } else {
        const err = await resp.json();
        throw new Error(err.detail || 'Simulation failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetWorkflow = () => {
    setActiveStep(0);
    setConsentChecked(false);
    setAadhaar('');
    setPan('');
    setTransactionToken(null);
    setVerificationResult(null);
    setInWorkflow(true);
  };

  if (loading) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="60vh" gap={2}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">Fetching verification profile...</Typography>
      </Box>
    );
  }

  const steps = ['Consent & DPDP', 'Verification Info', 'Vendor Verification'];

  return (
    <Box sx={{ py: 4, maxWidth: 650, mx: 'auto', px: 2 }}>
      {/* ─────────────────────────────────────────────────────────────
          1. DISPLAY COMPLETED / EXISTING VERIFICATION STATUS
          ───────────────────────────────────────────────────────────── */}
      {!inWorkflow && kycStatus && kycStatus.status === 'VERIFIED' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card sx={{ borderRadius: 5, border: `1px solid ${theme.palette.success.main}`, bgcolor: alpha(theme.palette.success.main, 0.02), mb: 3 }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              <Avatar
                sx={{
                  bgcolor: alpha(theme.palette.success.main, 0.1),
                  color: 'success.main',
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 3
                }}
              >
                <VerifiedUser sx={{ fontSize: 48 }} />
              </Avatar>

              <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: -0.5 }}>
                Identity Verified
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                Your Know Your Customer (KYC) check is active and compliant under DPDP guidelines.
              </Typography>

              <Divider sx={{ my: 3 }} />

              <Grid container spacing={2.5} sx={{ textAlign: 'left', mb: 2 }}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary">MASKED AADHAAR</Typography>
                  <Typography variant="body1" fontWeight={700} sx={{ letterSpacing: 1.5 }}>
                    {kycStatus.masked_aadhaar || 'XXXX-XXXX-XXXX'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary">MASKED PAN</Typography>
                  <Typography variant="body1" fontWeight={700} sx={{ letterSpacing: 1.5 }}>
                    {kycStatus.masked_pan || 'XXXXXXXXXX'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary">FACIAL LIVENESS SCORE</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {kycStatus.facial_match_score ? `${(kycStatus.facial_match_score * 100).toFixed(1)}% Match` : 'N/A'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary">VERIFIED AT</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {kycStatus.verified_at ? new Date(kycStatus.verified_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric'
                    }) : 'Recently'}
                  </Typography>
                </Grid>
              </Grid>

              <Box display="flex" alignItems="center" gap={1} justifyContent="center" sx={{ mt: 3, p: 1.5, bgcolor: alpha(theme.palette.success.main, 0.05), borderRadius: 2 }}>
                <Shield sx={{ fontSize: 18, color: 'success.main' }} />
                <Typography variant="caption" color="success.main" fontWeight={600}>
                  Your raw PII is AES-256 encrypted at rest & isolated.
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Button
            variant="outlined"
            fullWidth
            onClick={() => navigate('/dashboard')}
            sx={{ py: 1.5, borderRadius: 3, fontWeight: 700, textTransform: 'none' }}
          >
            Back to Dashboard
          </Button>
        </motion.div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          2. START / RE-INITIATE SCREEN
          ───────────────────────────────────────────────────────────── */}
      {!inWorkflow && kycStatus && kycStatus.status !== 'VERIFIED' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}`, mb: 3 }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              <Avatar
                sx={{
                  bgcolor: alpha(theme.palette.warning.main, 0.1),
                  color: 'warning.main',
                  width: 72,
                  height: 72,
                  mx: 'auto',
                  mb: 2.5
                }}
              >
                <Fingerprint sx={{ fontSize: 40 }} />
              </Avatar>

              <Typography variant="h5" sx={{ fontWeight: 800, mb: 1, letterSpacing: -0.5 }}>
                Identity Verification Required
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                To rent properties, upload lease agreements, or sign payments, verify your identity using our secure KYC engine.
              </Typography>

              {kycStatus.status === 'FAILED' && (
                <Alert severity="error" sx={{ mb: 3, borderRadius: 2, textAlign: 'left' }}>
                  {kycStatus.message || 'Verification failed. Please ensure the information entered is accurate.'}
                </Alert>
              )}

              <Box sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 3, p: 2, textAlign: 'left', mb: 3 }}>
                <Typography variant="subtitle2" fontWeight={700} mb={1}>🛡️ Privacy & Compliance Policy</Typography>
                <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                  - Fully compliant with the Indian Digital Personal Data Protection (DPDP) Act.
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                  - Column-level symmetric envelope encryption for sensitive fields.
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  - Data shared only with certified sandbox vendor endpoints for verification.
                </Typography>
              </Box>

              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleResetWorkflow}
                sx={{
                  py: 1.8,
                  borderRadius: 3,
                  fontWeight: 700,
                  textTransform: 'none',
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                  boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.2)}`
                }}
              >
                Start Verification
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          3. ACTIVE WORKFLOW STEPPER
          ───────────────────────────────────────────────────────────── */}
      {inWorkflow && (
        <Box>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{error}</Alert>
          )}

          <AnimatePresence mode="wait">
            {/* STEP 0: CONSENT FORM */}
            {activeStep === 0 && (
              <motion.div
                key="step-consent"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}`, mb: 3 }}>
                  <CardContent sx={{ p: 3 }}>
                    <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                      <Assignment color="primary" />
                      <Typography variant="h6" fontWeight={700}>DPDP Consent Agreement</Typography>
                    </Box>
                    <Divider sx={{ mb: 2.5 }} />

                    <Typography variant="body2" color="text.secondary" paragraph>
                      Please review the terms of data processing under the Digital Personal Data Protection (DPDP) Act:
                    </Typography>

                    <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), p: 2, borderRadius: 3, mb: 3, border: `1px solid ${theme.palette.divider}` }}>
                      <Typography variant="subtitle2" fontWeight={700} mb={1}>1. Purpose of Collection</Typography>
                      <Typography variant="caption" color="text.secondary" paragraph>
                        Your Aadhaar and PAN numbers are collected exclusively to perform identity verification to facilitate lease agreements.
                      </Typography>

                      <Typography variant="subtitle2" fontWeight={700} mb={1}>2. Encryption & Security</Typography>
                      <Typography variant="caption" color="text.secondary" paragraph>
                        These documents are encrypted locally using AES-256 (Fernet) before database write. The decrypted values exist only in temporary system memory during verification.
                      </Typography>

                      <Typography variant="subtitle2" fontWeight={700} mb={1}>3. Right to Revoke & Erase</Typography>
                      <Typography variant="caption" color="text.secondary" paragraph>
                        You have the right to request deletion of your records from the dashboard. Once deleted, the encrypted columns are purged completely.
                      </Typography>
                    </Box>

                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={consentChecked}
                          onChange={(e) => setConsentChecked(e.target.checked)}
                          color="primary"
                        />
                      }
                      label={
                        <Typography variant="body2" fontWeight={500}>
                          I give my explicit consent to Rentora to verify and securely store my masked details for property leasing.
                        </Typography>
                      }
                    />
                  </CardContent>
                </Card>

                <Box display="flex" gap={2}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => setInWorkflow(false)}
                    sx={{ py: 1.5, borderRadius: 3, textTransform: 'none', fontWeight: 600 }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant={consentChecked ? "contained" : "outlined"}
                    fullWidth
                    onClick={() => {
                      if (consentChecked) setActiveStep(1);
                    }}
                    className={consentChecked ? "bg-[#00467F] text-white" : "border-2 border-[#00467F] text-[#00467F] bg-transparent"}
                    sx={
                      consentChecked
                        ? { py: 1.5, borderRadius: 3, textTransform: 'none', fontWeight: 700, bgcolor: '#00467F', color: 'white', '&:hover': { bgcolor: '#00335c' } }
                        : { py: 1.5, borderRadius: 3, textTransform: 'none', fontWeight: 600, bgcolor: 'transparent', border: '2px solid #00467F', borderColor: '#00467F', color: '#00467F', '&:hover': { bgcolor: 'rgba(0, 70, 127, 0.05)', border: '2px solid #00467F' } }
                    }
                  >
                    Agree & Continue
                  </Button>
                </Box>
              </motion.div>
            )}
            {/* STEP 1: DOCUMENT INPUTS & MEDIA PIPELINE */}
            {activeStep === 1 && (() => {
              const isVerificationInfoValid = 
                aadhaar.replace(/\s+/g, '').length === 12 && 
                /^[A-Z]{5}[0-9]{4}[A-Z]$/.test(pan) &&
                capturedPhoto !== null &&
                aadhaarFile !== null &&
                panFile !== null &&
                (signatureFile !== null || signatureDataUrl !== null);

              return (
                <motion.div
                  key="step-inputs"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}`, mb: 3 }}>
                    <CardContent sx={{ p: 3 }}>
                      <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                        <Security color="primary" />
                        <Typography variant="h6" fontWeight={700}>Verification Details</Typography>
                      </Box>
                      <Divider sx={{ mb: 3 }} />

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Provide your Aadhaar, PAN, live camera snapshot, document uploads, and signature to proceed.
                      </Typography>

                      <Grid container spacing={3}>
                        {/* Text Inputs */}
                        <Grid size={{ xs: 12, md: 6 }}>
                          <TextField
                            label="Aadhaar Number"
                            fullWidth
                            value={aadhaar}
                            onChange={handleAadhaarChange}
                            error={!!aadhaarError}
                            helperText={aadhaarError || '12-digit number (format: XXXX XXXX XXXX)'}
                            placeholder="0000 0000 0000"
                            InputProps={{
                              startAdornment: <Fingerprint sx={{ mr: 1, color: 'text.secondary' }} />
                            }}
                          />
                        </Grid>
                        <Grid size={{ xs: 12, md: 6 }}>
                          <TextField
                            label="PAN Number"
                            fullWidth
                            value={pan}
                            onChange={handlePanChange}
                            error={!!panError}
                            helperText={panError || '10-character alphanumeric (format: ABCDE1234F)'}
                            placeholder="ABCDE1234F"
                            InputProps={{
                              startAdornment: <Assignment sx={{ mr: 1, color: 'text.secondary' }} />
                            }}
                          />
                        </Grid>

                        {/* Live Webcam Section */}
                        <Grid size={{ xs: 12 }}>
                          <Typography variant="subtitle2" fontWeight={700} mb={1}>Live Identity Photo (Webcam)</Typography>
                          <Box 
                            sx={{ 
                              border: `1px solid ${theme.palette.divider}`, 
                              borderRadius: 3, 
                              overflow: 'hidden', 
                              bgcolor: 'background.default',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              p: 2,
                              gap: 2
                            }}
                          >
                            {capturedPhoto ? (
                              <Box sx={{ width: '100%', maxWidth: 320, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                                <img src={capturedPhoto} alt="Captured Identity" style={{ width: '100%', borderRadius: 8, border: `2px solid ${theme.palette.success.main}` }} />
                                <Typography variant="caption" color="success.main" fontWeight={600}>Photo captured successfully!</Typography>
                              </Box>
                            ) : webcamActive ? (
                              <Box sx={{ width: '100%', maxWidth: 320, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                                <video ref={videoRef} style={{ width: '100%', borderRadius: 8, backgroundColor: '#000' }} autoPlay playsInline muted />
                                <Typography variant="caption" color="text.secondary">Look directly at the camera</Typography>
                              </Box>
                            ) : (
                              <Box sx={{ py: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                                <CameraAlt sx={{ fontSize: 48, color: 'text.secondary' }} />
                                <Typography variant="body2" color="text.secondary">No camera feed active</Typography>
                              </Box>
                            )}

                            <Box display="flex" gap={1.5}>
                              {!webcamActive && !capturedPhoto && (
                                <Button variant="outlined" size="small" onClick={startWebcam} startIcon={<CameraAlt />} sx={{ textTransform: 'none' }}>
                                  Start Camera
                                </Button>
                              )}
                              {webcamActive && (
                                <>
                                  <Button variant="contained" color="primary" size="small" onClick={capturePhoto} sx={{ textTransform: 'none' }}>
                                    Capture Photo
                                  </Button>
                                  <Button variant="text" color="error" size="small" onClick={stopWebcam} sx={{ textTransform: 'none' }}>
                                    Cancel
                                  </Button>
                                </>
                              )}
                              {capturedPhoto && (
                                <Button variant="outlined" size="small" onClick={retakePhoto} startIcon={<Replay />} sx={{ textTransform: 'none' }}>
                                  Retake Photo
                                </Button>
                              )}
                            </Box>
                          </Box>
                        </Grid>

                        {/* Drag and Drop Document Uploads */}
                        <Grid size={{ xs: 12, sm: 6 }}>
                          <Typography variant="subtitle2" fontWeight={700} mb={1}>Upload Aadhaar Card (PDF/Image)</Typography>
                          <FileDropZone label="Aadhaar Card" file={aadhaarFile} setFile={setAadhaarFile} accept=".pdf,image/*" theme={theme} alpha={alpha} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6 }}>
                          <Typography variant="subtitle2" fontWeight={700} mb={1}>Upload PAN Card (PDF/Image)</Typography>
                          <FileDropZone label="PAN Card" file={panFile} setFile={setPanFile} accept=".pdf,image/*" theme={theme} alpha={alpha} />
                        </Grid>

                        {/* Signature Section */}
                        <Grid size={{ xs: 12 }}>
                          <Typography variant="subtitle2" fontWeight={700} mb={1}>E-Signature</Typography>
                          <Grid container spacing={2}>
                            <Grid size={{ xs: 12, sm: 6 }}>
                              <Typography variant="caption" color="text.secondary" display="block" mb={1}>Option A: Draw your signature on the sketchpad</Typography>
                              {signatureDataUrl ? (
                                <Box sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 3, p: 1.5, bgcolor: '#FFFFFF', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                                  <img 
                                    src={signatureDataUrl} 
                                    alt="E-Signature Preview" 
                                    style={{ border: '1px solid #e0e0e0', borderRadius: 4, height: 120, width: '100%', objectFit: 'contain', backgroundColor: '#fafafa' }} 
                                  />
                                  <Box display="flex" justifyContent="space-between" width="100%">
                                    <Typography variant="caption" color="success.main" sx={{ display: 'flex', alignItems: 'center' }}>
                                      ✓ Signature captured
                                    </Typography>
                                    <Button size="small" color="error" variant="text" onClick={clearSignature} startIcon={<Delete />} sx={{ textTransform: 'none', py: 0 }}>Clear</Button>
                                  </Box>
                                </Box>
                              ) : (
                                <Box 
                                  onClick={() => setSignatureModalOpen(true)}
                                  sx={{ 
                                    border: '2px dashed #00467F', 
                                    borderRadius: 3, 
                                    height: 153, 
                                    display: 'flex', 
                                    flexDirection: 'column',
                                    alignItems: 'center', 
                                    justifyContent: 'center', 
                                    cursor: 'pointer',
                                    bgcolor: 'rgba(0, 70, 127, 0.02)',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                      bgcolor: 'rgba(0, 70, 127, 0.05)',
                                      borderColor: '#00335c'
                                    }
                                  }}
                                >
                                  <Create sx={{ color: '#00467F', fontSize: 28, mb: 1 }} />
                                  <Typography variant="body2" color="#00467F" fontWeight={600}>Click to Draw Signature</Typography>
                                </Box>
                              )}
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                              <Typography variant="caption" color="text.secondary" display="block" mb={1}>Option B: Upload signature file (Image/PDF)</Typography>
                              <FileDropZone label="Signature File" file={signatureFile} setFile={setSignatureFile} accept="image/*,.pdf" theme={theme} alpha={alpha} />
                            </Grid>
                          </Grid>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>

                  <Box display="flex" gap={2}>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={() => {
                        stopWebcam();
                        setActiveStep(0);
                      }}
                      disabled={actionLoading}
                      startIcon={<ArrowBack />}
                      sx={{ py: 1.5, borderRadius: 3, textTransform: 'none', fontWeight: 600 }}
                    >
                      Back
                    </Button>
                    <Button
                      variant={isVerificationInfoValid ? "contained" : "outlined"}
                      fullWidth
                      onClick={() => {
                        if (isVerificationInfoValid) {
                          handleInitiateKYC();
                        }
                      }}
                      disabled={actionLoading}
                      startIcon={actionLoading ? <CircularProgress size={20} color="inherit" /> : <Security />}
                      className={isVerificationInfoValid ? "bg-[#00467F] text-white" : "border-2 border-[#00467F] text-[#00467F] bg-transparent"}
                      sx={
                        isVerificationInfoValid
                          ? {
                              py: 1.5,
                              borderRadius: 3,
                              textTransform: 'none',
                              fontWeight: 700,
                              bgcolor: '#00467F',
                              color: 'white',
                              '&:hover': { bgcolor: '#00335c' }
                            }
                          : {
                              py: 1.5,
                              borderRadius: 3,
                              textTransform: 'none',
                              fontWeight: 600,
                              bgcolor: 'transparent',
                              border: '2px solid #00467F',
                              borderColor: '#00467F',
                              color: '#00467F',
                              '&:hover': { bgcolor: 'rgba(0, 70, 127, 0.05)', border: '2px solid #00467F' }
                            }
                      }
                    >
                      {actionLoading ? 'Initializing...' : 'Verify Details'}
                    </Button>
                  </Box>
                </motion.div>
              );
            })()}

            {/* STEP 2: VENDOR SIMULATION */}
            {activeStep === 2 && (
              <motion.div
                key="step-vendor"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <Card sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}`, mb: 3 }}>
                  <CardContent sx={{ p: 4, textAlign: 'center' }}>
                    {verificationResult === null ? (
                      <>
                        <CircularProgress thickness={3} size={56} sx={{ color: 'primary.main', mb: 3 }} />
                        <Typography variant="h6" fontWeight={700} mb={1}>
                          Waiting for Document Processing
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          Session Token: <code>{transactionToken}</code>
                        </Typography>

                        <Box sx={{ border: `1px dashed ${theme.palette.primary.main}`, borderRadius: 3, p: 2.5, bgcolor: alpha(theme.palette.primary.main, 0.01), mb: 3, mt: 2 }}>
                          <Typography variant="subtitle2" fontWeight={700} color="primary" mb={1.5}>
                            ⚙️ Sandboxed SDK Simulator
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                            In production, this step initiates the Digio/Signzy iFrame client SDK. In this sandbox environment, simulate webhook actions directly:
                          </Typography>

                          <Box display="flex" gap={2} justifyContent="center">
                            <Button
                              variant="contained"
                              color="success"
                              onClick={() => handleSimulateWebhook('VERIFIED')}
                              disabled={actionLoading}
                              sx={{ textTransform: 'none', borderRadius: 2 }}
                            >
                              Simulate Pass
                            </Button>
                            <Button
                              variant="contained"
                              color="error"
                              onClick={() => handleSimulateWebhook('FAILED')}
                              disabled={actionLoading}
                              sx={{ textTransform: 'none', borderRadius: 2 }}
                            >
                              Simulate Fail
                            </Button>
                          </Box>
                        </Box>
                      </>
                    ) : verificationResult === 'SUCCESS' ? (
                      <Box>
                        <Avatar sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.main', width: 64, height: 64, mx: 'auto', mb: 2 }}>
                          <CheckCircle sx={{ fontSize: 40 }} />
                        </Avatar>
                        <Typography variant="h6" fontWeight={700} mb={1}>
                          Verification Successful!
                        </Typography>
                        <Typography variant="body2" color="text.secondary" mb={3}>
                          The vendor sandbox verified your documents, and the webhook callback was processed securely.
                        </Typography>
                        <Button
                          variant="contained"
                          color="success"
                          fullWidth
                          onClick={() => {
                            setInWorkflow(false);
                            fetchKycStatus();
                          }}
                          sx={{ textTransform: 'none', py: 1.5, borderRadius: 2.5 }}
                        >
                          Show Status Details
                        </Button>
                      </Box>
                    ) : (
                      <Box>
                        <Avatar sx={{ bgcolor: alpha(theme.palette.error.main, 0.1), color: 'error.main', width: 64, height: 64, mx: 'auto', mb: 2 }}>
                          <ErrorIcon sx={{ fontSize: 40 }} />
                        </Avatar>
                        <Typography variant="h6" fontWeight={700} mb={1}>
                          Verification Failed
                        </Typography>
                        <Typography variant="body2" color="text.secondary" mb={3}>
                          The documents could not be matched against public registries. Ensure correct inputs and try again.
                        </Typography>
                        <Button
                          variant="contained"
                          onClick={handleResetWorkflow}
                          startIcon={<Replay />}
                          fullWidth
                          sx={{ textTransform: 'none', py: 1.5, borderRadius: 2.5 }}
                        >
                          Retry Workflow
                        </Button>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </Box>
      )}
      <Dialog 
        open={signatureModalOpen} 
        onClose={cancelSignatureDrawing}
        maxWidth="xs"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 4, p: 1 }
        }}
      >
        <DialogTitle sx={{ fontWeight: 700, pb: 1 }}>Draw Your Signature</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mt: 1 }}>
            <canvas
              ref={canvasRef}
              width={400}
              height={200}
              style={{ 
                border: '1px solid #e0e0e0', 
                borderRadius: 8, 
                cursor: 'crosshair', 
                backgroundColor: '#fafafa'
              }}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
            />
            <Typography variant="caption" color="text.secondary">
              Use your mouse or touchscreen to sign inside the box.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button 
            onClick={clearSignature} 
            color="error" 
            variant="outlined"
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            Clear
          </Button>
          <Box sx={{ flexGrow: 1 }} />
          <Button 
            onClick={cancelSignatureDrawing} 
            color="inherit" 
            variant="text"
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button 
            onClick={saveSignature} 
            variant="contained" 
            sx={{ borderRadius: 2, textTransform: 'none', bgcolor: '#00467F', '&:hover': { bgcolor: '#00335c' } }}
          >
            Save Signature
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KYCVerificationFlow;
