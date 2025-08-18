import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

const Login: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const [isLogin, setIsLogin] = useState(true); // Toggle between login and signup
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    user_type: 'trader'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (isLogin) {
        // Login logic
        const response = await fetch(`${import.meta.env.VITE_API_BASE}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Login failed');
        }

        const data = await response.json();
        
        if (data.data && data.data.access_token) {
          login(data.data.access_token, formData.email);
        } else {
          throw new Error('No access token received');
        }
      } else {
        // Registration logic
        const response = await fetch(`${import.meta.env.VITE_API_BASE}/auth/signup`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
            name: formData.name,
            user_type: formData.user_type,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Registration failed');
        }

        const data = await response.json();
        setSuccess('Registration successful! Please login with your credentials.');
        
        // Reset form and switch to login
        setFormData({
          email: '',
          password: '',
          name: '',
          user_type: 'trader'
        });
        setIsLogin(true);
      }
    } catch (err: any) {
      setError(err.message || `${isLogin ? 'Login' : 'Registration'} failed. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
    setFormData({
      email: '',
      password: '',
      name: '',
      user_type: 'trader'
    });
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Trading Platform</h1>
        <h2>{isLogin ? 'Login' : 'Create Account'}</h2>
        
        <form onSubmit={handleSubmit} className="login-form">
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                disabled={loading}
                placeholder="Enter your full name"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={loading}
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={loading}
              placeholder="Enter your password"
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="user_type">User Type</label>
              <select
                id="user_type"
                value={formData.user_type}
                onChange={(e) => setFormData({ ...formData, user_type: e.target.value })}
                required
                disabled={loading}
              >
                <option value="trader">Trader</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button type="submit" className="login-button" disabled={loading}>
            {loading 
              ? (isLogin ? 'Logging in...' : 'Creating account...') 
              : (isLogin ? 'Login' : 'Create Account')
            }
          </button>
        </form>

        <div className="auth-toggle">
          <p>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button 
              type="button" 
              className="toggle-btn" 
              onClick={toggleMode}
              disabled={loading}
            >
              {isLogin ? 'Sign up' : 'Login'}
            </button>
          </p>
        </div>

        {isLogin && (
          <div className="login-footer">
            <p>Demo Credentials:</p>
            <p>Email: demo@example.com | Password: demo123</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;