import React, { useState } from 'react';
import { 
  Box, Container, Typography, Stepper, Step, StepLabel, 
  Button, TextField, Paper, Grid, Divider, Alert, 
  CircularProgress, MenuItem, Checkbox, FormControlLabel,
  useTheme, alpha, Card, CardContent
} from '@mui/material';
import { 
  ArrowBack, ArrowForward, Article, Home, Person, 
  PeopleAlt, Summarize, CheckCircle, AssignmentTurnedIn, Draw 
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const steps = [
  'Contract Details', 
  'Property Details', 
  'Landlord Details', 
  'Tenant Details', 
  'Summary & Sign'
];

const PRE_BAKED_CLAUSES = [
  { id: 'painting', title: 'Painting Charges', text: 'Tenant agrees to pay one month\'s rent or a fixed ₹15,000 as painting charges upon vacating the premises.' },
  { id: 'electricity_water', title: 'Electricity & Water Rules', text: 'Tenant shall pay electricity and water bills directly to the respective authorities based on monthly meter readings.' },
  { id: 'pets', title: 'Pet Policies', text: 'Pets are permitted on the property, provided they do not cause nuisance to neighbors and any pet-related structural damage is repaired by the tenant.' },
  { id: 'late_fee', title: 'Late Rent Penalty', text: 'A late fee of 5% of monthly rent shall apply for rent payments received after the 5th of any month.' },
  { id: 'subletting', title: 'Subletting Restrictions', text: 'Subletting of the premises by the tenant is strictly prohibited without the landlord\'s explicit written consent.' }
];

const AgreementBuilder: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    // Step 1: Contract Details
    propertyLocation: '',
    securityDeposit: '',
    monthlyRent: '',
    timeframeMonths: 11, // 6 or 11
    maintenanceExclusion: 'Major structural repairs only. Minor day-to-day repairs under ₹1,000 to be borne by the tenant.',

    // Step 2: Property Details
    buildingCategory: 'Apartment', // Independent House, Apartment, Commercial Shop
    floorIndex: 0,
    buildingTags: 'Gated Community, Power Backup, Elevator',
    structuralDetails: '2 BHK, 2 Baths, Semi-furnished with cupboards and modular kitchen',

    // Step 3: Landlord Details
    landlordName: '',
    landlordAge: '',
    landlordGender: 'Male',
    landlordContact: '',
    landlordAddress: '',
    landlordTaxId: '', // PAN number

    // Step 4: Tenant Details
    tenantName: '',
    tenantAge: '',
    tenantGender: 'Male',
    tenantContact: '',
    tenantAddress: '',
    tenantTaxId: '', // PAN/Aadhaar

    // Step 5: Clauses & Confirmation
    selectedClauses: ['painting', 'electricity_water', 'pets'] as string[],
    signatureConfirmed: false,
    signatureName: ''
  });

  const handleNext = () => {
    if (validateCurrentStep()) {
      setActiveStep((prev) => prev + 1);
    }
  };
  
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const validateCurrentStep = () => {
    setError(null);
    if (activeStep === 0) {
      if (!formData.propertyLocation.trim()) { setError('Property Location is required.'); return false; }
      if (!formData.monthlyRent || Number(formData.monthlyRent) <= 0) { setError('Monthly rent must be a positive number.'); return false; }
      if (!formData.securityDeposit || Number(formData.securityDeposit) <= 0) { setError('Security deposit must be a positive number.'); return false; }
    }
    if (activeStep === 1) {
      if (formData.floorIndex < 0) { setError('Floor index cannot be negative.'); return false; }
    }
    if (activeStep === 2) {
      if (!formData.landlordName.trim()) { setError('Landlord full legal name is required.'); return false; }
      if (!formData.landlordContact.trim()) { setError('Landlord contact number is required.'); return false; }
      if (!formData.landlordAddress.trim()) { setError('Landlord permanent address is required.'); return false; }
      if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(formData.landlordTaxId.toUpperCase().trim())) {
        setError('Please enter a valid 10-character Landlord PAN (e.g. ABCDE1234F).');
        return false;
      }
    }
    if (activeStep === 3) {
      if (!formData.tenantName.trim()) { setError('Tenant full legal name is required.'); return false; }
      if (!formData.tenantContact.trim()) { setError('Tenant contact number is required.'); return false; }
      if (!formData.tenantAddress.trim()) { setError('Tenant permanent address is required.'); return false; }
      if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(formData.tenantTaxId.toUpperCase().trim())) {
        setError('Please enter a valid 10-character Tenant PAN (e.g. ABCDE1234F).');
        return false;
      }
    }
    return true;
  };

  const handleClauseToggle = (clauseId: string) => {
    setFormData(prev => {
      const alreadySelected = prev.selectedClauses.includes(clauseId);
      const updated = alreadySelected
        ? prev.selectedClauses.filter(id => id !== clauseId)
        : [...prev.selectedClauses, clauseId];
      return { ...prev, selectedClauses: updated };
    });
  };

  // Estimate expenses
  const baseStampDuty = 500;
  const portalDraftingFee = 150;
  const totalDraftingExpense = baseStampDuty + portalDraftingFee;

  const handleGenerate = async () => {
    if (!formData.signatureConfirmed || !formData.signatureName.trim()) {
      setError('Please sign/confirm to generate the rental agreement.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const userEmail = localStorage.getItem('email') || '';
      const userRole  = localStorage.getItem('role')  || '';

      // Resolve owner vs tenant from local session
      const ownerId  = userRole === 'owner'  ? userEmail : formData.landlordContact;
      const tenantId = userRole === 'tenant' ? userEmail : formData.tenantContact;

      // Build custom terms JSON for the Karnataka L&L template
      const customClauses = PRE_BAKED_CLAUSES
        .filter(c => formData.selectedClauses.includes(c.id))
        .map(c => ({ title: c.title, text: c.text }));
      if (formData.maintenanceExclusion.trim()) {
        customClauses.push({ title: 'Maintenance Exclusions', text: formData.maintenanceExclusion });
      }

      // Compute 11-month end date from today
      const startDate = new Date();
      const endDate   = new Date(startDate);
      endDate.setMonth(endDate.getMonth() + formData.timeframeMonths);
      const fmtDate = (d: Date) => d.toISOString().split('T')[0];

      // ── POST to onboarding_service — the single canonical agreement store ──
      const res = await fetch(`${import.meta.env.VITE_API_URL}/onboarding/agreements/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          property_id:       1, // TODO: pass real property_id via router state
          owner_id:          ownerId,
          tenant_id:         tenantId,
          start_date:        fmtDate(startDate),
          end_date:          fmtDate(endDate),
          monthly_rent:      parseFloat(formData.monthlyRent),
          security_deposit:  parseFloat(formData.securityDeposit),
          notice_period_days: 60,  // Bengaluru standard: 2 months
          terms_json: JSON.stringify(customClauses),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to generate agreement (${res.status})`);
      }

      const agreement = await res.json();

      // ── Submit the canvas/name signature immediately ─────────────────────
      // Signature is the typed name seal encoded as a minimal data-URI
      const sigPayload = btoa(`Signed by: ${formData.signatureName} | ${new Date().toISOString()}`);
      await fetch(`${import.meta.env.VITE_API_URL}/onboarding/agreements/${agreement.id}/canvas-sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          agreement_id:        agreement.id,
          signer_role:         userRole === 'owner' ? 'owner' : 'tenant',
          signature_image_b64: sigPayload,
          user_agent:          navigator.userAgent,
        }),
      });

      // ── Chain into Deposit Payment ───────────────────────────────────────
      navigate(`/payments/deposit/${agreement.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Title */}
      <Box sx={{ mb: 5 }}>
        <Typography variant="h4" fontWeight={900} letterSpacing={-1.2} mb={1}>
          Rental Agreement Wizard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Draft legally compliant, premium, digital rental agreements with custom clauses, landlord & tenant profiles, and real-time clause picking.
        </Typography>
      </Box>

      {/* Stepper */}
      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 6 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Main Form Box */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: { xs: 3, md: 5 }, 
          borderRadius: 6, 
          border: `1px solid ${theme.palette.divider}`,
          bgcolor: alpha(theme.palette.background.paper, 0.9),
          backdropFilter: 'blur(10px)',
          boxShadow: '0 20px 40px -15px rgba(0,0,0,0.05)'
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 4, borderRadius: 2.5 }}>
            {error}
          </Alert>
        )}

        <AnimatePresence mode="wait">
          {/* STEP 1: CONTRACT DETAILS */}
          {activeStep === 0 && (
            <motion.div key="step-1" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }}>
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <Article color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" fontWeight={800}>1. Contract Details</Typography>
              </Box>
              <Divider sx={{ mb: 4 }} />
              <Grid container spacing={3}>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    label="Property Location Address *" 
                    placeholder="Enter complete location details"
                    value={formData.propertyLocation} 
                    onChange={(e) => setFormData({...formData, propertyLocation: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Monthly Rent (INR) *" 
                    type="number"
                    placeholder="e.g. 25000"
                    value={formData.monthlyRent} 
                    onChange={(e) => setFormData({...formData, monthlyRent: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Refundable Security Deposit (INR) *" 
                    type="number"
                    placeholder="e.g. 100000"
                    value={formData.securityDeposit} 
                    onChange={(e) => setFormData({...formData, securityDeposit: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    select 
                    fullWidth 
                    label="Agreement Timeframe (Months) *" 
                    value={formData.timeframeMonths} 
                    onChange={(e) => setFormData({...formData, timeframeMonths: Number(e.target.value)})}
                  >
                    <MenuItem value={6}>6 Months</MenuItem>
                    <MenuItem value={11}>11 Months</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    multiline 
                    rows={3} 
                    label="Maintenance Exclusions & Repairs *" 
                    placeholder="Specify maintenance terms..."
                    value={formData.maintenanceExclusion} 
                    onChange={(e) => setFormData({...formData, maintenanceExclusion: e.target.value})}
                  />
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 2: PROPERTY DETAILS */}
          {activeStep === 1 && (
            <motion.div key="step-2" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }}>
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <Home color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" fontWeight={800}>2. Property Details</Typography>
              </Box>
              <Divider sx={{ mb: 4 }} />
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    select 
                    fullWidth 
                    label="Building Category *" 
                    value={formData.buildingCategory} 
                    onChange={(e) => setFormData({...formData, buildingCategory: e.target.value})}
                  >
                    <MenuItem value="Independent House">Independent House</MenuItem>
                    <MenuItem value="Apartment">Apartment</MenuItem>
                    <MenuItem value="Commercial Shop">Commercial Shop</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Floor Index *" 
                    type="number"
                    value={formData.floorIndex} 
                    onChange={(e) => setFormData({...formData, floorIndex: Number(e.target.value)})}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    label="Building Tags (Comma Separated)" 
                    placeholder="e.g. Semi-Furnished, Gated Society, Parking Included"
                    value={formData.buildingTags} 
                    onChange={(e) => setFormData({...formData, buildingTags: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    multiline 
                    rows={3} 
                    label="Structural Details & Amenities Included" 
                    placeholder="Describe rooms, furniture, power-backups, modular kitchen details..."
                    value={formData.structuralDetails} 
                    onChange={(e) => setFormData({...formData, structuralDetails: e.target.value})}
                  />
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 3: LANDLORD DETAILS */}
          {activeStep === 2 && (
            <motion.div key="step-3" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }}>
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <Person color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" fontWeight={800}>3. Landlord Details</Typography>
              </Box>
              <Divider sx={{ mb: 4 }} />
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 8 }}>
                  <TextField 
                    fullWidth 
                    label="Full Legal Name *" 
                    placeholder="Enter Landlord's official name"
                    value={formData.landlordName} 
                    onChange={(e) => setFormData({...formData, landlordName: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <TextField 
                    fullWidth 
                    label="Age *" 
                    type="number"
                    value={formData.landlordAge} 
                    onChange={(e) => setFormData({...formData, landlordAge: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    select 
                    fullWidth 
                    label="Gender *" 
                    value={formData.landlordGender} 
                    onChange={(e) => setFormData({...formData, landlordGender: e.target.value})}
                  >
                    <MenuItem value="Male">Male</MenuItem>
                    <MenuItem value="Female">Female</MenuItem>
                    <MenuItem value="Other">Other</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Contact Phone Number *" 
                    placeholder="Enter 10-digit mobile number"
                    value={formData.landlordContact} 
                    onChange={(e) => setFormData({...formData, landlordContact: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Tax ID (PAN Number) *" 
                    placeholder="ABCDE1234F"
                    inputProps={{ style: { textTransform: 'uppercase' } }}
                    value={formData.landlordTaxId} 
                    onChange={(e) => setFormData({...formData, landlordTaxId: e.target.value.toUpperCase()})}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    multiline 
                    rows={2.5} 
                    label="Permanent Registration Address *" 
                    placeholder="Enter Landlord's permanent legal address"
                    value={formData.landlordAddress} 
                    onChange={(e) => setFormData({...formData, landlordAddress: e.target.value})}
                  />
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 4: TENANT DETAILS */}
          {activeStep === 3 && (
            <motion.div key="step-4" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }}>
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <PeopleAlt color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" fontWeight={800}>4. Tenant Details</Typography>
              </Box>
              <Divider sx={{ mb: 4 }} />
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 8 }}>
                  <TextField 
                    fullWidth 
                    label="Full Legal Name *" 
                    placeholder="Enter Tenant's official name"
                    value={formData.tenantName} 
                    onChange={(e) => setFormData({...formData, tenantName: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <TextField 
                    fullWidth 
                    label="Age *" 
                    type="number"
                    value={formData.tenantAge} 
                    onChange={(e) => setFormData({...formData, tenantAge: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    select 
                    fullWidth 
                    label="Gender *" 
                    value={formData.tenantGender} 
                    onChange={(e) => setFormData({...formData, tenantGender: e.target.value})}
                  >
                    <MenuItem value="Male">Male</MenuItem>
                    <MenuItem value="Female">Female</MenuItem>
                    <MenuItem value="Other">Other</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Contact Phone Number *" 
                    placeholder="Enter 10-digit mobile number"
                    value={formData.tenantContact} 
                    onChange={(e) => setFormData({...formData, tenantContact: e.target.value})}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField 
                    fullWidth 
                    label="Tax ID (PAN Number) *" 
                    placeholder="ABCDE1234F"
                    inputProps={{ style: { textTransform: 'uppercase' } }}
                    value={formData.tenantTaxId} 
                    onChange={(e) => setFormData({...formData, tenantTaxId: e.target.value.toUpperCase()})}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField 
                    fullWidth 
                    multiline 
                    rows={2.5} 
                    label="Permanent Registration Address *" 
                    placeholder="Enter Tenant's permanent legal address"
                    value={formData.tenantAddress} 
                    onChange={(e) => setFormData({...formData, tenantAddress: e.target.value})}
                  />
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 5: SUMMARY & SELECTION PANEL */}
          {activeStep === 4 && (
            <motion.div key="step-5" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }}>
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <Summarize color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" fontWeight={800}>5. Summary & Confirmation</Typography>
              </Box>
              <Divider sx={{ mb: 4 }} />
              
              <Grid container spacing={4}>
                {/* Contract Summary Column */}
                <Grid size={{ xs: 12, md: 6 }}>
                  <Card sx={{ borderRadius: 4, mb: 3, border: `1px solid ${theme.palette.divider}`, bgcolor: alpha(theme.palette.background.default, 0.4) }}>
                    <CardContent sx={{ p: 3 }}>
                      <Typography variant="subtitle2" fontWeight={800} color="primary" mb={2}>Agreement Summary</Typography>
                      <Grid container spacing={2}>
                        <Grid size={{ xs: 12 }}>
                          <Typography variant="caption" color="text.secondary">LOCATION</Typography>
                          <Typography variant="body2" fontWeight={700}>{formData.propertyLocation}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">MONTHLY RENT</Typography>
                          <Typography variant="body2" fontWeight={700}>₹{Number(formData.monthlyRent).toLocaleString()}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">SECURITY DEPOSIT</Typography>
                          <Typography variant="body2" fontWeight={700}>₹{Number(formData.securityDeposit).toLocaleString()}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">TIMEFRAME</Typography>
                          <Typography variant="body2" fontWeight={700}>{formData.timeframeMonths} Months</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">PROPERTY CATEGORY</Typography>
                          <Typography variant="body2" fontWeight={700}>{formData.buildingCategory} (Floor: {formData.floorIndex})</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">LANDLORD (PAN)</Typography>
                          <Typography variant="body2" fontWeight={700}>{formData.landlordName} ({formData.landlordTaxId.substring(0,5)}XXXXX)</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary">TENANT (PAN)</Typography>
                          <Typography variant="body2" fontWeight={700}>{formData.tenantName} ({formData.tenantTaxId.substring(0,5)}XXXXX)</Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>

                  {/* Estimation Card */}
                  <Card sx={{ borderRadius: 4, border: `1px dashed ${theme.palette.success.main}`, bgcolor: alpha(theme.palette.success.main, 0.02) }}>
                    <CardContent sx={{ p: 3 }}>
                      <Typography variant="subtitle2" fontWeight={800} color="success.main" mb={2} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CheckCircle sx={{ fontSize: 18 }} /> Estimated Drafting Expenses
                      </Typography>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">Base Stamp Duty:</Typography>
                        <Typography variant="body2" fontWeight={700}>₹{baseStampDuty}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between" mb={1.5}>
                        <Typography variant="body2">Portal Drafting Fee:</Typography>
                        <Typography variant="body2" fontWeight={700}>₹{portalDraftingFee}</Typography>
                      </Box>
                      <Divider sx={{ mb: 1.5 }} />
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body1" fontWeight={800}>Total Expenses:</Typography>
                        <Typography variant="body1" fontWeight={900} color="success.main">₹{totalDraftingExpense}</Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Real-time Clause Picker and Signature Column */}
                <Grid size={{ xs: 12, md: 6 }}>
                  {/* Clause Picker */}
                  <Typography variant="subtitle2" fontWeight={800} mb={2}>Select Included Clauses</Typography>
                  <Box display="flex" flexDirection="column" gap={2} mb={4}>
                    {PRE_BAKED_CLAUSES.map((clause) => {
                      const isSelected = formData.selectedClauses.includes(clause.id);
                      return (
                        <Box 
                          key={clause.id}
                          onClick={() => handleClauseToggle(clause.id)}
                          sx={{ 
                            border: `1.5px solid ${isSelected ? theme.palette.primary.main : theme.palette.divider}`, 
                            borderRadius: 3.5, 
                            p: 2, 
                            cursor: 'pointer',
                            bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.02) : 'transparent',
                            transition: 'all 0.2s',
                            '&:hover': {
                              borderColor: theme.palette.primary.main
                            }
                          }}
                        >
                          <Box display="flex" justify-content="space-between" alignItems="center" mb={0.5}>
                            <Typography variant="subtitle2" fontWeight={700} color={isSelected ? "primary.main" : "text.primary"}>
                              {clause.title}
                            </Typography>
                            <Checkbox checked={isSelected} size="small" sx={{ p: 0, ml: 'auto' }} />
                          </Box>
                          <Typography variant="caption" color="text.secondary" display="block">
                            {clause.text}
                          </Typography>
                        </Box>
                      );
                    })}
                  </Box>

                  {/* Signature Confirmation */}
                  <Typography variant="subtitle2" fontWeight={800} mb={2}>Signature Confirmation</Typography>
                  <Box sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 4, p: 3, bgcolor: 'background.default' }}>
                    <Box display="flex" alignItems="center" gap={1.5} mb={2.5}>
                      <Draw color="primary" />
                      <Typography variant="body2" fontWeight={700}>Intuitive E-Signature Seal</Typography>
                    </Box>
                    <TextField
                      fullWidth
                      label="Type Legal Name for Seal *"
                      placeholder="Type your full legal name"
                      value={formData.signatureName}
                      onChange={(e) => setFormData({...formData, signatureName: e.target.value})}
                      sx={{ mb: 2.5, '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                    />
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.signatureConfirmed}
                          onChange={(e) => setFormData({...formData, signatureConfirmed: e.target.checked})}
                          color="primary"
                        />
                      }
                      label={
                        <Typography variant="caption" color="text.secondary" fontWeight={500}>
                          I hereby authorize and execute this digital lease agreement, certifying all profile info is valid.
                        </Typography>
                      }
                    />
                  </Box>
                </Grid>
              </Grid>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Wizard Controls */}
        <Box display="flex" justifyContent="space-between" mt={5}>
          <Button 
            variant="outlined"
            disabled={activeStep === 0 || loading} 
            onClick={handleBack}
            startIcon={<ArrowBack />}
            sx={{ borderRadius: 3, px: 3, textTransform: 'none', fontWeight: 600 }}
          >
            Back
          </Button>
          
          {activeStep === steps.length - 1 ? (
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleGenerate} 
              disabled={loading || !formData.signatureConfirmed || !formData.signatureName.trim()} 
              startIcon={loading ? <CircularProgress size={20} /> : <AssignmentTurnedIn />}
              sx={{ borderRadius: 3, px: 4, py: 1.2, textTransform: 'none', fontWeight: 700 }}
            >
              {loading ? 'Generating...' : 'Generate & Confirm'}
            </Button>
          ) : (
            <Button 
              variant="contained" 
              onClick={handleNext}
              endIcon={<ArrowForward />}
              sx={{ borderRadius: 3, px: 4, py: 1.2, textTransform: 'none', fontWeight: 700 }}
            >
              Next Step
            </Button>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default AgreementBuilder;
