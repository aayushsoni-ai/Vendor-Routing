import React, { useEffect, useState } from 'react';
import { Send, Bot } from 'lucide-react';

interface AgentProps {
  apiUrl: string;
}

interface Issue {
  vendor: string;
  status: string;
  reason: string;
  action: string;
}

interface Recommendation {
  recommendedStrategy: string;
  justification: string;
  fallbackSequence: string[];
  recommendedThresholds: Record<string, any>;
}

export const Agent: React.FC<AgentProps> = ({ apiUrl }) => {
  // Config parsing
  const [nlText, setNlText] = useState('Use weighted routing with 70% VendorA and 30% VendorB, with failover enabled');
  const [parsedConfig, setParsedConfig] = useState<any | null>(null);

  // Decision explanation
  const [requestId, setRequestId] = useState('');
  const [recentRequests, setRecentRequests] = useState<string[]>([]);
  const [explaining, setExplaining] = useState(false);

  // Health diagnosis
  const [issues, setIssues] = useState<Issue[]>([]);
  const [diagnosing, setDiagnosing] = useState(false);

  // Recommendation
  const [goal, setGoal] = useState('Minimize cost while maintaining high availability');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [recommending, setRecommending] = useState(false);

  // Chat window logs
  const [chatLog, setChatLog] = useState<{ sender: 'user' | 'agent' | 'system'; text: string }[]>([
    { sender: 'agent', text: 'Hello SRE. I am your routing intelligence copilot. Ask me to parse rules, explain decisions, diagnose anomalies, or optimize routing paths.' }
  ]);

  const fetchRecentLogs = async () => {
    try {
      const res = await fetch(`${apiUrl}/routing-logs?page_size=10`);
      const data = await res.json();
      if (data && data.logs) {
        setRequestId(data.logs[0]?.requestId || '');
        setRecentRequests(data.logs.map((log: any) => log.requestId));
      }
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    fetchRecentLogs();
  }, []);

  const handleParseConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlText.trim()) return;
    
    setChatLog(prev => [...prev, { sender: 'user', text: `Parse config from rule: "${nlText}"` }]);
    setParsedConfig(null);

    try {
      const res = await fetch(`${apiUrl}/agent/config-from-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: nlText })
      });
      if (!res.ok) throw new Error('Parsing failed');
      const data = await res.json();
      setParsedConfig(data.config);
      setChatLog(prev => [...prev, {
        sender: 'agent',
        text: `Parsed Routing Config generated successfully (${data.mode} mode). Ready to apply.`
      }]);
    } catch (err: any) {
      setChatLog(prev => [...prev, { sender: 'system', text: `Error: ${err.message}` }]);
    }
  };

  const handleExplainDecision = async () => {
    if (!requestId) return;
    
    setChatLog(prev => [...prev, { sender: 'user', text: `Explain routing decision for transaction: ${requestId.slice(0, 8)}...` }]);
    setExplaining(true);

    try {
      const res = await fetch(`${apiUrl}/agent/explain-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requestId })
      });
      if (!res.ok) throw new Error('Explanation request failed');
      const data = await res.json();
      setChatLog(prev => [...prev, { sender: 'agent', text: data.explanation }]);
    } catch (err: any) {
      setChatLog(prev => [...prev, { sender: 'system', text: `Error: ${err.message}` }]);
    } finally {
      setExplaining(false);
    }
  };

  const handleDiagnose = async () => {
    setChatLog(prev => [...prev, { sender: 'user', text: 'Scan telemetry logs for degraded providers.' }]);
    setIssues([]);
    setDiagnosing(true);

    try {
      const res = await fetch(`${apiUrl}/agent/detect-unhealthy`);
      if (!res.ok) throw new Error('Diagnostics failed');
      const data = await res.json();
      setIssues(data.issues);
      if (data.issues.length === 0) {
        setChatLog(prev => [...prev, { sender: 'agent', text: 'SRE status: All upstream providers are healthy. Circuit breakers CLOSED. Latencies stable.' }]);
      } else {
        setChatLog(prev => [...prev, { sender: 'agent', text: `Anomaly detected: Found ${data.issues.length} degraded providers. Please inspect findings.` }]);
      }
    } catch (err: any) {
      setChatLog(prev => [...prev, { sender: 'system', text: `Error: ${err.message}` }]);
    } finally {
      setDiagnosing(false);
    }
  };

  const handleRecommend = async () => {
    if (!goal.trim()) return;
    
    setChatLog(prev => [...prev, { sender: 'user', text: `Recommend settings for goal: "${goal}"` }]);
    setRecommendation(null);
    setRecommending(true);

    try {
      const res = await fetch(`${apiUrl}/agent/recommend-strategy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal })
      });
      if (!res.ok) throw new Error('Recommendation failed');
      const data = await res.json();
      setRecommendation(data.recommendation);
      setChatLog(prev => [...prev, {
        sender: 'agent',
        text: `Recommended strategy: ${data.recommendation.recommendedStrategy}. Justification: ${data.recommendation.justification}`
      }]);
    } catch (err: any) {
      setChatLog(prev => [...prev, { sender: 'system', text: `Error: ${err.message}` }]);
    } finally {
      setRecommending(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Agentic AI Copilot</h1>
          <p className="page-desc">LLM-assisted routing rule compilation, explanation, anomaly diagnostics, and recommendations.</p>
        </div>
      </div>

      <div className="grid-2">
        {/* Left: Chat Shell */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="panel-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '540px' }}>
            <h2 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <Bot size={18} color="var(--color-accent)" /> Interactive Operator Chat
            </h2>
            
            <div className="chat-window" style={{ flexGrow: 1 }}>
              {chatLog.map((chat, idx) => (
                <div key={idx} className={`chat-bubble ${chat.sender}`}>
                  {chat.text}
                </div>
              ))}
            </div>
            
            <button className="btn btn-secondary" onClick={handleDiagnose} disabled={diagnosing} style={{ width: '100%' }}>
              Diagnose Providers Health Anomaly
            </button>
          </div>
        </div>

        {/* Right: Functional Control Panels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Config Compiler */}
          <div className="panel-card">
            <h2 className="panel-title">Rule Compiler (Plain text to Config)</h2>
            <form onSubmit={handleParseConfig} style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                className="form-control"
                style={{ flexGrow: 1 }}
                value={nlText}
                onChange={e => setNlText(e.target.value)}
              />
              <button type="submit" className="btn btn-primary" style={{ padding: '8px 12px' }}>
                <Send size={14} />
              </button>
            </form>
            {parsedConfig && (
              <pre className="playground-results" style={{ marginTop: '12px', padding: '12px', fontSize: '11px' }}>
                {JSON.stringify(parsedConfig, null, 2)}
              </pre>
            )}
          </div>

          {/* Explain Decision */}
          <div className="panel-card">
            <h2 className="panel-title">Explain Routing Verdict</h2>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <select
                className="form-control font-mono"
                style={{ flexGrow: 1, fontSize: '12px' }}
                value={requestId}
                onChange={e => setRequestId(e.target.value)}
              >
                {recentRequests.length === 0 ? (
                  <option value="">No recent requests found</option>
                ) : (
                  recentRequests.map(id => (
                    <option key={id} value={id}>{id.slice(0, 16)}...</option>
                  ))
                )}
              </select>
              <button
                className="btn btn-secondary"
                onClick={handleExplainDecision}
                disabled={explaining || !requestId}
              >
                Explain
              </button>
            </div>
          </div>

          {/* SRE Issues list */}
          {issues.length > 0 && (
            <div className="panel-card" style={{ borderColor: 'var(--color-danger)' }}>
              <h2 className="panel-title" style={{ color: 'var(--color-danger)' }}>Telemetry Anomaly Diagnosis</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {issues.map((issue, idx) => (
                  <div key={idx} style={{ padding: '10px', backgroundColor: 'rgba(248, 81, 73, 0.05)', border: '1px solid rgba(248, 81, 73, 0.2)', borderRadius: '6px' }}>
                    <div style={{ fontWeight: 600, fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{issue.vendor}</span>
                      <span className="chip chip-danger" style={{ fontSize: '10px' }}>{issue.status}</span>
                    </div>
                    <p style={{ fontSize: '12px', marginTop: '4px', color: 'var(--color-text)' }}>{issue.reason}</p>
                    <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginTop: '6px' }}>
                      <strong>Action:</strong> {issue.action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strategy Recommender */}
          <div className="panel-card">
            <h2 className="panel-title">Strategy Optimizer</h2>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
              <input
                type="text"
                className="form-control"
                style={{ flexGrow: 1 }}
                value={goal}
                onChange={e => setGoal(e.target.value)}
              />
              <button className="btn btn-secondary" onClick={handleRecommend} disabled={recommending}>
                Optimize
              </button>
            </div>

            {recommendation && (
              <div style={{ padding: '12px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>Strategy Suggestion:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{recommendation.recommendedStrategy}</strong>
                </div>
                <p style={{ color: 'var(--color-muted)', lineHeight: '1.4', marginBottom: '8px' }}>
                  {recommendation.justification}
                </p>
                <div>
                  <strong>Fallback Sequence:</strong>
                  <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                    {recommendation.fallbackSequence.map(v => (
                      <span key={v} className="chip">{v}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};
