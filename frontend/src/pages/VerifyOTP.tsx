import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  useTheme,
  alpha,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  PhonelinkLock, 
  ArrowForward, 
  Refresh 
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

const VerifyOTP: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const [otp, setOtp] = useState('');
  const [identifier, setIdentifier] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    const id = sessionStorage.getItem('identifier');
    if (!id) {
      navigate('/register');
    } else {
      setIdentifier(id);
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_or_phone: identifier, otp: otp }),
      });
      
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error('Server returned an invalid response');
      }

      if (!response.ok) {
        const errorDetail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        throw new Error(errorDetail || 'Verification failed');
      }
      
      localStorage.setItem('token', data.access_token);
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError(null);
    // Add resend logic here
    setTimeout(() => {
      setResending(false);
      // alert('OTP Resent! (Mock)');
    }, 1500);
  };

  if (!identifier) return null;

  return (
    <Box 
      sx={{ 
        minHeight: '80vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: 'transparent'
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <Card 
          sx={{ 
            maxWidth: 440, 
            width: '100%', 
            borderRadius: 6,
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
            bgcolor: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(20px)',
            border: `1px solid ${theme.palette.divider}`,
            p: 2
          }}
        >
          <CardContent>
            <Box textAlign="center" mb={4}>
              <Box 
                sx={{ 
                  width: 64, 
                  height: 64, 
                  borderRadius: '50%', 
                  background: 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                  color: 'primary.main'
                }}
              >
                <PhonelinkLock fontSize="large" />
              </Box>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
                {t('verify_otp')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('otp_sent')} to <strong>{identifier}</strong>
              </Typography>
            </Box>

            <AnimatePresence mode="wait">
              {success ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{ textAlign: 'center', padding: '20px 0' }}
                >
                  <Alert severity="success" sx={{ mb: 2 }}>Verification Successful! Redirecting...</Alert>
                  <CircularProgress size={24} />
                </motion.div>
              ) : (
                <motion.div key="form">
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                    >
                      <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
                    </motion.div>
                  )}
                  <form onSubmit={handleSubmit}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <TextField
                        name="otp"
                        label="OTP Code"
                        type="text"
                        required
                        fullWidth
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        inputProps={{ 
                          maxLength: 6, 
                          style: { textAlign: 'center', fontSize: '1.5rem', letterSpacing: '8px', fontWeight: 700 } 
                        }}
                        autoFocus
                      />
                      
                      <Button 
                        type="submit" 
                        variant="contained" 
                        size="large" 
                        fullWidth
                        disabled={loading || otp.length < 6}
                        endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowForward />}
                        sx={{ height: 52 }}
                      >
                        {t('verify_btn')}
                      </Button>

                      <Button 
                        variant="text" 
                        onClick={handleResend}
                        disabled={resending}
                        startIcon={resending ? <CircularProgress size={16} color="inherit" /> : <Refresh />}
                        sx={{ fontWeight: 600 }}
                      >
                        Resend OTP
                      </Button>
                    </Box>
                  </form>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default VerifyOTP;
