import React, { useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false }) => {
  const { isAuthenticated, userType } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && userType) {
      // Auto-redirect based on user type when accessing root path
      if (location.pathname === '/') {
        if (userType === 'admin') {
          navigate('/admin', { replace: true });
        }
        // traders stay on root path
      }
    }
  }, [isAuthenticated, userType, location.pathname, navigate]);

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin-only routes
  if (adminOnly && userType !== 'admin') {
    return <Navigate to="/" replace />;
  }

  // Prevent non-admin users from accessing admin routes
  if (location.pathname === '/admin' && userType !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;