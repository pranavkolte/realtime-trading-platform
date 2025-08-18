import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const AuthContext = createContext<{
  isAuthenticated: boolean;
  token: string | null;
  email: string | null;
  userType: string | null;
  login: (token: string, email: string) => void;
  logout: () => void;
}>({
  isAuthenticated: false,
  token: null,
  email: null,
  userType: null,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [email, setEmail] = useState<string | null>(localStorage.getItem('email'));
  const [userType, setUserType] = useState<string | null>(null);

  // Function to decode JWT and extract user_type
  const decodeToken = (token: string) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.user_type || null;
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  };

  useEffect(() => {
    if (token) {
      const type = decodeToken(token);
      setUserType(type);
    }
  }, [token]);

  const login = (newToken: string, userEmail: string) => {
    setToken(newToken);
    setEmail(userEmail);
    localStorage.setItem('token', newToken);
    localStorage.setItem('email', userEmail);
    
    const type = decodeToken(newToken);
    setUserType(type);
  };

  const logout = () => {
    setToken(null);
    setEmail(null);
    setUserType(null);
    localStorage.removeItem('token');
    localStorage.removeItem('email');
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated: !!token,
      token,
      email,
      userType,
      login,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};