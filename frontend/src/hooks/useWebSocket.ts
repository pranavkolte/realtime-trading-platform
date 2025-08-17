import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export type WsMessage = { type: string; data: any };

export const useWebSocket = () => {
  const { token } = useAuth();
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<WsMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;
    const url = `${import.meta.env.VITE_WS_BASE}/api/v1/ws/update?token=${token}`;
    ws.current = new WebSocket(url);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);
    ws.current.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setMessages((prev) => [...prev, msg]);
    };

    return () => ws.current?.close();
  }, [token]);

  return { connected, messages };
};