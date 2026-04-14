import React, { useState } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  ToggleButton, 
  ToggleButtonGroup,
  Link as MuiLink,
  useTheme,
  alpha,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  Person as TenantIcon, 
  HomeWork as OwnerIcon, 
  AccountCircle, 
  Lock, 
  ArrowForward,
  CheckCircleOutline,
  AdminPanelSettings
} from '@mui/icons-material';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

const Register: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const [formData, setFormData] = useState({
    email_or_phone: '',
    password: '',
    role: 'tenant'
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleChange = (_: React.MouseEvent<HTMLElement>, newRole: string | null) => {
    if (newRole) {
      setFormData({ ...formData, role: newRole });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/signup`, {
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
        throw new Error(errorDetail || 'Registration failed');
      }
      
      sessionStorage.setItem('identifier', formData.email_or_phone);
      setSuccess(true);
      setTimeout(() => navigate('/verify'), 2000);
    } catch (err: any) {
      setError(err.message);
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
            bgcolor: 'background.paper',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${theme.palette?.divider || 'rgba(0,0,0,0.1)'}`,
            p: 2
          }}
        >
          <CardContent>
            <Box textAlign="center" mb={4}>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
                {t('register_title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('register_subtitle')}
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
                  <CheckCircleOutline color="success" sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6" gutterBottom>Registration Successful!</Typography>
                  <Typography variant="body2" color="text.secondary" mb={3}>
                    Redirecting to verification...
                  </Typography>
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
                    <Box mb={4}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Select your role
                      </Typography>
                      <ToggleButtonGroup
                        value={formData.role}
                        exclusive
                        onChange={handleRoleChange}
                        fullWidth
                        sx={{ 
                          gap: 2, 
                          '& .MuiToggleButtonGroup-grouped': { 
                            border: `1px solid ${theme.palette?.divider || 'rgba(0,0,0,0.1)'}`,
                            borderRadius: 2,
                            px: 3,
                            py: 1.5,
                            flex: 1,
                            transition: 'all 0.3s ease',
                            '&.Mui-selected': {
                              bgcolor: alpha(theme.palette?.primary?.main || '#0A3D62', 0.1),
                              color: 'primary.main',
                              borderColor: 'primary.main',
                              borderWidth: 2,
                              '&:hover': {
                                bgcolor: alpha(theme.palette?.primary?.main || '#0A3D62', 0.2),
                              }
                            }
                          } 
                        }}
                      >
                        <ToggleButton value="tenant">
                          <Box display="flex" flexDirection="column" alignItems="center">
                            <TenantIcon sx={{ mb: 0.5, fontSize: 24 }} />
                            <Typography variant="caption" fontWeight={600}>{t('role_tenant')}</Typography>
                          </Box>
                        </ToggleButton>
                        <ToggleButton value="owner">
                          <Box display="flex" flexDirection="column" alignItems="center">
                            <OwnerIcon sx={{ mb: 0.5, fontSize: 24 }} />
                            <Typography variant="caption" fontWeight={600}>{t('role_owner')}</Typography>
                          </Box>
                        </ToggleButton>
                        <ToggleButton value="admin">
                          <Box display="flex" flexDirection="column" alignItems="center">
                            <AdminPanelSettings sx={{ mb: 0.5, fontSize: 24 }} />
                            <Typography variant="caption" fontWeight={600}>Admin</Typography>
                          </Box>
                        </ToggleButton>
                      </ToggleButtonGroup>
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                      <TextField
                        name="email_or_phone"
                        label={t('email_phone')}
                        type="text"
                        required
                        fullWidth
                        value={formData.email_or_phone}
                        onChange={handleChange}
                        InputProps={{
                          startAdornment: <AccountCircle sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />,
                        }}
                      />
                      <TextField
                        name="password"
                        label={t('password')}
                        type="password"
                        required
                        fullWidth
                        value={formData.password}
                        onChange={handleChange}
                        InputProps={{
                          startAdornment: <Lock sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />,
                        }}
                      />
                      <Button 
                        type="submit" 
                        variant="contained" 
                        size="large" 
                        fullWidth
                        disabled={loading}
                        endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowForward />}
                        sx={{ mt: 2, height: 52 }}
                      >
                        {t('signup')}
                      </Button>
                    </Box>
                  </form>
                </motion.div>
              )}
            </AnimatePresence>

            {!success && (
              <Box textAlign="center" mt={4}>
                <Typography variant="body2" color="text.secondary">
                  {t('already_have_account')}{' '}
                  <MuiLink component={Link} to="/login" sx={{ fontWeight: 600, color: 'primary.main', textDecoration: 'none' }}>
                    {t('login')}
                  </MuiLink>
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default Register;
