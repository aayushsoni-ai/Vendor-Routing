import React from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';

interface Attempt {
  vendor: string;
  outcome: string;
  latencyMs?: number;
  error?: string;
}

interface AttemptsTimelineProps {
  attempts: Attempt[];
}

export const AttemptsTimeline: React.FC<AttemptsTimelineProps> = ({ attempts }) => {
  if (!attempts || attempts.length === 0) {
    return <div style={{ color: 'var(--color-muted)', fontSize: '13px' }}>No attempts made.</div>;
  }

  return (
    <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {attempts.map((attempt, index) => {
        const isSuccess = attempt.outcome === 'SUCCESS';
        
        let statusClass = 'failed';
        if (isSuccess) statusClass = 'success';
        
        return (
          <div key={index} className={`timeline-attempt ${statusClass}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isSuccess ? (
                <CheckCircle2 size={16} color="var(--color-success)" />
              ) : (
                <XCircle size={16} color="var(--color-danger)" />
              )}
              
              <span style={{ fontWeight: 600, fontSize: '13px' }}>
                {attempt.vendor}
              </span>
              
              <span className={`chip ${isSuccess ? 'chip-success' : 'chip-danger'}`}>
                {attempt.outcome}
              </span>
              
              {attempt.latencyMs !== undefined && attempt.latencyMs > 0 && (
                <span className="telemetry" style={{ color: 'var(--color-muted)' }}>
                  {attempt.latencyMs}ms
                </span>
              )}
            </div>
            
            {attempt.error && (
              <div style={{ fontSize: '11px', color: 'var(--color-danger)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                Err: {attempt.error}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
