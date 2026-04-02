import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  TextField, 
  Button, 
  useTheme, 
  alpha, 
  Stepper, 
  Step, 
  StepLabel,
  InputAdornment,
  IconButton,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  ArrowBack, 
  CheckCircle,
  CloudUpload,
  Home
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import React, { useRef } from 'react';

const CreateProperty: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    title: '',
    price: '',
    address: '',
    amenities: '',
    description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = ['Basic Information', 'Financials & Amenities', 'Media & Confirm'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/property/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(formData),
      });
      
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error('Server returned an invalid response');
      }

      if (!response.ok) {
        const detail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail;
        throw new Error(detail || 'Posting failed');
      }

      const propertyId = data.id;

      // Upload files if any
      if (selectedFiles.length > 0) {
        for (const file of selectedFiles) {
          const fileFormData = new FormData();
          fileFormData.append('file', file);
          
          const uploadResp = await fetch(`${import.meta.env.VITE_API_URL}/property/${propertyId}/upload-media`, {
            method: 'POST',
            headers: { 
              'Authorization': `Bearer ${token}` 
            },
            body: fileFormData,
          });

          if (!uploadResp.ok) {
            console.error(`Failed to upload ${file.name}`);
          }
        }
      }

      setSuccess(true);
      setTimeout(() => navigate('/listings'), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <TextField 
              name="title" 
              label="Property Title" 
              placeholder="e.g. Modern Studio in South Mumbai"
              value={formData.title} 
              onChange={handleChange}
              fullWidth
              InputProps={{
                startAdornment: <Home sx={{ color: 'text.secondary', mr: 1 }} />,
              }}
            />
            <TextField 
              name="address" 
              label="Full Address" 
              placeholder="e.g. 123 Flat, Bandra West"
              value={formData.address} 
              onChange={handleChange}
              fullWidth
            />
            <TextField 
              name="description" 
              label="Detailed Description" 
              placeholder="Tell tenants about your property..."
              multiline 
              rows={4} 
              value={formData.description} 
              onChange={handleChange}
              fullWidth
            />
          </Box>
        );
      case 1:
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <TextField 
              name="price" 
              label="Monthly Rent" 
              type="number"
              value={formData.price} 
              onChange={handleChange}
              fullWidth
              InputProps={{
                startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                endAdornment: <Typography variant="caption">/mo</Typography>
              }}
            />
            <TextField 
              name="amenities" 
              label="Amenities" 
              placeholder="Pool, Gym, Parking, WiFi..."
              helperText="Separate multiple with commas"
              value={formData.amenities} 
              onChange={handleChange}
              fullWidth
            />
          </Box>
        );
      case 2:
        return (
          <Box textAlign="center" py={4}>
            <Box 
              sx={{ 
                p: 5, 
                border: `2px dashed ${theme.palette.divider}`, 
                borderRadius: 4,
                bgcolor: alpha(theme.palette.primary.main, 0.02),
                mb: 4,
                position: 'relative'
              }}
              onClick={() => fileInputRef.current?.click()}
              style={{ cursor: 'pointer' }}
            >
              <input 
                type="file" 
                multiple 
                hidden 
                ref={fileInputRef} 
                onChange={handleFileChange}
                accept="image/*"
              />
              <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" fontWeight={700}>Upload Property Photos</Typography>
              <Typography variant="body2" color="text.secondary">Add high-quality photos for 3x better conversions.</Typography>
              <Button size="small" variant="contained" sx={{ mt: 2 }}>
                {selectedFiles.length > 0 ? `${selectedFiles.length} files selected` : 'Select Images'}
              </Button>
              {selectedFiles.length > 0 && (
                <Box mt={2} display="flex" flexWrap="wrap" gap={1} justifyContent="center">
                  {selectedFiles.map((f, i) => (
                    <Typography key={i} variant="caption" sx={{ p: 0.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                      {f.name}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
            <Alert severity="info">Review your details before publishing. Listing will be live immediately.</Alert>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ py: 2 }}>
      <Box display="flex" alignItems="center" gap={3} mb={5}>
        <IconButton onClick={() => navigate('/dashboard')} sx={{ bgcolor: alpha(theme.palette.text.primary, 0.05) }}>
          <ArrowBack fontSize="small" />
        </IconButton>
        <Typography variant="h4" fontWeight={700}>Post New Listing</Typography>
      </Box>

      <Card 
        sx={{ 
          maxWidth: 700, 
          width: '100%', 
          mx: 'auto', 
          borderRadius: 6,
          boxShadow: '0 20px 40px -10px rgba(0,0,0,0.2)',
          bgcolor: alpha(theme.palette.background.paper, 0.6),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${theme.palette.divider}`,
          p: { xs: 2, sm: 4 }
        }}
      >
        <CardContent>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 6 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          <AnimatePresence mode="wait">
            {success ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{ textAlign: 'center', padding: '40px 0' }}
              >
                <CheckCircle sx={{ color: 'success.main', fontSize: 80, mb: 2 }} />
                <Typography variant="h5" fontWeight={700}>Success!</Typography>
                <Typography color="text.secondary">Your property has been listed on Rentora.</Typography>
              </motion.div>
            ) : (
              <motion.div
                key={activeStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
                
                {renderStepContent(activeStep)}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 6 }}>
                  <Button 
                    disabled={activeStep === 0 || loading} 
                    onClick={handleBack}
                    sx={{ fontWeight: 600 }}
                  >
                    Back
                  </Button>
                  {activeStep === steps.length - 1 ? (
                    <Button 
                      variant="contained" 
                      color="primary" 
                      onClick={handleSubmit}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
                      sx={{ borderRadius: 3, px: 4, height: 48 }}
                    >
                      Publish Listing
                    </Button>
                  ) : (
                    <Button 
                      variant="contained" 
                      onClick={handleNext}
                      disabled={!formData.title && activeStep === 0}
                      sx={{ borderRadius: 3, px: 4, height: 48 }}
                    >
                      Next Step
                    </Button>
                  )}
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CreateProperty;
