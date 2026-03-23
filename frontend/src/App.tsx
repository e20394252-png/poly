import React, { useState, useEffect } from 'react';
import './App.css';

interface Position {
  token_id: string;
  title: string;
  outcome: string;
  entry_price: number;
  shares: number;
  entry_timestamp: string;
}

interface Trade {
  timestamp: string;
  title: string;
  market: string;
  outcome: string;
  price: number;
  size: number;
  status: string;
  error?: string;
  order_id?: string;
}

interface Opportunity {
  event_title: string;
  market_question: string;
  outcome: string;
  price: number;
  token_id: string;
}

interface BotStatus {
  status: string;
  current_action: string;
  latency_ms: number;
  active_proxy: string;
  last_poll: string | null;
  trades_count: number;
  balance: number;
  realized_profit: number;
  recent_trades: Trade[];
  opportunities: Opportunity[];
  positions: Position[];
  config: {
    trade_amount: number;
    poll_interval: number;
    take_profit_threshold: number;
  };
}

const App: React.FC = () => {
  const [data, setData] = useState<BotStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/status');
      const json = await response.json();
      setData(json);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    await fetch('http://localhost:8000/api/start', { method: 'POST' });
    fetchData();
  };

  const handleStop = async () => {
    await fetch('http://localhost:8000/api/stop', { method: 'POST' });
    fetchData();
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: '#8B5CF6' }}>Initializing Systems...</div>;
  }

  return (
    <div className="dashboard">
      <header>
        <div className="title-group">
          <h1>PolyBot Terminal</h1>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Autonomous Predictive Arbitrage v1.0</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="status-badge" style={{ background: '#111827', border: '1px solid #374151', minWidth: '250px', justifyContent: 'flex-start' }}>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem', marginRight: '8px' }}>ACTION:</span>
            <span style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.8rem' }}>
              {data?.status === 'running' ? (data?.current_action || 'Idle') : 'System Halted'}
            </span>
          </div>
          <div className={`status-badge ${data?.status === 'stopped' ? 'stopped' : ''}`}>
            <div className={`indicator ${data?.status === 'running' ? 'animate-pulse' : ''}`}></div>
            {data?.status?.toUpperCase()}
          </div>
          {data?.status === 'stopped' ? (
            <button className="btn btn-primary" onClick={handleStart}>START ENGINE</button>
          ) : (
            <button className="btn btn-secondary" onClick={handleStop}>HALT</button>
          )}
        </div>
      </header>

      <div className="grid">
        <div className="card col-3">
          <p className="stat-label">BANK BALANCE</p>
          <p className="stat-value" style={{ color: 'var(--primary)' }}>${(data?.balance ?? 0).toFixed(2)} USDC</p>
        </div>
        <div className="card col-3">
          <p className="stat-label">TOTAL TRADES</p>
          <p className="stat-value">{data?.trades_count}</p>
        </div>
        <div className="card col-3">
          <p className="stat-label">REALIZED PROFIT</p>
          <p className="stat-value" style={{ color: data && (data.realized_profit ?? 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
            {data && (data.realized_profit ?? 0) >= 0 ? '+' : ''}${(data?.realized_profit ?? 0).toFixed(2)}
          </p>
        </div>
        <div className="card col-3">
          <p className="stat-label">TRADE SIZE</p>
          <p className="stat-value" style={{ fontSize: '1rem' }}>${data?.config?.trade_amount ?? 1.0} USDC (MIN)</p>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>TP @ {((data?.config?.take_profit_threshold ?? 0.05) * 100).toFixed(0)}% PROFIT</p>
        </div>

        <div className="card col-8">
          <h2>ACTIVE SCAN RESULTS</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Market Target</th>
                  <th>Probability</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data?.opportunities.length === 0 ? (
                  <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem' }}>Scanning markets for short-term alpha...</td></tr>
                ) : (
                  data?.opportunities.map((opp, i) => (
                    <tr key={i}>
                      <td>{opp.event_title}</td>
                      <td>{opp.outcome}</td>
                      <td style={{ color: 'var(--primary)', fontWeight: 600 }}>{(opp.price * 100).toFixed(0)}%</td>
                      <td><span style={{ color: 'var(--success)', fontSize: '0.75rem' }}>TARGETED</span></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card col-4">
          <h2>ENGINE CONFIG</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="stat-label">Polling Rate</span>
              <span>{data?.config.poll_interval}s</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="stat-label">Last Ping</span>
              <span style={{ fontSize: '0.75rem' }}>{data?.last_poll ? new Date(data.last_poll).toLocaleTimeString() : 'Never'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="stat-label">Active Node</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--primary)', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={data?.active_proxy}>
                {data?.active_proxy ? data.active_proxy.split('@').pop() : 'Direct'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="stat-label">API Latency</span>
              <span style={{ 
                color: (data?.latency_ms ?? 0) === 0 ? 'var(--text-dim)' : 
                       (data?.latency_ms ?? 0) < 0 ? 'var(--danger)' :
                       (data?.latency_ms ?? 0) < 400 ? 'var(--success)' : 
                       (data?.latency_ms ?? 0) < 1000 ? '#F59E0B' : 'var(--danger)',
                fontWeight: 600,
                fontSize: '0.85rem'
              }}>
                {(data?.latency_ms ?? 0) > 0 ? `${data?.latency_ms}ms` : ((data?.latency_ms ?? 0) < 0 ? 'Error' : 'Measuring...')}
              </span>
            </div>
          </div>
        </div>

        <div className="card col-12">
          <h2>ACTIVE POSITIONS ({(data?.positions ?? []).length})</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ENTERED</th>
                  <th>TARGET</th>
                  <th>SIDE</th>
                  <th>ENTRY</th>
                  <th>SHARES</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {(!data || !data.positions || data.positions.length === 0) ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-dim)' }}>No active positions being monitored.</td></tr>
                ) : (
                  data?.positions.map((pos, i) => (
                    <tr key={i}>
                      <td>{new Date(pos.entry_timestamp).toLocaleTimeString()}</td>
                      <td>{pos.title}</td>
                      <td><span className="badge">{pos.outcome}</span></td>
                      <td>${pos.entry_price.toFixed(3)}</td>
                      <td>{pos.shares.toFixed(2)}</td>
                      <td style={{ color: 'var(--success)' }}>MONITORING TP</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card col-12">
          <h2>TRADE HISTORY</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Target</th>
                  <th>Side</th>
                  <th>Price</th>
                  <th>Size</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data?.recent_trades.length === 0 ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem' }}>No trades recorded in current session.</td></tr>
                ) : (
                  data?.recent_trades.map((trade, i) => (
                    <tr key={i}>
                      <td>{new Date(trade.timestamp).toLocaleString()}</td>
                      <td>{trade.title}</td>
                      <td>{trade.outcome}</td>
                      <td>${trade.price.toFixed(2)}</td>
                      <td>{trade.size}</td>
                      <td>
                        <span style={{ 
                          color: trade.status === 'success' ? 'var(--success)' : 'var(--danger)',
                          fontSize: '0.75rem',
                          fontWeight: 700
                        }}>
                          {trade.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
