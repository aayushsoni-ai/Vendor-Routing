import React, { useState } from 'react';
import { Activity, ShieldCheck, Database, Terminal, Bot } from 'lucide-react';
import { Vendors } from './pages/Vendors';
import { Metrics } from './pages/Metrics';
import { Logs } from './pages/Logs';
import { Playground } from './pages/Playground';
import { Agent } from './pages/Agent';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type Page = 'vendors' | 'metrics' | 'logs' | 'playground' | 'agent';

const App: React.FC = () => {
  const [activePage, setActivePage] = useState<Page>('metrics');

  const renderPage = () => {
    switch (activePage) {
      case 'vendors':
        return <Vendors apiUrl={API_URL} />;
      case 'metrics':
        return <Metrics apiUrl={API_URL} />;
      case 'logs':
        return <Logs apiUrl={API_URL} />;
      case 'playground':
        return <Playground apiUrl={API_URL} />;
      case 'agent':
        return <Agent apiUrl={API_URL} />;
      default:
        return <Metrics apiUrl={API_URL} />;
    }
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar Nav */}
      <nav className="sidebar">
        <div className="logo-container">
          <div className="logo-title">
            <Activity size={18} color="var(--color-accent)" />
            <span>ROUTER GATEWAY</span>
          </div>
          <div className="logo-sub">v1.0.0-observability</div>
        </div>

        <ul className="nav-list">
          <li>
            <button
              className={`nav-item ${activePage === 'metrics' ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
              onClick={() => setActivePage('metrics')}
            >
              <Activity size={16} />
              <span>Telemetry Matrix</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-item ${activePage === 'vendors' ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
              onClick={() => setActivePage('vendors')}
            >
              <Database size={16} />
              <span>Upstream Providers</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-item ${activePage === 'playground' ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
              onClick={() => setActivePage('playground')}
            >
              <Terminal size={16} />
              <span>Gateway Sandbox</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-item ${activePage === 'logs' ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
              onClick={() => setActivePage('logs')}
            >
              <ShieldCheck size={16} />
              <span>Decision Log</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-item ${activePage === 'agent' ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
              onClick={() => setActivePage('agent')}
            >
              <Bot size={16} />
              <span>AI Copilot</span>
            </button>
          </li>
        </ul>
        
        <div style={{ marginTop: 'auto', padding: '12px 10px', fontSize: '11px', color: 'var(--color-muted)', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }}></span>
            <span>Gateway Online</span>
          </div>
          <div style={{ marginTop: '4px', fontFamily: 'var(--font-mono)' }}>sqlite+aiosqlite</div>
        </div>
      </nav>

      {/* Main Panel content */}
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
};

export default App;
