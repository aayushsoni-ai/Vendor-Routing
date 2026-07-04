import React, { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, ShieldAlert } from 'lucide-react';
import { AttemptsTimeline } from '../components/AttemptsTimeline';

interface Attempt {
  vendor: string;
  outcome: string;
  latencyMs?: number;
  error?: string;
}

interface LogEntry {
  id: string;
  requestId: string;
  capability: string;
  strategyUsed: string;
  vendorUsed: string | null;
  outcome: string;
  routingReason: string;
  latencyMs: number | null;
  cost: number | null;
  attempts: Attempt[];
  filterReasons: Record<string, string>;
  createdAt: string;
}

interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

interface LogsResponse {
  logs: LogEntry[];
  pagination: Pagination;
}

interface LogsProps {
  apiUrl: string;
}

export const Logs: React.FC<LogsProps> = ({ apiUrl }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter criteria
  const [capability, setCapability] = useState('');
  const [vendor, setVendor] = useState('');
  const [outcome, setOutcome] = useState('');
  const [page, setPage] = useState(1);
  
  // Expanded rows state
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      let query = `?page=${page}`;
      if (capability) query += `&capability=${capability}`;
      if (vendor) query += `&vendor=${vendor}`;
      if (outcome) query += `&outcome=${outcome}`;

      const res = await fetch(`${apiUrl}/routing-logs${query}`);
      if (!res.ok) throw new Error('Failed to fetch routing logs');
      const data: LogsResponse = await res.json();
      setLogs(data.logs);
      setPagination(data.pagination);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, capability, vendor, outcome]);

  const toggleRow = (id: string) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  const getOutcomeBadge = (outcome: string) => {
    return outcome === 'SUCCESS' ? (
      <span className="chip chip-success">SUCCESS</span>
    ) : (
      <span className="chip chip-danger">FAILED</span>
    );
  };

  const formatTime = (isoString: string) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Decision Logs</h1>
          <p className="page-desc">Audit trail of all routed requests, filtering reasons, and failover chains.</p>
        </div>
      </div>

      {/* Filters Panel */}
      <div className="panel-card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '160px' }}>
            <label className="form-label">Capability</label>
            <select
              className="form-control"
              value={capability}
              onChange={e => { setCapability(e.target.value); setPage(1); }}
            >
              <option value="">All Capabilities</option>
              <option value="PAN_VERIFICATION">PAN_VERIFICATION</option>
              <option value="OCR">OCR</option>
              <option value="SMS">SMS</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0, minWidth: '160px' }}>
            <label className="form-label">Vendor</label>
            <select
              className="form-control"
              value={vendor}
              onChange={e => { setVendor(e.target.value); setPage(1); }}
            >
              <option value="">All Vendors</option>
              <option value="VendorA">VendorA</option>
              <option value="VendorB">VendorB</option>
              <option value="VendorC">VendorC</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0, minWidth: '140px' }}>
            <label className="form-label">Outcome</label>
            <select
              className="form-control"
              value={outcome}
              onChange={e => { setOutcome(e.target.value); setPage(1); }}
            >
              <option value="">All Outcomes</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
          
          <button className="btn btn-secondary" style={{ marginTop: '18px' }} onClick={fetchLogs}>
            Filter
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'var(--color-muted)', fontSize: '14px' }}>Loading logs...</div>
      ) : error ? (
        <div style={{ color: 'var(--color-danger)', fontSize: '14px' }}>Error: {error}</div>
      ) : logs.length === 0 ? (
        <div className="panel-card" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)' }}>
          <p>No decision logs found matching active filter parameters.</p>
        </div>
      ) : (
        <>
          <div className="panel-card" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}></th>
                  <th>Timestamp</th>
                  <th>Request ID</th>
                  <th>Capability</th>
                  <th>Strategy</th>
                  <th>Provider</th>
                  <th>Latency</th>
                  <th>Cost</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr onClick={() => toggleRow(log.id)} style={{ cursor: 'pointer' }}>
                        <td>{isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</td>
                        <td className="telemetry">{formatTime(log.createdAt)}</td>
                        <td>
                          <span className="id-badge">{log.requestId.slice(0, 8)}...</span>
                        </td>
                        <td>
                          <span className="chip">{log.capability}</span>
                        </td>
                        <td className="telemetry" style={{ color: 'var(--color-muted)' }}>{log.strategyUsed}</td>
                        <td style={{ fontWeight: 600 }}>{log.vendorUsed || 'N/A'}</td>
                        <td className="telemetry">{log.latencyMs ? `${log.latencyMs}ms` : '-'}</td>
                        <td className="telemetry">{log.cost !== null ? `₹${log.cost}` : '-'}</td>
                        <td>{getOutcomeBadge(log.outcome)}</td>
                      </tr>

                      {isExpanded && (
                        <tr>
                          <td colSpan={9} style={{ backgroundColor: 'rgba(255,255,255,0.015)', padding: '20px 24px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <span style={{ fontWeight: 600, fontSize: '12px', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
                                  Routing Logic Trace
                                </span>
                                <div style={{ fontSize: '14px', marginTop: '6px', color: 'var(--color-text)' }}>
                                  {log.routingReason}
                                </div>
                              </div>

                              {Object.keys(log.filterReasons).length > 0 && (
                                <div style={{ marginTop: '8px' }}>
                                  <span style={{ fontWeight: 600, fontSize: '12px', color: 'var(--color-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <ShieldAlert size={14} color="var(--color-warning)" /> Exclusion Decisions
                                  </span>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                                    {Object.entries(log.filterReasons).map(([vendor, reason]) => (
                                      <div key={vendor} style={{ fontSize: '13px', color: 'var(--color-muted)' }}>
                                        <strong style={{ color: 'var(--color-text)' }}>{vendor}:</strong> {reason}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              <div style={{ marginTop: '8px' }}>
                                <span style={{ fontWeight: 600, fontSize: '12px', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
                                  Failover Attempt Chain
                                </span>
                                <AttemptsTimeline attempts={log.attempts} />
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {pagination && pagination.totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Prev
              </button>
              <span style={{ alignSelf: 'center', fontSize: '13px', color: 'var(--color-muted)', padding: '0 8px' }}>
                Page {page} of {pagination.totalPages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page === pagination.totalPages}
                onClick={() => setPage(p => Math.min(pagination.totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
