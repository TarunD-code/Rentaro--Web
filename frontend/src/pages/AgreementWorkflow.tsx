import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, Container, Paper, Typography, Button, Stepper, Step, StepLabel,
  Divider, Alert, CircularProgress, TextField
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, Description, Draw, History } from '@mui/icons-material';

const steps = ['Agreement Generated', 'Signatures Pending', 'Fully Signed'];

// Map onboarding_service status values to stepper index
const statusToStep = (s: string): number => {
  if (!s || s === 'draft' || s === 'generated') return 0;
  if (s === 'sent_for_signing' || s === 'tenant_signed' || s === 'owner_signed') return 1;
  return 2; // fully_signed, active
};

const AgreementWorkflow: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);

  const [agreement, setAgreement] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [signName, setSignName] = useState('');
  const [signError, setSignError] = useState<string | null>(null);
  const [signSuccess, setSignSuccess] = useState(false);

  const token = localStorage.getItem('token');
  const role  = localStorage.getItem('role') || 'tenant';
  const API   = import.meta.env.VITE_API_URL;

  const fetchAgreement = async () => {
    try {
      // Read from onboarding_service — the single source of truth
      const res = await fetch(`${API}/onboarding/agreements/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) setAgreement(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAgreement(); }, [id]);

  // ── Canvas drawing helpers ──────────────────────────────────────────────
  const startDraw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setDrawing(true);
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) { ctx.beginPath(); ctx.moveTo(e.nativeEvent.offsetX, e.nativeEvent.offsetY); }
  };
  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing) return;
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) {
      ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.strokeStyle = '#0A3D62';
      ctx.lineTo(e.nativeEvent.offsetX, e.nativeEvent.offsetY);
      ctx.stroke();
    }
  };
  const stopDraw = () => setDrawing(false);
  const clearCanvas = () => {
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx && canvasRef.current) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
  };

  // ── Submit canvas signature ─────────────────────────────────────────────
  const handleSign = async () => {
    if (!signName.trim()) { setSignError('Please type your full legal name.'); return; }
    const canvas = canvasRef.current;
    if (!canvas) return;

    setSigning(true);
    setSignError(null);
    try {
      // Capture canvas as base64 PNG
      const imageB64 = canvas.toDataURL('image/png');

      const res = await fetch(`${API}/onboarding/agreements/${id}/canvas-sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          agreement_id:        Number(id),
          signer_role:         role === 'owner' ? 'owner' : 'tenant',
          signature_image_b64: imageB64,
          user_agent:          navigator.userAgent,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Signature submission failed');
      }

      setSignSuccess(true);
      await fetchAgreement(); // refresh status
    } catch (err: any) {
      setSignError(err.message);
    } finally {
      setSigning(false);
    }
  };

  if (loading) return <Box p={10} textAlign="center"><CircularProgress /></Box>;
  if (!agreement) return <Alert severity="error">Agreement not found</Alert>;

  const activeStep = statusToStep(agreement.status);

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Typography variant="h4" fontWeight={800} gutterBottom>
        Leave &amp; License Agreement
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={4}>
        11-Month Karnataka L&amp;L · Agreement #{id} · Bengaluru
      </Typography>

      <Stepper activeStep={activeStep} sx={{ my: 5 }}>
        {steps.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
      </Stepper>

      <Paper elevation={0} sx={{ p: 4, borderRadius: 6, border: '1px solid #eee' }}>
        <Box display="flex" alignItems="center" gap={2} mb={3}>
          <Description color="primary" sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h6">Agreement #{agreement.id}</Typography>
            <Typography variant="caption" color="text.secondary">
              Created {new Date(agreement.created_at).toLocaleDateString('en-IN')}
            </Typography>
          </Box>
          <Box ml="auto" textAlign="right">
            <Typography variant="body2"><strong>Rent:</strong> ₹{agreement.monthly_rent?.toLocaleString()}/mo</Typography>
            <Typography variant="body2"><strong>Deposit:</strong> ₹{agreement.security_deposit?.toLocaleString()}</Typography>
          </Box>
        </Box>

        <Alert
          severity={activeStep === 2 ? 'success' : 'info'}
          sx={{ mb: 4, borderRadius: 3 }}
        >
          Status: <strong>{(agreement.status || '').replace(/_/g, ' ').toUpperCase()}</strong>
        </Alert>

        <Box display="flex" gap={2} mb={4}>
          <Button
            variant="outlined"
            href={`${API}/onboarding/agreements/${id}/pdf`}
            target="_blank"
            startIcon={<Description />}
            sx={{ borderRadius: 3 }}
          >
            View Agreement PDF
          </Button>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* ── Canvas E-Sign Panel ─────────────────────────────────────── */}
        {activeStep < 2 && !signSuccess && (
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Draw color="primary" />
              <Typography variant="subtitle1" fontWeight={700}>
                Draw Your Signature
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Draw your signature in the box below, then type your full legal name to confirm.
              Your IP address and timestamp are recorded as an immutable audit trail.
            </Typography>

            {signError && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{signError}</Alert>}

            {/* Canvas pad */}
            <Box
              sx={{
                border: '2px dashed #c8d6e5', borderRadius: 3, mb: 2,
                bgcolor: '#fafbfc', display: 'inline-block', width: '100%',
              }}
            >
              <canvas
                ref={canvasRef}
                width={580} height={160}
                style={{ display: 'block', cursor: 'crosshair', width: '100%', height: 160 }}
                onMouseDown={startDraw}
                onMouseMove={draw}
                onMouseUp={stopDraw}
                onMouseLeave={stopDraw}
              />
            </Box>

            <Box display="flex" gap={2} alignItems="center" mb={3}>
              <TextField
                size="small"
                label="Full Legal Name"
                placeholder="Type your name to confirm"
                value={signName}
                onChange={e => setSignName(e.target.value)}
                sx={{ flex: 1, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
              <Button
                variant="text"
                size="small"
                onClick={clearCanvas}
                sx={{ color: 'text.secondary', textTransform: 'none' }}
              >
                Clear
              </Button>
            </Box>

            <Button
              variant="contained"
              onClick={handleSign}
              disabled={signing}
              startIcon={signing ? <CircularProgress size={18} /> : <Draw />}
              sx={{ borderRadius: 3, px: 4 }}
            >
              {signing ? 'Submitting…' : 'Submit Signature'}
            </Button>
          </Box>
        )}

        {/* ── Both signed ────────────────────────────────────────────── */}
        {(activeStep === 2 || signSuccess) && (
          <Box mt={2} p={3} bgcolor="#f0fdf4" borderRadius={3} display="flex" alignItems="center" gap={2}>
            <CheckCircle color="success" sx={{ fontSize: 36 }} />
            <Box>
              <Typography variant="body1" color="success.main" fontWeight={700}>
                Agreement fully executed and legally active.
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Document Hash: {agreement.document_hash}
              </Typography>
            </Box>
          </Box>
        )}
      </Paper>

      <Box mt={4} display="flex" gap={2}>
        <Button startIcon={<History />} onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
        {(activeStep === 2 || signSuccess) && (
          <Button
            variant="contained"
            onClick={() => navigate(`/payments/deposit/${agreement.id}`)}
            sx={{ borderRadius: 3 }}
          >
            Proceed to Deposit Payment →
          </Button>
        )}
      </Box>
    </Container>
  );
};

export default AgreementWorkflow;
