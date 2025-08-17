import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_BASE;

export const placeOrder = (
  token: string,
  body: { side: string; order_type: string; quantity: number; price: number }
) =>
  axios.post(`${API_BASE}/orders/place`, body, {
    headers: { Authorization: `Bearer ${token}` },
  });
