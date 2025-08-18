import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import TradingPlatform from './components/TradingPlatform';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <WebSocketProvider>
          <Router>
            <div className="App">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <TradingPlatform />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </div>
          </Router>
        </WebSocketProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;