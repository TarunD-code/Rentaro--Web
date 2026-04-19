import React, { useState } from 'react';
import { 
  Box, 
  Stepper, 
  Step, 
  StepLabel, 
  Button, 
  Typography, 
  Paper, 
  useTheme, 
  alpha,
  Divider,
  Grid
} from '@mui/material';
import { 
  CheckCircle, 
  FileText, 
  ShieldCheck, 
  ArrowForward, 
  ArrowBack,
  Download
} from '@mui/icons-material';
import { DEFAULT_CLAUSES, AGREEMENT_TEMPLATES, Clause } from './AgreementTemplates';

const steps = ['Templates & Parties', 'Clause Library', 'Financials & Bond', 'Review & Generate'];

import { 
  FormControlLabel, 
  Checkbox, 
  TextField as MuiTextField,
  Slider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';

import AgreementPreview from './AgreementPreview';

const AgreementBuilder: React.FC = () => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState(AGREEMENT_TEMPLATES[0]);
  const [selectedClauses, setSelectedClauses] = useState<Clause[]>(
    DEFAULT_CLAUSES.map(c => ({ ...c }))
  );
  const [financials, setFinancials] = useState({
    rent: 25000,
    deposit: 50000,
    bondWeightage: 50,
  });
  const [parties, setParties] = useState({
    property: { address: 'Plot 42, Electronic City Phase 1, Bengaluru' },
    tenant: { full_name: 'John Doe', address: 'BTM Layout, Bengaluru' },
    owner: { full_name: 'Jane Smith', address: 'Indiranagar, Bengaluru' }
  });

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const toggleClause = (id: string) => {
    setSelectedClauses(prev => prev.map(c => 
      c.id === id ? { ...c, defaultChecked: !c.defaultChecked } : c
    ));
  };

  const updateClauseText = (id: string, newText: string) => {
    setSelectedClauses(prev => prev.map(c => 
      c.id === id ? { ...c, text: newText } : c
    ));
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" fontWeight={700} mb={3}>Configuration & Parties</Typography>
            <Grid container spacing={3}>
               {/* Template Cards */}
              {AGREEMENT_TEMPLATES.map((tmpl) => (
                <Grid size={{ xs: 12, md: 6 }} key={tmpl.id}>
                  <Paper 
                    onClick={() => setSelectedTemplate(tmpl)}
                    sx={{ 
                      p: 3, 
                      borderRadius: 4, 
                      cursor: 'pointer',
                      border: '2px solid',
                      borderColor: selectedTemplate.id === tmpl.id ? 'primary.main' : 'divider',
                      bgcolor: selectedTemplate.id === tmpl.id ? alpha(theme.palette.primary.main, 0.02) : 'transparent'
                    }}
                  >
                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                      <FileText color={selectedTemplate.id === tmpl.id ? 'primary' : 'disabled'} />
                      <Typography variant="subtitle1" fontWeight={700}>{tmpl.name}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">{tmpl.description}</Typography>
                  </Paper>
                </Grid>
              ))}
              
              <Grid size={{ xs: 12 }}>
                 <Divider sx={{ my: 2 }} />
                 <Typography variant="subtitle2" fontWeight={700} mb={2}>Selected Parties</Typography>
                 <Box display="flex" gap={2} flexDirection={{ xs: 'column', sm: 'row' }}>
                    <Paper variant="outlined" sx={{ p: 2, flex: 1, borderRadius: 3 }}>
                       <Typography variant="caption" color="text.secondary">Tenant</Typography>
                       <Typography variant="body2" fontWeight={700}>{parties.tenant.full_name}</Typography>
                    </Paper>
                    <Paper variant="outlined" sx={{ p: 2, flex: 1, borderRadius: 3 }}>
                       <Typography variant="caption" color="text.secondary">Property</Typography>
                       <Typography variant="body2" fontWeight={700}>{parties.property.address}</Typography>
                    </Paper>
                 </Box>
              </Grid>
            </Grid>
          </Box>
        );
      case 1:
        return (
          <Box>
            <Typography variant="h6" fontWeight={700} mb={1}>Agreement Clauses</Typography>
            <Typography variant="body2" color="text.secondary" mb={4}>Select and customize the legal clauses for your agreement.</Typography>
            
            <List sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {selectedClauses.map((clause) => (
                <Paper key={clause.id} elevation={0} sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 4, overflow: 'hidden' }}>
                    <ListItem sx={{ alignItems: 'flex-start', py: 2 }}>
                      <ListItemIcon sx={{ mt: 0.5 }}>
                        <Checkbox 
                          checked={clause.defaultChecked} 
                          disabled={clause.isMandatory}
                          onChange={() => toggleClause(clause.id)}
                        />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box display="flex" alignItems="center" gap={1} mb={1}>
                             <Typography variant="subtitle2" fontWeight={700}>{clause.category}</Typography>
                             {clause.isMandatory && <Chip label="Mandatory" size="small" sx={{ height: 16, fontSize: '0.6rem', fontWeight: 800 }} />}
                          </Box>
                        }
                        secondary={
                          <MuiTextField 
                            fullWidth 
                            multiline 
                            variant="standard"
                            value={clause.text}
                            onChange={(e) => updateClauseText(clause.id, e.target.value)}
                            InputProps={{ disableUnderline: !clause.defaultChecked }}
                            sx={{ '& .MuiInputBase-root': { fontSize: '0.9rem', color: clause.defaultChecked ? 'text.primary' : 'text.disabled' } }}
                          />
                        }
                      />
                    </ListItem>
                </Paper>
              ))}
            </List>
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="h6" fontWeight={700} mb={3}>Financial Terms & Bond</Typography>
            <Grid container spacing={4}>
              <Grid size={{ xs: 12, md: 6 }}>
                <MuiTextField 
                  fullWidth 
                  label="Monthly Rent (INR)" 
                  type="number" 
                  value={financials.rent}
                  onChange={(e) => setFinancials({...financials, rent: Number(e.target.value)})}
                  sx={{ mb: 3 }}
                />
                <MuiTextField 
                  fullWidth 
                  label="Security Deposit (INR)" 
                  type="number" 
                  value={financials.deposit}
                  onChange={(e) => setFinancials({...financials, deposit: Number(e.target.value)})}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Rentora Bond Weightage</Typography>
                <Typography variant="caption" color="text.secondary" mb={3} display="block">
                  Choosing a higher bond weightage reduces the upfront security deposit for the tenant.
                </Typography>
                <Box sx={{ px: 2 }}>
                  <Slider 
                    value={financials.bondWeightage}
                    onChange={(_, val) => setFinancials({...financials, bondWeightage: val as number})}
                    valueLabelDisplay="auto"
                    marks={[ { value: 0, label: '0%' }, { value: 50, label: '50%' }, { value: 100, label: '100%' } ]}
                  />
                </Box>
                <Box mt={4} p={2} bgcolor={alpha(theme.palette.primary.main, 0.05)} borderRadius={3} border={`1px dashed ${theme.palette.primary.main}`}>
                    <Typography variant="body2" fontWeight={600}>Estimated Bond Coverage: ₹{(financials.deposit * financials.bondWeightage / 100).toLocaleString()}</Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        );
      case 3:
        return (
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
               <Box>
                 <Typography variant="h6" fontWeight={700}>Agreement Review</Typography>
                 <Typography variant="body2" color="text.secondary">Review the generated draft before sending for signatures.</Typography>
               </Box>
               <Button variant="outlined" startIcon={<ShieldCheck color="success" />} sx={{ borderRadius: 3 }}>Instant Verification</Button>
            </Box>
            <AgreementPreview 
                clauses={selectedClauses}
                financials={financials}
                property={parties.property}
                tenant={parties.tenant}
                owner={parties.owner}
            />
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 1200, mx: 'auto', py: 4 }}>
      <Typography variant="h4" fontWeight={800} mb={1}>Advanced Agreement Builder</Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>Construct a legally compliant rental agreement in minutes.</Typography>
      
      <Stepper 
        activeStep={activeStep} 
        sx={{ 
          mb: 5,
          '& .MuiStepLabel-label': { fontWeight: 600, color: 'text.secondary' },
          '& .MuiStepLabel-label.Mui-active': { color: 'primary.main' }
        }}
      >
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper 
        elevation={0} 
        sx={{ 
          p: 0, 
          borderRadius: 6, 
          border: `1px solid ${theme.palette.divider}`,
          overflow: 'hidden',
          minHeight: 500
        }}
      >
        <Box sx={{ p: 4 }}>
          {renderStepContent(activeStep)}
        </Box>

        <Divider />
        
        <Box sx={{ p: 3, display: 'flex', justifyContent: 'space-between', bgcolor: alpha(theme.palette.background.default, 0.5) }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
            startIcon={<ArrowBack />}
            sx={{ borderRadius: 3, px: 3 }}
          >
            Back
          </Button>
          <Box>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={() => console.log('Generate PDF')}
                startIcon={<Download />}
                sx={{ borderRadius: 3, px: 4, py: 1.2, fontWeight: 700 }}
              >
                Generate Basic PDF
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<ArrowForward />}
                sx={{ borderRadius: 3, px: 4, py: 1.2, fontWeight: 700 }}
              >
                Next Step
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default AgreementBuilder;
