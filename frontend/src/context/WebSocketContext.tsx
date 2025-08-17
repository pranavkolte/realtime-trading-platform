import React, { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';

interface OrderBookEntry {
  price: number;
  total_qty: number;
}

interface OrderBook {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  last_trade_price: number;
}

interface BookUpdateData {
  symbol: string;
  latest_price: number;
  order_book: OrderBook;
}

interface WebSocketMessage {
  event: string;
  timestamp?: string;
  data?: BookUpdateData;
  message?: string;
  [key: string]: any;
}

interface WebSocketContextType {
  isConnected: boolean;
  error: string | null;
  orderBooks: Record<string, BookUpdateData>;
  connect: () => void;
  disconnect: () => void;
  setInitialOrderBook: (orderBookData: any) => void; // Add this
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderBooks, setOrderBooks] = useState<Record<string, BookUpdateData>>({});
  const [hasInitialData, setHasInitialData] = useState(false); // Add this flag
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const shouldConnectRef = useRef(false);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const msg = JSON.parse(event.data);

      // Only process order book updates if we have initial data
      if (msg.type === 'order_book_update' && msg.data && hasInitialData) {
        const { bids, asks, last_trade_price } = msg.data;

        setOrderBooks(prev => ({
          ...prev,
          DEFAULT: {
            symbol: 'DEFAULT',
            latest_price: last_trade_price,
            order_book: { bids, asks, last_trade_price }
          }
        }));
        return;
      }

      if (msg.event === 'book_update' && msg.data && hasInitialData) {
        if (msg.data.symbol) {
          setOrderBooks(prev => ({
            ...prev,
            [msg.data.symbol]: msg.data
          }));
        }
        return;
      }

      if (msg.event === 'connected') {
        console.log('[WS] ✅ Connected:', msg.message);
      } else {
        console.log('[WS] ℹ️ Unhandled:', msg);
      }
    } catch (err) {
      console.error('[WS] Parse error:', err);
      setError('Bad message from server');
    }
  }, [hasInitialData]);

  const handleOpen = useCallback(() => {
    console.log('[WebSocket] ✅ Successfully Connected!');
    setIsConnected(true);
    setError(null);
    reconnectAttempts.current = 0;
  }, []);

  const handleClose = useCallback((event: CloseEvent) => {
    console.log('[WebSocket] ❌ Disconnected - Code:', event.code, 'Reason:', event.reason, 'Was Clean:', event.wasClean);
    setIsConnected(false);
    
    // Only attempt reconnection if we should maintain connection and it wasn't a normal closure
    if (shouldConnectRef.current && event.code !== 1000 && reconnectAttempts.current < 5) {
      const delay = Math.pow(2, reconnectAttempts.current) * 1000;
      console.log(`[WebSocket] 🔄 Attempting reconnect #${reconnectAttempts.current + 1} in ${delay}ms`);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current++;
        if (token && shouldConnectRef.current) {
          connectWebSocket(token);
        }
      }, delay);
    } else if (event.code === 4001) {
      console.log('[WebSocket] Authentication failed - token might be invalid');
      setError('Authentication failed - please refresh the page');
    }
  }, [token]);

  const handleError = useCallback((event: Event) => {
    console.error('[WebSocket] ⚠️ Error occurred:', event);
    if (wsRef.current) {
      console.log('[WebSocket] Current state:', wsRef.current.readyState);
    }
    setError('WebSocket connection error');
  }, []);

  const connectWebSocket = useCallback((authToken: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected, skipping');
      return;
    }
    
    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      console.log('[WebSocket] Closing existing connection');
      wsRef.current.close();
      wsRef.current = null;
    }
    
    const wsUrl = `${import.meta.env.VITE_WS_BASE}/api/v1/ws/update?token=${authToken}`;
    console.log('[WebSocket] 🚀 Attempting connection to:', wsUrl);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.onopen = handleOpen;
      wsRef.current.onmessage = handleMessage;
      wsRef.current.onclose = handleClose;
      wsRef.current.onerror = handleError;
    } catch (err) {
      console.error('[WebSocket] ❌ Failed to create connection:', err);
      setError('Failed to establish WebSocket connection: ' + (err as Error).message);
    }
  }, [handleOpen, handleMessage, handleClose, handleError]);

  const connect = useCallback(() => {
    console.log('[WebSocket] 🔌 connect() called');
    shouldConnectRef.current = true;
    if (token) {
      connectWebSocket(token);
    } else {
      console.log('[WebSocket] No token available, waiting...');
    }
  }, [token, connectWebSocket]);

  // Add method to set initial order book data
  const setInitialOrderBook = useCallback((orderBookData: any) => {
    if (orderBookData) {
      setOrderBooks({
        DEFAULT: {
          symbol: 'DEFAULT',
          latest_price: orderBookData.last_trade_price || 100,
          order_book: {
            bids: orderBookData.bids || [],
            asks: orderBookData.asks || [],
            last_trade_price: orderBookData.last_trade_price
          }
        }
      });
      setHasInitialData(true);
    }
  }, []);

  // Reset flags on disconnect
  const disconnect = useCallback(() => {
    console.log('[WebSocket] 🔌 disconnect() called');
    shouldConnectRef.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setOrderBooks({});
    setHasInitialData(false); // Reset the flag
    reconnectAttempts.current = 0;
  }, []);

  // Auto-connect when token becomes available
  useEffect(() => {
    if (token && shouldConnectRef.current && !isConnected) {
      console.log('[WebSocket] Token available, auto-connecting...');
      connectWebSocket(token);
    }
  }, [token, isConnected, connectWebSocket]);

  // Cleanup on provider unmount (app close)
  useEffect(() => {
    return () => {
      console.log('[WebSocket] Provider unmounting, cleaning up');
      shouldConnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'App closing');
      }
    };
  }, []);

  const value: WebSocketContextType = {
    isConnected,
    error,
    orderBooks,
    connect,
    disconnect,
    setInitialOrderBook // Add this to the context
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};