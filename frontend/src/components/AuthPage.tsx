import React, { useState } from 'react';
import { login, signup, LoginPayload, SignupPayload } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState<LoginPayload & { name?: string }>({
    email: '',
    password: '',
    name: '',
  });
  const [loading, setLoading] = useState(false);
  const { login: onLogin } = useAuth();

  console.log('AuthPage rendered');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = isLogin
        ? await login({ email: form.email, password: form.password })
        : await signup({ ...form, user_type: 'trader' } as SignupPayload);

      if (isLogin) {
        const { access_token, user_id } = res.data.data;
        onLogin(access_token, form.email, user_id);
      } else alert('Account created! Please log in.');
    } catch (err: any) {
      console.error('Auth error:', err);
      alert(err.response?.data?.message || 'Error');
    } finally {
      setLoading(false);
    }
  };

  const containerStyle: React.CSSProperties = {
    maxWidth: '400px',
    margin: '100px auto',
    textAlign: 'center',
    padding: '20px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: '#fff'
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px',
    margin: '10px 0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '16px'
  };

  const buttonStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px',
    margin: '10px 0',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer'
  };

  return (
    <div style={containerStyle}>
      <h1>🏦 Trading Platform</h1>
      <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
      <form onSubmit={handleSubmit}>
        {!isLogin && (
          <input
            style={inputStyle}
            placeholder="Full Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        )}
        <input
          style={inputStyle}
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          style={inputStyle}
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <button style={buttonStyle} disabled={loading}>
          {loading ? 'Loading...' : isLogin ? 'Login' : 'Sign Up'}
        </button>
      </form>
      <button 
        style={{...buttonStyle, backgroundColor: '#6c757d'}} 
        onClick={() => setIsLogin(!isLogin)}
      >
        {isLogin ? 'Create account' : 'Already have an account?'}
      </button>
    </div>
  );
}