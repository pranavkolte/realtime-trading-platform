import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './TradingPlatform.css';

const API_BASE = import.meta.env.VITE_API_BASE;

export default function TradingPlatform() {
  const { token, email, logout } = useAuth();
  const [stocks, setStocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [orderBook, setOrderBook] = useState<any>(null);
  const [activeOrders, setActiveOrders] = useState<any[]>([]);
  const [orderHistory, setOrderHistory] = useState<any[]>([]);
  const [tradeHistory, setTradeHistory] = useState<any[]>([]);
  const [orderTab, setOrderTab] = useState<'active' | 'history' | 'trades'>('active');
  const [orderForm, setOrderForm] = useState({
    price: '',
    quantity: '',
    orderType: 'LIMIT'
  });
  // Add local loading states for orders and order book
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [orderBookLoading, setOrderBookLoading] = useState(false);

  useEffect(() => {
    // Initial load
    loadOrdersAndBook();
  }, []);

  // Fetch orders and order book in parallel, update only relevant UI parts
  const loadOrdersAndBook = async () => {
    setOrdersLoading(true);
    setOrderBookLoading(true);

    // Fetch orders
    fetch(`${API_BASE}/orders/my-orders`, {
      headers: {
        'accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Failed to fetch orders');
        const orders = await res.json();
        setActiveOrders(
          orders.filter(
            (o: any) =>
              (o.status === 'OPEN' || o.status === 'PARTIALLY_FILLED') && o.active
          )
        );
        setOrderHistory(
          orders.filter(
            (o: any) =>
              (o.status !== 'OPEN' && o.status !== 'PARTIALLY_FILLED') || !o.active
          )
        );
        setTradeHistory([]);
        setStocks([]);
        setLoading(false); // <-- ADD THIS LINE
      })
      .catch((error) => {
        // Optionally handle error
        setLoading(false); // <-- ADD THIS LINE (in case of error)
      })
      .finally(() => setOrdersLoading(false));

    // Fetch order book
    fetch(`${API_BASE}/orders/book`, {
      headers: { 'accept': 'application/json' },
    })
      .then(async (res) => {
        if (res.ok) {
          const ob = await res.json();
          setOrderBook(ob);
        } else {
          setOrderBook(null);
        }
      })
      .catch((error) => {
        // Optionally handle error
      })
      .finally(() => setOrderBookLoading(false));
  };

  // Place order API
  const placeOrder = async (
    token: string,
    order: { side: string; order_type: string; quantity: number; price: number }
  ) => {
    const res = await fetch(`${API_BASE}/orders/place`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(order),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Order failed');
    }
    return res.json();
  };

  // Buy/Sell from market overview
  const handleOrder = async (symbol: string, type: 'buy' | 'sell', quantity: number) => {
    try {
      await placeOrder(token!, {
        side: type,
        order_type: 'market',
        quantity,
        price: 100,
      });
      // Only reload orders and order book, not the whole page
      loadOrdersAndBook();
    } catch (error: any) {
      // No alert
    }
  };

  // Place order from form
  const handlePlaceOrder = async (side: 'BUY' | 'SELL') => {
    const price = parseFloat(orderForm.price);
    const quantity = parseInt(orderForm.quantity);

    if (!price || price <= 0) {
      return;
    }
    if (!quantity || quantity <= 0) {
      return;
    }

    try {
      await placeOrder(token!, {
        side: side,
        order_type: orderForm.orderType,
        quantity: quantity,
        price: price,
      });
      setOrderForm({ price: '', quantity: '', orderType: 'LIMIT' });
      // Only reload orders and order book, not the whole page
      loadOrdersAndBook();
    } catch (error: any) {
      // No alert
    }
  };

  // Cancel order
  const cancelOrder = async (orderId: string) => {
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE}/orders/cancel/${orderId}/`,
        {
          method: 'DELETE',
          headers: {
            'accept': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Failed to cancel order');
      }
      // Only reload orders and order book, not the whole page
      loadOrdersAndBook();
    } catch (err: any) {
      // No alert
    }
  };

  return (
    <div className="dark-theme">
      <div className="trading-root">
        <header className="trading-header">
          <h1>Trading Platform</h1>
          <div className="user-info">
            <span>Welcome, <b>{email}</b>!</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            {/* Market Overview - full width */}
            <section className="card market-card market-fullwidth">
              <h3>Market Overview</h3>
              {stocks.length === 0 ? (
                <p className="empty-msg">No stock data available</p>
              ) : (
                <div className="market-grid">
                  {stocks.map((stock) => (
                    <div key={stock.symbol} className="market-stock">
                      <h4>{stock.symbol}</h4>
                      <div>Price: ${stock.price.toFixed(2)}</div>
                      <div>Change: {stock.changePercent}%</div>
                      <button className="buy-btn" onClick={() => handleOrder(stock.symbol, 'buy', 1)}>Buy</button>
                      <button className="sell-btn" onClick={() => handleOrder(stock.symbol, 'sell', 1)}>Sell</button>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Two columns: Order Book (left), My Orders (right) */}
            <div className="main-two-col">
              {/* Left: Order Book */}
              <div className="card orderbook-card">
                <h3>Order Book</h3>
                <div className="orderbook-flex">
                  {/* Buy */}
                  <div className="orderbook-side">
                    <h4>🟢 Buy</h4>
                    {orderBookLoading ? (
                      <div className="loading">Loading...</div>
                    ) : orderBook?.bids?.length ? (
                      <table className="order-table">
                        <thead>
                          <tr>
                            <th>Price</th>
                            <th>Quantity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {orderBook.bids
                            .sort((a: any, b: any) => b.price - a.price)
                            .slice(0, 10)
                            .map((bid: any, idx: number) => (
                              <tr key={idx}>
                                <td>${bid.price}</td>
                                <td>{bid.total_qty ?? bid.quantity}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    ) : (
                      <div className="empty-msg">No bids available</div>
                    )}
                  </div>
                  {/* Sell */}
                  <div className="orderbook-side">
                    <h4>🔴 Sell</h4>
                    {orderBookLoading ? (
                      <div className="loading">Loading...</div>
                    ) : orderBook?.asks?.length ? (
                      <table className="order-table">
                        <thead>
                          <tr>
                            <th>Price</th>
                            <th>Quantity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {orderBook.asks
                            .sort((a: any, b: any) => a.price - b.price)
                            .slice(0, 10)
                            .map((ask: any, idx: number) => (
                              <tr key={idx}>
                                <td>${ask.price}</td>
                                <td>{ask.total_qty ?? ask.quantity}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    ) : (
                      <div className="empty-msg">No asks available</div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: My Orders */}
              <div className="card orders-card">
                <h3>My Orders</h3>
                <div className="order-tabs">
                  <button className={orderTab === 'active' ? 'tab-btn active' : 'tab-btn'} onClick={() => setOrderTab('active')}>Active</button>
                  <button className={orderTab === 'history' ? 'tab-btn active' : 'tab-btn'} onClick={() => setOrderTab('history')}>History</button>
                </div>
                <div>
                  {orderTab === 'active' && (
                    <div>
                      <h4>Active Orders</h4>
                      {ordersLoading ? (
                        <div className="loading">Loading...</div>
                      ) : activeOrders?.length ? (
                        <div className="orders-table-scroll">
                          <table className="order-table">
                            <thead>
                              <tr>
                                <th>Side</th>
                                <th>Order Type</th>
                                <th>Price</th>
                                <th>Remaining</th>
                                <th>Status</th>
                                <th></th>
                              </tr>
                            </thead>
                            <tbody>
                              {activeOrders.map((order: any) => (
                                <tr key={order.id}>
                                  <td>
                                    <span className={`order-side ${order.side.toLowerCase()}`}>{order.side}</span>
                                  </td>
                                  <td>{order.order_type}</td>
                                  <td>${order.price}</td>
                                  <td>{order.remaining}/{order.quantity}</td>
                                  <td>
                                    <span
                                      className={
                                        "status-badge " +
                                        (order.status?.toUpperCase() === "FILLED"
                                          ? "status-filled"
                                          : order.status?.toUpperCase() === "OPEN"
                                          ? "status-open"
                                          : order.status?.toUpperCase() === "PARTIALLY_FILLED"
                                          ? "status-partially_filled"
                                          : "")
                                      }
                                    >
                                      {order.status?.replace('_', ' ').toLowerCase()}
                                    </span>
                                  </td>
                                  <td>
                                    <button
                                      className="cancel-btn"
                                      onClick={() => cancelOrder(order.id)}
                                      disabled={
                                        order.status?.toUpperCase() === 'PARTIALLY_FILLED' ||
                                        order.status?.toUpperCase() === 'FILLED'
                                      }
                                    >
                                      Cancel
                                    </button>
                                  </td>
                                </tr>
                              ))} 
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="empty-msg">No active orders</div>
                      )}
                    </div>
                  )}
                  {orderTab === 'history' && (
                    <div>
                      <h4>Order History</h4>
                      {ordersLoading ? (
                        <div className="loading">Loading...</div>
                      ) : orderHistory?.length ? (
                        <div className="orders-table-scroll">
                          <table className="order-table">
                            <thead>
                              <tr>
                                <th>Side</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>Status</th>
                                <th>Created At</th>
                              </tr>
                            </thead>
                            <tbody>
                              {orderHistory
                                .filter((order: any) => order.status !== 'PARTIALLY_FILLED')
                                .slice(-20)
                                .map((order: any, idx: number) => (
                                  <tr key={idx}>
                                    <td>{order.side}</td>
                                    <td>${order.price}</td>
                                    <td>{order.quantity}</td>
                                    <td>
                                      <span
                                        className={
                                          "status-badge " +
                                          (order.status === "FILLED"
                                            ? "status-filled"
                                            : order.status === "OPEN"
                                            ? "status-open"
                                            : order.status === "PARTIALLY_FILLED"
                                            ? "status-partially_filled"
                                            : "")
                                        }
                                      >
                                        {order.status.replace('_', ' ').toLowerCase()}
                                      </span>
                                    </td>
                                    <td>
                                      {new Date(order.created_at).toLocaleString('en-IN', {
                                        timeZone: 'Asia/Kolkata',
                                        year: 'numeric',
                                        month: 'short',
                                        day: '2-digit',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                        hour12: true,
                                      })}
                                    </td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="empty-msg">No order history</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Place Order Section - Bottom */}
            <div className="place-order-section">
              <div className="card place-order-card">
                <h3>📊 Place Order</h3>
                <div className="place-order-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label>Price</label>
                      <input
                        type="number"
                        value={orderForm.price}
                        onChange={(e) => setOrderForm({...orderForm, price: e.target.value})}
                        placeholder="0.00"
                        step="0.01"
                        min="0"
                      />
                    </div>
                    <div className="form-group">
                      <label>Quantity</label>
                      <input
                        type="number"
                        value={orderForm.quantity}
                        onChange={(e) => setOrderForm({...orderForm, quantity: e.target.value})}
                        placeholder="0"
                        step="1"
                        min="1"
                      />
                    </div>
                    <div className="form-group">
                      <label>Order Type</label>
                      <select
                        value={orderForm.orderType}
                        onChange={(e) => setOrderForm({...orderForm, orderType: e.target.value})}
                      >
                        <option value="LIMIT">LIMIT</option>
                        <option value="MARKET">MARKET</option>
                      </select>
                    </div>
                    <div className="form-group order-buttons">
                      <button
                        className="order-btn buy-order-btn"
                        onClick={() => handlePlaceOrder('BUY')}
                      >
                        🟢 Buy
                      </button>
                      <button
                        className="order-btn sell-order-btn"
                        onClick={() => handlePlaceOrder('SELL')}
                      >
                        🔴 Sell
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Control buttons */}
                <div className="control-buttons">
                  <button className="control-btn" onClick={loadOrdersAndBook}>
                    🔄 Refresh Orders
                  </button>
                  <button className="control-btn" onClick={loadOrdersAndBook}>
                    📊 Refresh All
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}