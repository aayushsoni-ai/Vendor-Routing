import React from 'react';

export type VendorStatus = 'healthy' | 'degraded' | 'down' | 'open';

interface StatusDotProps {
  status: VendorStatus;
  label?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, label }) => {
  const displayLabel = label || status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <div className="status-dot-container">
      <span className={`status-dot ${status}`} />
      <span className="telemetry" style={{ fontSize: '12px' }}>{displayLabel}</span>
    </div>
  );
};
