import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import { PriceChartChartJS } from './PriceChart';

interface Trade {
  id: string;
  engine_trade_id: number;
  price: number;
  quantity: number;
  buy_order_id: string;
  sell_order_id: string;
  buy_user_id: string;
  sell_user_id: string;
  ts: string;
}

interface MarketStats {
  best_bid: number | null;
  best_ask: number | null;
  spread: number | null;
  last_trade_price: number | null;
}

const AdminDashboard: React.FC = () => {
  const { token, email, logout } = useAuth();
  const { orderBooks, isConnected, priceHistory } = useWebSocket();
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [tradesLoading, setTradesLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE;

  // Fetch recent trades
  const fetchRecentTrades = async () => {
    setTradesLoading(true);
    try {
      const response = await fetch(`${API_BASE}/orders/recent-trades?limit=50`, {
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch recent trades');
      }
      
      const trades = await response.json();
      setRecentTrades(trades);
    } catch (error) {
      console.error('Error fetching recent trades:', error);
      setRecentTrades([]);
    } finally {
      setTradesLoading(false);
    }
  };

  // Fetch market stats
  const fetchMarketStats = async () => {
    setStatsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/orders/market-stats`, {
        headers: {
          'accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch market stats');
      }
      
      const stats = await response.json();
      setMarketStats(stats);
    } catch (error) {
      console.error('Error fetching market stats:', error);
      setMarketStats(null);
    } finally {
      setStatsLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchRecentTrades(),
        fetchMarketStats()
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  // Refresh all data
  const refreshData = async () => {
    await Promise.all([
      fetchRecentTrades(),
      fetchMarketStats()
    ]);
  };

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const liveOrderBook = orderBooks.DEFAULT?.order_book;

  // For chart
  const chartPrices = priceHistory.map(item => item.price);
  const chartTimestamps = priceHistory.map(item => item.timestamp);

  if (loading) {
    return (
      <div className="dark-theme">
        <div className="trading-root">
          <div className="loading">Loading Admin Dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dark-theme">
      <div className="trading-root">
        {/* WebSocket status indicator */}
        <div className={`ws-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Live Data' : '🔴 Disconnected'}
        </div>
        
        <header className="trading-header">
          <h1>Admin Dashboard</h1>
          <div className="user-info">
            <span>Welcome, <b>{email}</b> (Admin)</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>


        {/* Add Price Chart Section */}
        <section className="card market-card market-fullwidth">
        <h2>Live Market Data</h2>
          <h3>Price Chart</h3>
          <div style={{ flex: 1 }}>
            <PriceChartChartJS 
              data={chartPrices} 
              timestamps={chartTimestamps}
              currentPrice={marketStats?.last_trade_price != null ? marketStats.last_trade_price : undefined}
            />
            <div style={{ marginTop: '8px', fontSize: '14px', color: '#6b7280' }}>
              {priceHistory.length > 0 && (
                <span style={{ marginLeft: '16px' }}>
                  Latest Price: ${priceHistory[priceHistory.length - 1]?.price || 'N/A'}
                </span>
              )}
            </div>
          </div>
        </section>

        <div className="main-two-col">
          {/* Order Book */}
          <div className="card orderbook-card">
            <h3>Live Order Book</h3>
            <div className="orderbook-flex">
              {/* Buy Side */}
              <div className="orderbook-side">
                <h4>🟢 Bids</h4>
                {liveOrderBook ? (
                  <table className="order-table">
                    <thead>
                      <tr>
                        <th>Price</th>
                        <th>Quantity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {liveOrderBook.bids
                        .sort((a: any, b: any) => b.price - a.price)
                        .slice(0, 10)
                        .map((bid: any, index: number) => (
                          <tr key={`bid-${bid.price}-${index}`}>
                            <td>${bid.price.toFixed(2)}</td>
                            <td>{bid.total_qty}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="empty-msg">No bid data</div>
                )}
              </div>

              {/* Sell Side */}
              <div className="orderbook-side">
                <h4>🔴 Asks</h4>
                {liveOrderBook ? (
                  <table className="order-table">
                    <thead>
                      <tr>
                        <th>Price</th>
                        <th>Quantity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {liveOrderBook.asks
                        .sort((a: any, b: any) => a.price - b.price)
                        .slice(0, 10)
                        .map((ask: any, index: number) => (
                          <tr key={`ask-${ask.price}-${index}`}>
                            <td>${ask.price.toFixed(2)}</td>
                            <td>{ask.total_qty}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="empty-msg">No ask data</div>
                )}
              </div>
            </div>
          </div>

          {/* Recent Trades */}
          <div className="card orders-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>Recent Trades</h3>
              <button 
                className="control-btn" 
                onClick={fetchRecentTrades}
                disabled={tradesLoading}
              >
                🔄 Refresh Trades
              </button>
            </div>
            
            {tradesLoading ? (
              <div className="loading">Loading trades...</div>
            ) : recentTrades.length > 0 ? (
              <div className="orders-table-scroll" style={{ maxHeight: '500px' }}>
                <table className="order-table">
                  <thead>
                    <tr>
                      <th>Trade ID</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th>Buy User</th>
                      <th>Sell User</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTrades.map((trade) => (
                      <tr key={trade.id}>
                        <td>#{trade.engine_trade_id}</td>
                        <td>${trade.price.toFixed(2)}</td>
                        <td>{trade.quantity}</td>
                        <td title={trade.buy_user_id}>
                          {trade.buy_user_id.substring(0, 8)}...
                        </td>
                        <td title={trade.sell_user_id}>
                          {trade.sell_user_id.substring(0, 8)}...
                        </td>
                        <td>{formatDateTime(trade.ts)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-msg">No recent trades</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;