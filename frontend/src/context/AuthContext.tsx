import React, { createContext, useContext, useState, ReactNode } from 'react';

interface AuthContextType {
  token: string | null;
  email: string | null;
  userId: string | null;
  login: (token: string, email: string, userId: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem('token');
    } catch {
      return null;
    }
  });
  
  const [email, setEmail] = useState<string | null>(() => {
    try {
      return localStorage.getItem('email');
    } catch {
      return null;
    }
  });
  
  const [userId, setUserId] = useState<string | null>(() => {
    try {
      return localStorage.getItem('userId');
    } catch {
      return null;
    }
  });

  const login = (newToken: string, newEmail: string, newUserId: string) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('email', newEmail);
    localStorage.setItem('userId', newUserId);
    setToken(newToken);
    setEmail(newEmail);
    setUserId(newUserId);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    localStorage.removeItem('userId');
    setToken(null);
    setEmail(null);
    setUserId(null);
  };

  return (
    <AuthContext.Provider value={{ token, email, userId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}