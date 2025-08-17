import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_BASE;

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload extends LoginPayload {
  name: string;
  user_type: string;
}

export const login = (payload: LoginPayload) =>
  axios.post(`${API_BASE}/auth/login`, payload);

export const signup = (payload: SignupPayload) =>
  axios.post(`${API_BASE}/auth/signup`, payload);