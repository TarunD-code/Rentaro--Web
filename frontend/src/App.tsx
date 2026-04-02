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
            <Route path="/" element={isFeatureEnabled('landing_v1') ? <Home /> : <Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Suspense>
    </Router>
  );
};

export default App;
