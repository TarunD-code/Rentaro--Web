import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, useTheme, alpha, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, TextField, Alert, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, Tooltip, IconButton
} from '@mui/material';
import {
  AdminPanelSettings, Analytics, People, VerifiedUser, Warning,
  Gavel, MailOutline, Download, CheckCircle, Cancel, Refresh,
  OpenInNew
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HostAnalytics from '../HostAnalytics';
import ErrorBoundary from '../ErrorBoundary';

interface AdminDashboardProps {
  agreements: any[];
  metrics?: any;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ agreements, metrics }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  useTranslation();

  const token = localStorage.getItem('token');
  const API   = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // ── KYC Audit State ───────────────────────────────────────────────────────
  const [kycRecords, setKycRecords]     = useState<any[]>([]);
  const [kycLoading, setKycLoading]     = useState(true);
  const [kycError, setKycError]         = useState<string | null>(null);

  // ── Onboarding KYC queue (pending docs for review) ───────────────────────
  const [onboardingKyc, setOnboardingKyc]       = useState<any[]>([]);
  const [onboardingLoading, setOnboardingLoading] = useState(true);

  // ── Review dialog ─────────────────────────────────────────────────────────
  const [reviewing, setReviewing]           = useState<any | null>(null);
  const [rejectReason, setRejectReason]     = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewMsg, setReviewMsg]           = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Report engine ─────────────────────────────────────────────────────────
  const [emailReport, setEmailReport]       = useState('admin@rentora.com');
  const [submittingReport, setSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess]   = useState<string | null>(null);

  useEffect(() => {
    fetchKycRecords();
    fetchOnboardingKyc();
  }, []);

  const fetchKycRecords = async () => {
    setKycLoading(true);
    setKycError(null);
    try {
      const resp = await fetch(`${API}/kyc/api/v1/admin/kyc/records`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setKycRecords(await resp.json());
      else setKycError(`Failed to load KYC records (HTTP ${resp.status})`);
    } catch (err: any) {
      setKycError(err.message);
    } finally {
      setKycLoading(false);
    }
  };

  // Fetch ALL pending onboarding KYC docs across users for the review queue
  const fetchOnboardingKyc = async () => {
    setOnboardingLoading(true);
    try {
      // There's no global "all docs" endpoint yet; we fetch from onboarding stats
      // and derive the list. For now we request agreements list to get onboarding IDs.
      const resp = await fetch(`${API}/onboarding/agreements`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        // Show agreements that are still in early stages (need KYC approval)
        const all = await resp.json();
        setOnboardingKyc(
          all.filter((a: any) =>
            ['draft', 'generated', 'sent_for_signing'].includes(a.status)
          )
        );
      }
    } catch { /* non-fatal */ }
    finally { setOnboardingLoading(false); }
  };

  // ── Approve / Reject KYC doc via onboarding_service ─────────────────────
  const handleKycDecision = async (kycId: number, decision: 'verified' | 'rejected') => {
    setReviewSubmitting(true);
    setReviewMsg(null);
    try {
      const resp = await fetch(`${API}/onboarding/onboarding/kyc/${kycId}/verify`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          status: decision,
          rejection_reason: decision === 'rejected' ? rejectReason || 'Did not meet verification standards.' : null,
        }),
      });
      if (resp.ok) {
        setReviewMsg({ type: 'success', text: `KYC document ${decision} successfully.` });
        setReviewing(null);
        setRejectReason('');
        fetchOnboardingKyc();
        fetchKycRecords();
      } else {
        const err = await resp.json().catch(() => ({}));
        setReviewMsg({ type: 'error', text: err.detail || `Action failed (HTTP ${resp.status})` });
      }
    } catch (err: any) {
      setReviewMsg({ type: 'error', text: err.message });
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleReportSubmit = async (immediate: boolean) => {
    setSubmittingReport(true);
    setReportSuccess(null);
    try {
      const resp = await fetch(`${API}/kyc/api/v1/admin/reports/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ email: emailReport, file_format: 'csv', immediate }),
      });
      if (resp.ok) {
        if (immediate) {
          const blob = await resp.blob();
          const url  = window.URL.createObjectURL(blob);
          const a    = document.createElement('a');
          a.href = url; a.download = `kyc_report_${Date.now()}.csv`;
          document.body.appendChild(a); a.click(); a.remove();
          setReportSuccess('CSV report downloaded successfully!');
        } else {
          const d = await resp.json();
          setReportSuccess(d.message || 'Report scheduled.');
        }
      } else {
        const e = await resp.json();
        alert(e.detail || 'Failed to schedule report');
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setSubmittingReport(false);
    }
  };

  const adminStats = [
    { label: 'Total Properties', value: metrics?.total_active_listings ?? '—', icon: <People color="primary" />, color: theme.palette.primary.main },
    { label: 'Total Views', value: metrics?.total_views ?? '—', icon: <VerifiedUser color="success" />, color: theme.palette.success.main },
    { label: 'Pending Applications', value: metrics?.total_applications ?? '—', icon: <Warning color="warning" />, color: theme.palette.warning.main },
    { label: 'Est. Revenue', value: `₹${(metrics?.pending_rent || 0).toLocaleString()}`, icon: <Gavel color="error" />, color: theme.palette.error.main },
  ];

  const kycStatusColor = (s: string) =>
    s === 'VERIFIED' ? 'success' : s === 'FAILED' ? 'error' : 'warning';

  return (
    <Box>
      {/* ── Global Stats ─────────────────────────────────────────────────── */}
      <Grid container spacing={3} mb={5}>
        {adminStats.map((stat, i) => (
          <Grid key={i} size={{ xs: 12, sm: 6, md: 3 }}>
            <Paper sx={{
              p: 2.5, borderRadius: 4, display: 'flex', alignItems: 'center', gap: 2,
              border: `1px solid ${alpha(stat.color, 0.1)}`, bgcolor: alpha(stat.color, 0.02),
            }}>
              <Box sx={{ p: 1, bgcolor: alpha(stat.color, 0.1), borderRadius: 2, display: 'flex' }}>
                {stat.icon}
              </Box>
              <Box>
                <Typography variant="h6" fontWeight={700}>{stat.value}</Typography>
                <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Global Market Performance</Typography>
      <ErrorBoundary><HostAnalytics /></ErrorBoundary>

      {/* ── System Agreements ─────────────────────────────────────────────── */}
      <Typography variant="h6" sx={{ fontWeight: 700, mt: 5, mb: 3 }}>System-Wide Agreements</Typography>
      <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
        <Table>
          <TableHead sx={{ bgcolor: alpha(theme.palette.background.default, 0.5) }}>
            <TableRow>
              {['ID', 'Tenant', 'Owner', 'Property', 'Status'].map(h => (
                <TableCell key={h} sx={{ fontWeight: 700 }}>{h}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {agreements.length > 0 ? agreements.slice(0, 10).map(ag => (
              <TableRow key={ag.id} hover onClick={() => navigate(`/agreements/${ag.id}`)} sx={{ cursor: 'pointer' }}>
                <TableCell>#{ag.id}</TableCell>
                <TableCell>{ag.tenant_id?.split('@')[0]}</TableCell>
                <TableCell>{ag.owner_id?.split('@')[0]}</TableCell>
                <TableCell>{ag.property_id}</TableCell>
                <TableCell>
                  <Chip label={ag.status?.toUpperCase()} size="small"
                    color={ag.status === 'fully_signed' || ag.status === 'active' ? 'success' : 'warning'}
                    sx={{ fontWeight: 700, fontSize: '0.65rem' }} />
                </TableCell>
              </TableRow>
            )) : (
              <TableRow><TableCell colSpan={5} align="center">No agreements found.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* ══════════════════════════════════════════════════════════════════════
          KYC VERIFICATION QUEUE
      ══════════════════════════════════════════════════════════════════════ */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mt={6} mb={2}>
        <Typography variant="h6" fontWeight={700}>KYC Verification Queue</Typography>
        <Tooltip title="Refresh queue">
          <IconButton size="small" onClick={() => { fetchOnboardingKyc(); fetchKycRecords(); }}>
            <Refresh fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Review submitted KYC documents for onboarding tenants and owners. Approve or reject to
        advance the user through the onboarding workflow.
      </Typography>

      {reviewMsg && (
        <Alert severity={reviewMsg.type} sx={{ mb: 3, borderRadius: 2 }} onClose={() => setReviewMsg(null)}>
          {reviewMsg.text}
        </Alert>
      )}

      <Grid container spacing={3} mb={4}>
        {/* ── Left: Pending onboarding agreements needing KYC ─────────────── */}
        <Grid size={{ xs: 12, md: 8 }}>
          <TableContainer component={Paper} elevation={0}
            sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
            <Table>
              <TableHead sx={{ bgcolor: alpha(theme.palette.background.default, 0.5) }}>
                <TableRow>
                  {['Agr #', 'Tenant', 'Owner', 'Status', 'Created', 'Actions'].map(h => (
                    <TableCell key={h} sx={{ fontWeight: 700, fontSize: '0.75rem' }}>{h}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {onboardingLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <CircularProgress size={22} sx={{ my: 2 }} />
                    </TableCell>
                  </TableRow>
                ) : onboardingKyc.length > 0 ? onboardingKyc.map(ag => (
                  <TableRow key={ag.id} hover>
                    <TableCell>#{ag.id}</TableCell>
                    <TableCell sx={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {ag.tenant_id}
                    </TableCell>
                    <TableCell sx={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {ag.owner_id}
                    </TableCell>
                    <TableCell>
                      <Chip label={ag.status?.replace(/_/g, ' ').toUpperCase()} size="small"
                        color="warning" sx={{ fontWeight: 700, fontSize: '0.6rem' }} />
                    </TableCell>
                    <TableCell>{new Date(ag.created_at).toLocaleDateString('en-IN')}</TableCell>
                    <TableCell>
                      <Box display="flex" gap={0.5}>
                        <Tooltip title="Approve KYC">
                          <IconButton size="small" color="success"
                            onClick={() => handleKycDecision(ag.id, 'verified')}>
                            <CheckCircle fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Reject KYC">
                          <IconButton size="small" color="error"
                            onClick={() => setReviewing(ag)}>
                            <Cancel fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Agreement">
                          <IconButton size="small"
                            onClick={() => navigate(`/agreements/${ag.id}`)}>
                            <OpenInNew fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                )) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                      ✅ No pending KYC reviews. All agreements are progressing normally.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* ── Right: Report engine ──────────────────────────────────────────── */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{
            p: 3, borderRadius: 4, height: '100%',
            border: `1px solid ${theme.palette.divider}`,
            bgcolor: alpha(theme.palette.background.default, 0.2),
          }}>
            <Typography variant="subtitle1" fontWeight={700} mb={1}
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MailOutline color="primary" /> Report Engine
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Generate a CSV verification summary or schedule an email dispatch.
            </Typography>
            {reportSuccess && <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>{reportSuccess}</Alert>}
            <TextField label="Recipient Email" fullWidth value={emailReport}
              onChange={e => setEmailReport(e.target.value)}
              sx={{ mb: 3, '& .MuiOutlinedInput-root': { borderRadius: 2 } }} />
            <Box display="flex" flexDirection="column" gap={1.5}>
              <Button variant="contained" onClick={() => handleReportSubmit(false)}
                disabled={submittingReport || !emailReport} startIcon={<MailOutline />}
                sx={{ borderRadius: 3, textTransform: 'none', py: 1.2 }}>
                {submittingReport ? 'Scheduling…' : 'Email Report'}
              </Button>
              <Button variant="outlined" onClick={() => handleReportSubmit(true)}
                disabled={submittingReport} startIcon={<Download />}
                sx={{ borderRadius: 3, textTransform: 'none', py: 1.2 }}>
                {submittingReport ? 'Compiling…' : 'Download CSV'}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* ── Encrypted KYC Audit Log (read-only) ──────────────────────────── */}
      <Typography variant="h6" sx={{ fontWeight: 700, mt: 5, mb: 2 }}>
        KYC Encryption Audit Log
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Fernet-encrypted records from <code>kyc_service</code>. All Aadhaar / PAN values
        are masked. Raw values are never accessible via the API.
      </Typography>
      <TableContainer component={Paper} elevation={0}
        sx={{ borderRadius: 4, border: `1px solid ${theme.palette.divider}` }}>
        <Table size="small">
          <TableHead sx={{ bgcolor: alpha(theme.palette.background.default, 0.5) }}>
            <TableRow>
              {['User ID', 'Status', 'Aadhaar (Masked)', 'PAN (Masked)', 'Facial Score', 'Date'].map(h => (
                <TableCell key={h} sx={{ fontWeight: 700, fontSize: '0.72rem' }}>{h}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {kycLoading ? (
              <TableRow><TableCell colSpan={6} align="center">
                <CircularProgress size={22} sx={{ my: 2 }} />
              </TableCell></TableRow>
            ) : kycError ? (
              <TableRow><TableCell colSpan={6} align="center">
                <Alert severity="warning" sx={{ m: 1, borderRadius: 2 }}>{kycError}</Alert>
              </TableCell></TableRow>
            ) : kycRecords.length > 0 ? kycRecords.map(rec => (
              <TableRow key={rec.id} hover>
                <TableCell sx={{ fontSize: '0.75rem' }}>{rec.user_id}</TableCell>
                <TableCell>
                  <Chip label={rec.status} size="small" color={kycStatusColor(rec.status) as any}
                    sx={{ fontWeight: 700, fontSize: '0.6rem' }} />
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {rec.masked_aadhaar || '—'}
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {rec.masked_pan || '—'}
                </TableCell>
                <TableCell>
                  {rec.facial_match_score ? `${(rec.facial_match_score * 100).toFixed(1)}%` : '—'}
                </TableCell>
                <TableCell sx={{ fontSize: '0.75rem' }}>
                  {new Date(rec.created_at).toLocaleDateString('en-IN')}
                </TableCell>
              </TableRow>
            )) : (
              <TableRow><TableCell colSpan={6} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                No KYC records submitted yet.
              </TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 5, display: 'flex', gap: 2 }}>
        <Button variant="contained" startIcon={<AdminPanelSettings />} sx={{ borderRadius: 3 }}>
          User Management
        </Button>
        <Button variant="outlined" startIcon={<Analytics />} sx={{ borderRadius: 3 }}
          onClick={() => handleReportSubmit(true)}>
          Export Global Data
        </Button>
      </Box>

      {/* ── Reject KYC Dialog ─────────────────────────────────────────────── */}
      <Dialog open={!!reviewing} onClose={() => setReviewing(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Reject KYC — Agreement #{reviewing?.id}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Provide a reason for rejection. This will be visible to the applicant.
          </Typography>
          <TextField
            fullWidth multiline rows={3} autoFocus
            label="Rejection Reason"
            placeholder="e.g. Document image is unclear or not a valid government ID."
            value={rejectReason}
            onChange={e => setRejectReason(e.target.value)}
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5, gap: 1 }}>
          <Button onClick={() => setReviewing(null)} sx={{ borderRadius: 2, textTransform: 'none' }}>
            Cancel
          </Button>
          <Button variant="contained" color="error" disabled={reviewSubmitting}
            onClick={() => reviewing && handleKycDecision(reviewing.id, 'rejected')}
            startIcon={reviewSubmitting ? <CircularProgress size={16} /> : <Cancel />}
            sx={{ borderRadius: 2, textTransform: 'none' }}>
            {reviewSubmitting ? 'Rejecting…' : 'Confirm Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminDashboard;
