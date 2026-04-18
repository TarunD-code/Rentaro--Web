import React, { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  MenuItem, 
  Box, 
  Typography,
  alpha,
  useTheme,
  CircularProgress
} from '@mui/material';
import { 
  SupportAgent, 
  AutoAwesome,
  EventNote,
  ListAlt
} from '@mui/icons-material';

interface ConciergeModalProps {
  open: boolean;
  onClose: () => void;
  propertyId?: number;
}

const ConciergeModal: React.FC<ConciergeModalProps> = ({ open, onClose, propertyId }) => {
    const theme = useTheme();
    const [requestType, setRequestType] = useState('viewing');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/subscriptions/concierge/requests`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    request_type: requestType,
                    property_id: propertyId,
                    details: { notes, timestamp: new Date().toISOString() }
                })
            });

            if (response.ok) {
                alert("Concierge request submitted! An agent will contact you shortly.");
                onClose();
            } else {
                const err = await response.json();
                alert(`Error: ${err.detail}`);
            }
        } catch (err) {
            alert("Failed to submit request");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs" PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
            <DialogTitle sx={{ textAlign: 'center', pb: 0 }}>
                <Box sx={{ 
                    display: 'inline-flex', 
                    p: 2, 
                    borderRadius: '50%', 
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    mb: 2
                }}>
                    <SupportAgent color="primary" fontSize="large" />
                </Box>
                <Typography variant="h5" fontWeight={800}>Concierge Assistance</Typography>
                <Typography variant="body2" color="text.secondary">Premium VIP Feature</Typography>
            </DialogTitle>

            <DialogContent>
                <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                        select
                        fullWidth
                        label="What can we help with?"
                        value={requestType}
                        onChange={(e) => setRequestType(e.target.value)}
                        variant="outlined"
                    >
                        <MenuItem value="viewing">
                            <Box display="flex" alignItems="center" gap={1}>
                                <EventNote fontSize="small" /> Coordinate Viewing
                            </Box>
                        </MenuItem>
                        <MenuItem value="shortlist">
                            <Box display="flex" alignItems="center" gap={1}>
                                <ListAlt fontSize="small" /> Build Property Shortlist
                            </Box>
                        </MenuItem>
                        <MenuItem value="custom">
                            <Box display="flex" alignItems="center" gap={1}>
                                <AutoAwesome fontSize="small" /> Bespoke Assistance
                            </Box>
                        </MenuItem>
                    </TextField>

                    <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Specific Requirements / Preferred Times"
                        placeholder="e.g. I only want to see pet-friendly properties near Electronic City..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                    />
                </Box>
            </DialogContent>

            <DialogActions sx={{ p: 3, pt: 0 }}>
                <Button onClick={onClose} fullWidth variant="text" sx={{ borderRadius: 2 }}>Cancel</Button>
                <Button 
                    onClick={handleSubmit} 
                    fullWidth 
                    variant="contained" 
                    disabled={loading}
                    sx={{ borderRadius: 2, fontWeight: 700 }}
                >
                    {loading ? <CircularProgress size={24} color="inherit" /> : 'Send Request'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ConciergeModal;
