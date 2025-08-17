import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import AuthPage from './components/AuthPage';
import TradingPlatform from './components/TradingPlatform';
import { ErrorBoundary } from './components/ErrorBoundary';

function AppRoutes() {
  const { token } = useAuth();
  
  console.log('AppRoutes - token:', token);
  
  return (
    <div className="dark-theme app-wrapper">
      {token ? <TradingPlatform /> : <AuthPage />}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  );
}