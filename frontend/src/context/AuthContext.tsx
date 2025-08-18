import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  token: string | null;
  email: string | null;
  isAuthenticated: boolean;
  login: (token: string, userEmail: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  // Load authentication data from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('authToken');
    const savedEmail = localStorage.getItem('userEmail');
    
    if (savedToken && savedEmail) {
      setToken(savedToken);
      setEmail(savedEmail);
    }
  }, []);

  const login = (authToken: string, userEmail: string) => {
    setToken(authToken);
    setEmail(userEmail);
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('userEmail', userEmail);
  };

  const logout = () => {
    setToken(null);
    setEmail(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    // Redirect to login page
    window.location.href = '/login';
  };

  const value: AuthContextType = {
    token,
    email,
    isAuthenticated: !!token,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};