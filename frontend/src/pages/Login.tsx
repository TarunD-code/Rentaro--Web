import React, { useState } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  Link as MuiLink,
  useTheme,
  alpha,
  Alert,
  CircularProgress,
  ToggleButton,
  ToggleButtonGroup
} from '@mui/material';
import { 
  AccountCircle, 
  Lock,
  Login as LoginIcon,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import { useNavigate, Link } from 'react-router-dom';
import { InputAdornment, IconButton } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

const Login: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const [formData, setFormData] = useState({
    email_or_phone: '',
    password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error('Server returned an invalid response');
      }

      if (!response.ok) {
        const errorDetail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        if (errorDetail === "User is not verified") {
           sessionStorage.setItem('identifier', formData.email_or_phone);
           navigate('/verify');
           return;
        }
        throw new Error(errorDetail || 'Login failed');
      }
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('role', data.role); // Save role for dashboard logic
      navigate('/dashboard');
    } catch (err: any) {
      if (err.message === 'Failed to fetch') {
        setError('Connection failed. Please check if the API Gateway is running on port 8000.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

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
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <Card 
          sx={{ 
            maxWidth: 440, 
            width: '100%', 
            borderRadius: 6,
            boxShadow: '0 25px 50px -12px rgba(0,0,0,1.5)',
            bgcolor: alpha(theme.palette?.background?.paper || '#FFFFFF', 0.9),
            backdropFilter: 'blur(20px)',
            border: `1px solid ${theme.palette?.divider || 'rgba(0,0,0,0.1)'}`,
            p: 2
          }}
        >
          <CardContent>
            <Box textAlign="center" mb={4}>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
                {t('login')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('subtitle')}
              </Typography>
            </Box>

            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <TextField
                  name="email_or_phone"
                  label={t('email_phone')}
                  type="text"
                  required
                  value={formData.email_or_phone}
                  onChange={handleChange}
                  InputProps={{
                    startAdornment: <AccountCircle sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />,
                  }}
                />
                <TextField
                  name="password"
                  label={t('password')}
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  InputProps={{
                    startAdornment: <Lock sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />,
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={() => setShowPassword(!showPassword)}
                          onMouseDown={(e) => e.preventDefault()}
                          edge="end"
                          size="small"
                        >
                          {showPassword ? <VisibilityOff sx={{ fontSize: 18 }} /> : <Visibility sx={{ fontSize: 18 }} />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
                <Button 
                  type="submit" 
                  variant="contained" 
                  size="large" 
                  fullWidth
                  disabled={loading}
                  endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
                  sx={{ mt: 1, height: 52 }}
                >
                  {t('login')}
                </Button>
              </Box>
            </form>

            <Box textAlign="center" mt={4}>
              <Typography variant="body2" color="text.secondary">
                {t('dont_have_account')}{' '}
                <MuiLink component={Link} to="/register" sx={{ fontWeight: 600, color: 'primary.main', textDecoration: 'none' }}>
                  {t('signup')}
                </MuiLink>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default Login;
