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
const AdminAnalyticsDashboard = lazy(() => import('./pages/AdminAnalyticsDashboard'));

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

const App: React.FC = () => {
  return (
    <Router>
      <Suspense fallback={<LoadingScreen />}>
        <Layout>
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/verify" element={<VerifyOTP />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/create" element={<CreateProperty />} />
            <Route path="/listings/:id" element={<PropertyDetail />} />
            <Route path="/listings" element={<Listings />} />
            <Route path="/agreements/:id" element={<AgreementWorkflow />} />
            <Route path="/payments/deposit/:agreementId" element={<DepositPayment />} />
            <Route path="/payments/autopay" element={<AutoPaySetup />} />
            <Route path="/payments/history" element={<PaymentHistory />} />
            <Route path="/moveout/initiate/:agreementId" element={<MoveOutInitiate />} />
            <Route path="/moveout/review/:moveoutId" element={<MoveOutReview />} />
            <Route path="/moveout/settlement/:settlementId" element={<SettlementPage />} />
            <Route path="/maintenance/request" element={<ServiceRequestForm />} />
            <Route path="/maintenance/assign" element={<OwnerAssignmentPanel />} />
            <Route path="/maintenance/tasks" element={<VendorTaskView />} />
            <Route path="/maintenance/history" element={<MaintenanceHistory />} />
            <Route path="/onboarding/form" element={<OnboardingForm />} />
            <Route path="/onboarding/agreements" element={<AgreementPage />} />
            <Route path="/payouts" element={<OwnerPayoutDashboard />} />
            <Route path="/statements" element={<StatementsPage />} />
            <Route path="/reconciliation" element={<ReconciliationAdmin />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsDashboard />} />
            <Route path="/" element={isFeatureEnabled('landing_v1') ? <Home /> : <Navigate to="/dashboard" replace />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Suspense>
    </Router>
  );
};

export default App;
