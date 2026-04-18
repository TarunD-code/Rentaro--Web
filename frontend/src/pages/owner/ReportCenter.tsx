import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Button, 
  Chip,
  IconButton,
  CircularProgress,
  Stack
} from '@mui/material';
import { 
  CloudDownload, 
  PictureAsPdf, 
  Add,
  Refresh
} from '@mui/icons-material';

const ReportCenter: React.FC = () => {
    const [reports, setReports] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/owner-dashboard/owners/${user.user_identifier}/reports`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (response.ok) setReports(data);
        } catch (err) {
            console.error("Failed to fetch reports", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []);

    const handleRequestReport = async (type: string) => {
        setGenerating(true);
        try {
            const token = localStorage.getItem('token');
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/owner-dashboard/owners/${user.user_identifier}/reports?report_type=${type}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                await fetchReports();
            }
        } catch (err) {
            console.error("Failed to generate report", err);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <Box sx={{ py: 6, px: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={6}>
                <Box>
                    <Typography variant="h4" fontWeight={800}>Report Center</Typography>
                    <Typography color="text.secondary">Download professional performance and tax-ready reports.</Typography>
                </Box>
                <Stack direction="row" spacing={2}>
                    <Button variant="outlined" startIcon={<Refresh />} onClick={fetchReports}>Refresh</Button>
                    <Button 
                        variant="contained" 
                        startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <Add />}
                        disabled={generating}
                        onClick={() => handleRequestReport('revenue')}
                    >
                        New Revenue Report
                    </Button>
                </Stack>
            </Box>

            <Paper elevation={0} sx={{ borderRadius: 6, border: '1px solid #eee', overflow: 'hidden' }}>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow sx={{ bgcolor: '#f8f9fa' }}>
                                <TableCell sx={{ fontWeight: 700 }}>Report ID</TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>Date Generated</TableCell>
                                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 700 }}>Action</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow><TableCell colSpan={5} align="center" sx={{ py: 10 }}><CircularProgress /></TableCell></TableRow>
                            ) : reports.length === 0 ? (
                                <TableRow><TableCell colSpan={5} align="center" sx={{ py: 10 }}><Typography color="text.secondary">No reports generated yet.</Typography></TableCell></TableRow>
                            ) : reports.map((report) => (
                                <TableRow key={report.id} hover>
                                    <TableCell>#REP-{report.id.toString().padStart(6, '0')}</TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={1} alignItems="center">
                                            <PictureAsPdf fontSize="small" color="error" />
                                            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{report.report_type}</Typography>
                                        </Stack>
                                    </TableCell>
                                    <TableCell>{new Date(report.generated_at).toLocaleDateString()}</TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={report.status} 
                                            size="small" 
                                            color={report.status === 'generated' ? 'success' : 'warning'} 
                                            variant="outlined"
                                        />
                                    </TableCell>
                                    <TableCell align="right">
                                        <Button 
                                            size="small" 
                                            startIcon={<CloudDownload />}
                                            href={`${import.meta.env.VITE_API_URL}${report.report_path}`}
                                            target="_blank"
                                        >
                                            Download
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Box>
    );
};

export default ReportCenter;
