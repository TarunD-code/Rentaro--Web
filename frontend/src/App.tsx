import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import { Box, CircularProgress, Typography, alpha, useTheme } from '@mui/material';

// Lazy load pages for performance
const Register = lazy(() => import('./pages/Register'));
const Login = lazy(() => import('./pages/Login'));
const VerifyOTP = lazy(() => import('./pages/VerifyOTP'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const CreateProperty = lazy(() => import('./pages/CreateProperty'));
const Listings = lazy(() => import('./pages/Listings'));
const Home = lazy(() => import('./pages/Home'));
const PropertyDetail = lazy(() => import('./pages/PropertyDetail'));
const AgreementWorkflow = lazy(() => import('./pages/AgreementWorkflow'));
const DepositPayment = lazy(() => import('./pages/DepositPayment'));
const AutoPaySetup = lazy(() => import('./pages/AutoPaySetup'));
const PaymentHistory = lazy(() => import('./pages/PaymentHistory'));
const MoveOutInitiate = lazy(() => import('./pages/MoveOutInitiate'));
const MoveOutReview = lazy(() => import('./pages/MoveOutReview'));
const SettlementPage = lazy(() => import('./pages/SettlementPage'));
const ServiceRequestForm = lazy(() => import('./pages/ServiceRequestForm'));
const OwnerAssignmentPanel = lazy(() => import('./pages/OwnerAssignmentPanel'));
const VendorTaskView = lazy(() => import('./pages/VendorTaskView'));
const MaintenanceHistory = lazy(() => import('./pages/MaintenanceHistory'));
const OnboardingForm = lazy(() => import('./pages/OnboardingForm'));
const AgreementPage = lazy(() => import('./pages/AgreementPage'));
const OwnerPayoutDashboard = lazy(() => import('./pages/OwnerPayoutDashboard'));
const StatementsPage = lazy(() => import('./pages/StatementsPage'));
const ReconciliationAdmin = lazy(() => import('./pages/ReconciliationAdmin'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const OwnerPremiumDashboard = lazy(() => import('./pages/owner/OwnerDashboard'));
const FeaturedListings = lazy(() => import('./pages/owner/FeaturedListings'));
const ReportCenter = lazy(() => import('./pages/owner/ReportCenter'));
const SubscriptionLanding = lazy(() => import('./pages/tenant/SubscriptionLanding'));

import { isFeatureEnabled } from './config/featureFlags';


const LoadingScreen = () => {
  const theme = useTheme();
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100vh', 
        width: '100vw',
        alignItems: 'center', 
        justifyContent: 'center',
        bgcolor: 'background.default',
        gap: 2
      }}
    >
      <CircularProgress thickness={4} size={50} sx={{ color: 'primary.main' }} />
      <Typography 
        variant="h6" 
        sx={{ 
          fontWeight: 600, 
          color: alpha(theme.palette.text.primary, 0.6),
          fontFamily: 'Inter'
        }}
      >
        Loading Rentora...
      </Typography>
    </Box>
  );
};

import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const TenantDashboard = lazy(() => import('./pages/tenant/TenantDashboard'));

const App: React.FC = () => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const isAuthenticated = !!token && !!role;

    React.useEffect(() => {
        const handleAuthLogout = () => {
            window.location.href = '/login';
        };
        window.addEventListener('auth-logout', handleAuthLogout);
        return () => window.removeEventListener('auth-logout', handleAuthLogout);
    }, []);

    const getDefaultDashboard = () => {
        if (role === 'owner') return '/owner/dashboard';
        if (role === 'admin') return '/admin/dashboard';
        return '/tenant/dashboard';
    };

  return (
    <Router>
      <Suspense fallback={<LoadingScreen />}>
        <ErrorBoundary>
          <Layout>
            <Routes>
              {/* Public Routes */}
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/verify" element={<VerifyOTP />} />
              
              {/* Protected Routes */}
              <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/create" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><CreateProperty /></ProtectedRoute>} />
              <Route path="/listings/:id" element={<PropertyDetail />} />
              <Route path="/listings" element={<Listings />} />
              <Route path="/agreements/:id" element={<ProtectedRoute><AgreementWorkflow /></ProtectedRoute>} />
              <Route path="/payments/deposit/:agreementId" element={<ProtectedRoute><DepositPayment /></ProtectedRoute>} />
              <Route path="/payments/autopay" element={<ProtectedRoute><AutoPaySetup /></ProtectedRoute>} />
              <Route path="/payments/history" element={<ProtectedRoute><PaymentHistory /></ProtectedRoute>} />
              <Route path="/moveout/initiate/:agreementId" element={<ProtectedRoute><MoveOutInitiate /></ProtectedRoute>} />
              <Route path="/moveout/review/:moveoutId" element={<ProtectedRoute><MoveOutReview /></ProtectedRoute>} />
              <Route path="/moveout/settlement/:settlementId" element={<ProtectedRoute><SettlementPage /></ProtectedRoute>} />
              <Route path="/maintenance/request" element={<ProtectedRoute><ServiceRequestForm /></ProtectedRoute>} />
              <Route path="/maintenance/assign" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><OwnerAssignmentPanel /></ProtectedRoute>} />
              <Route path="/maintenance/tasks" element={<ProtectedRoute><VendorTaskView /></ProtectedRoute>} />
              <Route path="/maintenance/history" element={<ProtectedRoute><MaintenanceHistory /></ProtectedRoute>} />
              <Route path="/onboarding/form" element={<ProtectedRoute><OnboardingForm /></ProtectedRoute>} />
              <Route path="/onboarding/agreements" element={<ProtectedRoute><AgreementPage /></ProtectedRoute>} />
              <Route path="/payouts" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><OwnerPayoutDashboard /></ProtectedRoute>} />
              <Route path="/statements" element={<ProtectedRoute><StatementsPage /></ProtectedRoute>} />
              <Route path="/reconciliation" element={<ProtectedRoute allowedRoles={['admin']}><ReconciliationAdmin /></ProtectedRoute>} />
              <Route path="/chat/:receiverId" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
              <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
              
              {/* Role Specific Dashboards */}
              <Route path="/dashboard" element={<Navigate to={getDefaultDashboard()} replace />} />
              <Route path="/tenant/dashboard" element={<ProtectedRoute allowedRoles={['tenant', 'admin']}><TenantDashboard /></ProtectedRoute>} />
              <Route path="/owner/dashboard" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><OwnerPremiumDashboard /></ProtectedRoute>} />
              <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
              
              <Route path="/owner/premium" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><FeaturedListings /></ProtectedRoute>} />
              <Route path="/owner/reports" element={<ProtectedRoute allowedRoles={['owner', 'admin']}><ReportCenter /></ProtectedRoute>} />
              <Route path="/tenant/subscription" element={<ProtectedRoute allowedRoles={['tenant']}><SubscriptionLanding /></ProtectedRoute>} />
  
              {/* Entry Redirects */}
              <Route path="/" element={
                  isAuthenticated 
                      ? <Navigate to={getDefaultDashboard()} replace /> 
                      : <Navigate to="/login" replace />
              } />
  
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </ErrorBoundary>
      </Suspense>
    </Router>
  );
};

export default App;
