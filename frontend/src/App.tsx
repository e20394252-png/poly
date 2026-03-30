import React, { useState, useEffect } from 'react';
import './App.css';

interface Position {
  token_id: string;
  title: string;
  outcome: string;
  entry_price: number;
  shares: number;
  current_price?: number;
  pnl_percent?: number;
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
  logs: string[];
  config: {
    trade_amount: number;
    poll_interval: number;
    take_profit_threshold: number;
    stop_loss_threshold: number;
    price_min: number;
    price_max: number;
  };
}

const Terminal: React.FC<{ logs: string[] }> = ({ logs }) => {
  const [filter, setFilter] = useState<'all' | 'info' | 'success' | 'error' | 'opportunity'>('all');
  const [follow, setFollow] = useState(true);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (follow && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, follow, filter]);

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    if (filter === 'error') return log.toLowerCase().includes('error') || log.toLowerCase().includes('failed');
    if (filter === 'success') return log.toLowerCase().includes('success');
    if (filter === 'opportunity') return log.includes('OPPORTUNITY');
    if (filter === 'info') return !log.toLowerCase().includes('error') && !log.toLowerCase().includes('failed') && !log.toLowerCase().includes('success') && !log.includes('OPPORTUNITY');
    return true;
  });

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.05em' }}>SYSTEM_LOGS</span>
          <div className="terminal-actions">
            {(['all', 'info', 'success', 'error', 'opportunity'] as const).map(f => (
              <button 
                key={f} 
                className={`filter-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <button 
          className={`filter-btn ${follow ? 'active' : ''}`}
          onClick={() => setFollow(!follow)}
          style={{ marginLeft: 'auto' }}
        >
          {follow ? 'FOLLOW ON' : 'FOLLOW OFF'}
        </button>
      </div>
      <div className="terminal-body log-font" ref={scrollRef}>
        {filteredLogs.length === 0 ? (
          <div style={{ color: '#444' }}>No logs matching filter...</div>
        ) : (
          filteredLogs.map((log, i) => {
            const timeMatch = log.match(/^\[(.*?)\]/);
            const timestamp = timeMatch ? timeMatch[1] : '';
            const content = timeMatch ? log.replace(timeMatch[0], '').trim() : log;
            
            let levelClass = 'log-info';
            if (log.includes('Error') || log.includes('Failed') || log.includes('FAILED')) levelClass = 'log-error';
            else if (log.includes('Success') || log.includes('SUCCESS')) levelClass = 'log-success';
            else if (log.includes('OPPORTUNITY')) levelClass = 'log-opportunity';

            return (
              <div key={i} className={`log-line ${levelClass}`}>
                <span className="log-time">[{timestamp}]</span>
                <span className="log-content">{content}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const TradeHistory: React.FC<{ trades: Trade[] }> = ({ trades }) => {
  const groupTrades = (trades: Trade[]) => {
    if (trades.length === 0) return [];
    
    const grouped: (Trade & { count: number })[] = [];
    let currentGroup: (Trade & { count: number }) | null = null;

    trades.forEach(trade => {
      // Group if: same market title, same outcome, both are failed
      const canGroup = currentGroup && 
                       currentGroup.title === trade.title && 
                       currentGroup.outcome === trade.outcome && 
                       currentGroup.status === 'failed' && 
                       trade.status === 'failed';

      if (canGroup && currentGroup) {
        currentGroup.count++;
        // Update timestamp to the latest one
        currentGroup.timestamp = trade.timestamp;
      } else {
        currentGroup = { ...trade, count: 1 };
        grouped.push(currentGroup);
      }
    });

    return grouped;
  };

  const groupedTrades = groupTrades(trades);

  return (
    <div className="table-container" style={{ maxHeight: '500px', overflowY: 'auto' }}>
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
          {groupedTrades.length === 0 ? (
            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem' }}>No trades recorded in current session.</td></tr>
          ) : (
            groupedTrades.map((trade, i) => (
              <tr key={i} className={trade.status === 'failed' ? (trade.count > 1 ? 'trade-row-grouped' : '') : 'trade-row-success'}>
                <td>{new Date(trade.timestamp).toLocaleString()}</td>
                <td>
                  {trade.title}
                  {trade.count > 1 && <span className="badge-count">x{trade.count} REPEATS</span>}
                </td>
                <td><span className={`badge ${trade.outcome.toLowerCase() === 'yes' ? 'green' : (trade.outcome.toLowerCase() === 'no' ? 'red' : '')}`}>{trade.outcome}</span></td>
                <td style={{fontWeight: 600}}>${trade.price.toFixed(2)}</td>
                <td>{trade.size}</td>
                <td>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ 
                      color: trade.status === 'success' ? 'var(--success)' : 'var(--danger)',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}>
                      {trade.status.toUpperCase()}
                    </span>
                    {trade.error && trade.status === 'failed' && (
                      <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={trade.error}>
                        {trade.error}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

const App: React.FC = () => {
  const [data, setData] = useState<BotStatus | null>(null);
  const [loading, setLoading] = useState(true);

  let API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  // If API_URL is just a hostname (common in Render blueprints), make it a full URL
  if (API_URL && !API_URL.startsWith('http') && API_URL !== 'localhost:8000') {
    API_URL = `https://${API_URL}.onrender.com`;
  }

  const fetchData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/status`);
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

  const handleSellPosition = async (tokenId: string | null = null) => {
    try {
      if (!window.confirm(tokenId ? "Are you sure you want to sell this position at market price?" : "Are you sure you want to PANIC SELL ALL active positions?")) {
        return;
      }
      
      const payload = tokenId ? { token_id: tokenId } : {};
      const res = await fetch(`${API_URL}/api/sell_position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      console.log("Sell Response:", json);
      setTimeout(fetchData, 1000);
    } catch (error) {
      console.error("Sell error:", error);
    }
  };

  const handleStart = async () => {
    await fetch(`${API_URL}/api/start`, { method: 'POST' });
    fetchData();
  };

  const handleStop = async () => {
    await fetch(`${API_URL}/api/stop`, { method: 'POST' });
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
          <p className="stat-value gradient">${(data?.balance ?? 0).toFixed(2)} USDC</p>
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
          <p className="stat-value" style={{ fontSize: '1.2rem', paddingTop: '6px' }}>${data?.config?.trade_amount ?? 1.0} <span style={{fontSize: '0.8rem', color: 'var(--text-dim)'}}>USDC</span></p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px' }}>
            <p style={{ color: 'var(--success)', fontSize: '0.75rem', fontWeight: 600 }}>[TP] TAKE PROFIT: +{((data?.config?.take_profit_threshold ?? 0.03) * 100).toFixed(0)}%</p>
            <p style={{ color: 'var(--danger)', fontSize: '0.75rem', fontWeight: 600 }}>[SL] STOP LOSS: {((data?.config?.stop_loss_threshold ?? -0.08) * 100).toFixed(0)}%</p>
            <p style={{ color: 'var(--primary)', fontSize: '0.65rem', fontWeight: 500, opacity: 0.8, marginTop: '2px' }}>SCALP RANGE: {(data?.config?.price_min ?? 0.70) * 100}% - {(data?.config?.price_max ?? 0.89) * 100}%</p>
          </div>
        </div>

        <div className="card col-8">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>ACTIVE SCAN RESULTS</h2>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>{data?.opportunities.length} markets targeted</span>
          </div>
          <div className="table-container" style={{ height: '300px' }}>
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
          <Terminal logs={data?.logs || []} />
        </div>

        <div className="card col-12">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ marginBottom: 0 }}>ACTIVE POSITIONS <span style={{fontSize: '0.8rem', fontWeight: 400, color: 'var(--text-dim)'}}>({(data?.positions ?? []).length} items)</span></h2>
            <button className="btn btn-secondary" style={{ backgroundColor: '#EF4444', borderColor: '#DC2626', color: 'white', padding: '0.4rem 1rem', fontSize: '0.8rem' }} onClick={() => handleSellPosition(null)}>
              SELL ALL POSITIONS
            </button>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ENTERED</th>
                  <th>MARKET</th>
                  <th>SIDE</th>
                  <th>ENTRY</th>
                  <th>CURRENT</th>
                  <th>ROI / STATUS</th>
                </tr>
              </thead>
              <tbody>
                {(!data || !data.positions || data.positions.length === 0) ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem' }}>No active positions being monitored.</td></tr>
                ) : (
                  data?.positions.map((pos, i) => {
                    const currentPrice = pos.current_price || pos.entry_price;
                    const roi = ((currentPrice / pos.entry_price) - 1) * 100;
                    const isProfitable = roi > 0;
                    const isLosing = roi < -5;

                    return (
                      <tr key={i}>
                        <td style={{color: 'var(--text-dim)'}}>{new Date(pos.entry_timestamp).toLocaleTimeString()}</td>
                        <td style={{fontWeight: 500}}>{pos.title}</td>
                        <td><span className={`badge ${pos.outcome.toLowerCase() === 'yes' ? 'green' : (pos.outcome.toLowerCase() === 'no' ? 'red' : '')}`}>{pos.outcome}</span></td>
                        <td>${pos.entry_price.toFixed(3)}</td>
                        <td style={{color: isProfitable ? 'var(--success)' : (isLosing ? 'var(--danger)' : 'var(--text)')}}>${currentPrice.toFixed(3)}</td>
                        <td>
                          <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
                            <span style={{ fontWeight: 600, color: isProfitable ? 'var(--success)' : (isLosing ? 'var(--danger)' : 'var(--text)') }}>
                              {roi > 0 ? '+' : ''}{roi.toFixed(1)}%
                            </span>
                            <span style={{fontSize: '0.65rem', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px'}}>MONITORING</span>
                            <button 
                              onClick={() => handleSellPosition(pos.token_id)} 
                              style={{ marginLeft: 'auto', background: 'transparent', border: '1px solid #DC2626', color: '#EF4444', borderRadius: '4px', padding: '2px 8px', fontSize: '0.7rem', cursor: 'pointer', transition: 'all 0.2s' }}
                              onMouseOver={(e) => { e.currentTarget.style.background = '#DC2626'; e.currentTarget.style.color = '#fff'; }}
                              onMouseOut={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#EF4444'; }}
                            >
                              SELL
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card col-12">
          <h2>TRADE HISTORY</h2>
          <TradeHistory trades={data?.recent_trades || []} />
        </div>
      </div>
    </div>
  );
};

export default App;
