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
  CircularProgress,
  Checkbox,
  FormControlLabel,
  FormGroup
} from '@mui/material';
import { 
  ArrowBack,
  CheckCircle,
  Home
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import React from 'react';
import Upload from '../components/Upload';

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
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [otherAmenity, setOtherAmenity] = useState('');
  const role = localStorage.getItem('role');

  const steps = ['Basic Information', 'Financials & Amenities', 'Media & Confirm'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const finalAmenities = [...selectedAmenities];
      if (otherAmenity) finalAmenities.push(otherAmenity);
      
      const payload = {
        ...formData,
        amenities: finalAmenities.join(', ')
      };

      const response = await fetch(`${import.meta.env.VITE_API_URL}/property/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(payload),
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
            <Box>
              <Typography variant="subtitle2" fontWeight={700} mb={1.5}>Amenities</Typography>
              <FormGroup row>
                {['Pool', 'Gym', 'Parking', 'CCTV', 'Generator', 'Lift', 'Garden'].map((amt) => (
                  <FormControlLabel 
                    key={amt}
                    control={
                      <Checkbox 
                        checked={selectedAmenities.includes(amt)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedAmenities([...selectedAmenities, amt]);
                          else setSelectedAmenities(selectedAmenities.filter(a => a !== amt));
                        }}
                      />
                    }
                    label={amt}
                  />
                ))}
              </FormGroup>
              <TextField 
                name="other" 
                label="Other Amenities" 
                placeholder="e.g. Roof deck, Cinema Room"
                value={otherAmenity} 
                onChange={(e) => setOtherAmenity(e.target.value)}
                fullWidth
                sx={{ mt: 2 }}
              />
            </Box>
          </Box>
        );
      case 2:
        return (
          <Box textAlign="center" py={4}>
            <Upload onFilesSelected={setSelectedFiles} />
            <Alert severity="info" sx={{ mt: 2 }}>Review your details before publishing. Listing will be live immediately.</Alert>
          </Box>
        );
      default:
        return null;
    }
  };

  if (role === 'tenant') {
    return (
      <Box sx={{ py: 10, px: 2 }}>
        <Card sx={{ maxWidth: 500, mx: 'auto', p: 4, textAlign: 'center', borderRadius: 4 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            Tenants are not authorized to post new listings. Please register as an Owner or Admin to access this feature.
          </Alert>
          <Button variant="outlined" onClick={() => navigate('/dashboard')}>Return to Dashboard</Button>
        </Card>
      </Box>
    );
  }

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
