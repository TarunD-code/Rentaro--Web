import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: JSX.Element;
  allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const location = useLocation();
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');

  if (!token) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && (!userRole || !allowedRoles.includes(userRole))) {
    // Redirect to login if role is missing or not allowed, to avoid infinite loops with "/"
    localStorage.clear();
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
