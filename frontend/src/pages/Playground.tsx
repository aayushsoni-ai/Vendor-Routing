import React, { useEffect, useState } from 'react';
import { Play, Info } from 'lucide-react';
import { AttemptsTimeline } from '../components/AttemptsTimeline';
import { StatusDot } from '../components/StatusDot';

interface PlaygroundProps {
  apiUrl: string;
  mockUrl: string;
}

interface MockStatus {
  profile: {
    baseLatencyMs: number;
    jitterMs: number;
    errorRate: number;
    supports: string[];
    rateLimitPerMinute: number;
  };
  forcedDown: boolean;
  requestsInWindow: number;
}

export const Playground: React.FC<PlaygroundProps> = ({ apiUrl, mockUrl }) => {
  const [capability, setCapability] = useState('PAN_VERIFICATION');
  const [pan, setPan] = useState('ABCDE1234F');
  const [name, setName] = useState('Rahul Sharma');
  
  // Requirements overrides
  const [maxLatency, setMaxLatency] = useState('');
  const [preferLowCost, setPreferLowCost] = useState(false);
  const [requiredFeatures, setRequiredFeatures] = useState('nameMatch');
  const [strategyOverride, setStrategyOverride] = useState('');

  // Results state
  const [loading, setLoading] = useState(false);
  const [routeResult, setRouteResult] = useState<any | null>(null);

  // Mock vendors health control state
  const [mockStatus, setMockStatus] = useState<Record<string, MockStatus>>({});

  const fetchMockStatus = async () => {
    try {
      // Mock vendors runs on port 9000 (standard port in scaffold)
      const res = await fetch(`${mockUrl}/mock/status`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMockStatus(data);
    } catch {
      // Gracefully ignore if mock vendors service isn't reachable directly
    }
  };

  useEffect(() => {
    fetchMockStatus();
    const interval = setInterval(fetchMockStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleMock = async (vendorName: string) => {
    try {
      const res = await fetch(`${mockUrl}/mock/${vendorName}/toggle-down`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error();
      await fetchMockStatus();
    } catch {
      alert(`Could not connect to mock vendor simulator at ${mockUrl}`);
    }
  };

  const handleFireRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setRouteResult(null);

    const payload: any = {
      capability,
      payload: {
        pan,
        name
      }
    };

    const requirements: any = {};
    if (maxLatency) requirements.maxLatencyMs = Number(maxLatency);
    if (preferLowCost) requirements.preferLowCost = true;
    if (requiredFeatures) {
      requirements.requiredFeatures = requiredFeatures.split(',').map(f => f.trim()).filter(Boolean);
    }
    if (strategyOverride) requirements.strategy = strategyOverride;

    if (Object.keys(requirements).length > 0) {
      payload.requirements = requirements;
    }

    try {
      const res = await fetch(`${apiUrl}/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setRouteResult(data);
    } catch (err: any) {
      alert(`API Connection Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Playground & Simulator</h1>
          <p className="page-desc">Simulate requests and toggle mock provider health to observe failover chains live.</p>
        </div>
      </div>

      <div className="grid-2">
        {/* Left: Input parameters */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="panel-card" style={{ marginBottom: 0 }}>
            <h2 className="panel-title">1. Trigger Route Query</h2>
            <form onSubmit={handleFireRoute}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Capability</label>
                  <select
                    className="form-control"
                    value={capability}
                    onChange={e => setCapability(e.target.value)}
                  >
                    <option value="PAN_VERIFICATION">PAN_VERIFICATION</option>
                    <option value="OCR">OCR (Stub)</option>
                    <option value="SMS">SMS (Stub)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">PAN Card Format</label>
                  <input
                    type="text"
                    required
                    className="form-control font-mono"
                    value={pan}
                    onChange={e => setPan(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Name on Card</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={name}
                  onChange={e => setName(e.target.value)}
                />
              </div>

              <h2 className="panel-title" style={{ marginTop: '24px', fontSize: '11px' }}>Routing Options Overrides</h2>
              
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Max Allowed Latency (ms)</label>
                  <input
                    type="number"
                    className="form-control"
                    placeholder="e.g. 2000"
                    value={maxLatency}
                    onChange={e => setMaxLatency(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Strategy Override</label>
                  <select
                    className="form-control"
                    value={strategyOverride}
                    onChange={e => setStrategyOverride(e.target.value)}
                  >
                    <option value="">Use Config Default</option>
                    <option value="priority">Priority</option>
                    <option value="weighted">Weighted</option>
                    <option value="lowest_latency">Lowest Latency</option>
                    <option value="lowest_cost">Lowest Cost</option>
                    <option value="round_robin">Round Robin</option>
                    <option value="health_based">Health Based</option>
                  </select>
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Required Features</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="nameMatch, dobMatch"
                    value={requiredFeatures}
                    onChange={e => setRequiredFeatures(e.target.value)}
                  />
                </div>
                <div className="form-group" style={{ justifyContent: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', marginTop: '16px' }}>
                    <input
                      type="checkbox"
                      checked={preferLowCost}
                      onChange={e => setPreferLowCost(e.target.checked)}
                    />
                    Force Cheapest Option (Soft Override)
                  </label>
                </div>
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }} disabled={loading}>
                <Play size={14} /> Send API Request
              </button>
            </form>
          </div>

          {/* Provider Failover Simulation Card */}
          <div className="panel-card" style={{ marginBottom: 0 }}>
            <h2 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Info size={16} /> Live Outage Simulator
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--color-muted)', marginBottom: '16px' }}>
              Simulate outages to test real failover. Toggle providers offline and fire requests.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {Object.keys(mockStatus).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--color-warning)' }}>
                  Outage simulator offline (Is mock-vendors running at {mockUrl}?)
                </div>
              ) : (
                Object.keys(mockStatus).map(name => {
                  const state = mockStatus[name];
                  return (
                    <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '13px' }}>{name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--color-muted)' }}>
                          Latency: {state.profile.baseLatencyMs}ms | Err: {state.profile.errorRate * 100}%
                        </div>
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <StatusDot status={state.forcedDown ? 'down' : 'healthy'} label={state.forcedDown ? 'Offline' : 'Online'} />
                        <button
                          className={`btn ${state.forcedDown ? 'btn-danger' : 'btn-secondary'}`}
                          style={{ padding: '4px 10px', fontSize: '11px' }}
                          onClick={() => handleToggleMock(name)}
                        >
                          {state.forcedDown ? 'Power Up' : 'Kill Provider'}
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right: API Response */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="panel-card" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
            <h2 className="panel-title">2. API Gateway Trace</h2>
            
            {loading ? (
              <div style={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--color-muted)' }}>
                Waiting for backend router...
              </div>
            ) : routeResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', flexGrow: 1 }}>
                
                {/* Result header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>Transaction Status</span>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: routeResult.status === 'SUCCESS' ? 'var(--color-success)' : 'var(--color-danger)' }}>
                      {routeResult.status}
                    </div>
                  </div>
                  {routeResult.latencyMs !== undefined && (
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>Total Latency</span>
                      <div className="telemetry" style={{ fontSize: '18px', fontWeight: 700 }}>
                        {routeResult.latencyMs}ms
                      </div>
                    </div>
                  )}
                </div>

                {/* Routing Reason */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-muted)', textTransform: 'uppercase' }}>
                    Routing Verdict
                  </span>
                  <p style={{ fontSize: '13px', marginTop: '4px', lineHeight: '1.4' }}>
                    {routeResult.routingReason}
                  </p>
                </div>

                {/* Attempts Timeline */}
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-muted)', textTransform: 'uppercase' }}>
                    Failover Chain Verification
                  </span>
                  <AttemptsTimeline attempts={routeResult.attempts} />
                </div>

                {/* Standardized Response Code block */}
                <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                    Normalized Canonical Output
                  </span>
                  <pre className="playground-results" style={{ flexGrow: 1 }}>
                    {JSON.stringify(routeResult, null, 2)}
                  </pre>
                </div>

              </div>
            ) : (
              <div style={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--color-muted)', textAlign: 'center', padding: '40px' }}>
                Fill out parameters on the left and execute the query to inspect routing traces here.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
