import React from 'react';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import AuthPage from './components/AuthPage';
import TradingPlatform from './components/TradingPlatform';
import { useAuth } from './context/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import './index.css';

const AppContent: React.FC = () => {
  const { token } = useAuth();
  const isAuthenticated = !!token; // Use token presence as authentication

  return (
    <ErrorBoundary>
      {isAuthenticated ? <TradingPlatform /> : <AuthPage />}
    </ErrorBoundary>
  );
};

function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <AppContent />
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;