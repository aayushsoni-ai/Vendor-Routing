import React, { useEffect, useState } from 'react';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import { StatusDot } from '../components/StatusDot';

interface Vendor {
  id: string;
  name: string;
  capability: string;
  baseUrl: string;
  priority: number;
  weight: number;
  costPerRequest: number;
  timeoutMs: number;
  rateLimitPerMinute: number;
  supportedFeatures: string[];
  enabled: boolean;
}

interface VendorsProps {
  apiUrl: string;
  mockUrl: string;
}

export const Vendors: React.FC<VendorsProps> = ({ apiUrl, mockUrl }) => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [name, setName] = useState('');
  const [capability, setCapability] = useState('PAN_VERIFICATION');
  const [baseUrl, setBaseUrl] = useState(mockUrl);
  const [priority, setPriority] = useState(1);
  const [weight, setWeight] = useState(50);
  const [costPerRequest, setCostPerRequest] = useState(1.0);
  const [timeoutMs, setTimeoutMs] = useState(2000);
  const [rateLimitPerMinute, setRateLimitPerMinute] = useState(100);
  const [featuresInput, setFeaturesInput] = useState('nameMatch, dobMatch');

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/vendors`);
      if (!res.ok) throw new Error('Failed to fetch vendors');
      const data = await res.json();
      setVendors(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVendor = async (vendorName: string) => {
    if (!window.confirm(`Are you sure you want to delete ${vendorName}?`)) return;

    try {
      const res = await fetch(`${apiUrl}/vendors/${vendorName}`, {
        method: 'DELETE'
      });

      if (!res.ok) {
        throw new Error('Failed to delete vendor');
      }

      await fetchVendors();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  useEffect(() => {
    if (vendors.length > 0) {
      setBaseUrl(vendors[0].baseUrl);
    }
  }, [vendors]);

  const handleSaveVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name,
      capability,
      baseUrl,
      priority: Number(priority),
      weight: Number(weight),
      costPerRequest: Number(costPerRequest),
      timeoutMs: Number(timeoutMs),
      rateLimitPerMinute: Number(rateLimitPerMinute),
      supportedFeatures: featuresInput.split(',').map(f => f.trim()).filter(Boolean),
      enabled: editingVendor ? editingVendor.enabled : true
    };

    try {
      let res;
      if (editingVendor) {
        res = await fetch(`${apiUrl}/vendors/${editingVendor.name}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            baseUrl: payload.baseUrl,
            priority: payload.priority,
            weight: payload.weight,
            costPerRequest: payload.costPerRequest,
            timeoutMs: payload.timeoutMs,
            rateLimitPerMinute: payload.rateLimitPerMinute,
            supportedFeatures: payload.supportedFeatures,
            enabled: payload.enabled
          })
        });
      } else {
        res = await fetch(`${apiUrl}/vendors`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Save failed');
      }

      await fetchVendors();
      setShowAddForm(false);
      setEditingVendor(null);
      // Reset form
      setName('');
      setPriority(1);
      setWeight(50);
      setCostPerRequest(1.0);
      setTimeoutMs(2000);
      setRateLimitPerMinute(100);
      setFeaturesInput('nameMatch, dobMatch');
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const startEdit = (vendor: Vendor) => {
    setEditingVendor(vendor);
    setShowAddForm(false);
    setName(vendor.name);
    setCapability(vendor.capability);
    setBaseUrl(vendor.baseUrl);
    setPriority(vendor.priority);
    setWeight(vendor.weight);
    setCostPerRequest(vendor.costPerRequest);
    setTimeoutMs(vendor.timeoutMs);
    setRateLimitPerMinute(vendor.rateLimitPerMinute);
    setFeaturesInput(vendor.supportedFeatures.join(', '));
  };

  const handleCancel = () => {
    setShowAddForm(false);
    setEditingVendor(null);
    setName('');
    setPriority(1);
    setWeight(50);
    setCostPerRequest(1.0);
    setTimeoutMs(2000);
    setRateLimitPerMinute(100);
    setFeaturesInput('nameMatch, dobMatch');
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Vendor Registry</h1>
          <p className="page-desc">Register and manage upstream capabilities and provider accounts.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
          <Plus size={16} /> Add Provider
        </button>
      </div>

      {(showAddForm || editingVendor) && (
        <div className="panel-card" style={{ maxWidth: '600px' }}>
          <h2 className="panel-title">{editingVendor ? `Edit ${editingVendor.name} Details` : 'Register New Vendor'}</h2>
          <form onSubmit={handleSaveVendor}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Vendor Name</label>
                <input
                  type="text"
                  required
                  disabled={!!editingVendor}
                  className="form-control"
                  placeholder="e.g. VendorA"
                  value={name}
                  onChange={e => setName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Capability</label>
                <select
                  className="form-control"
                  disabled={!!editingVendor}
                  value={capability}
                  onChange={e => setCapability(e.target.value)}
                >
                  <option value="PAN_VERIFICATION">PAN_VERIFICATION</option>
                  <option value="OCR">OCR</option>
                  <option value="SMS">SMS</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Base URL</label>
              <input
                type="text"
                required
                className="form-control"
                value={baseUrl}
                onChange={e => setBaseUrl(e.target.value)}
              />
            </div>

            <div className="grid-3">
              <div className="form-group">
                <label className="form-label">Priority (1-10)</label>
                <input
                  type="number"
                  min="1"
                  required
                  className="form-control"
                  value={priority}
                  onChange={e => setPriority(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Weight (0-100)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  required
                  className="form-control"
                  value={weight}
                  onChange={e => setWeight(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Cost per Call (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  className="form-control"
                  value={costPerRequest}
                  onChange={e => setCostPerRequest(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Timeout (ms)</label>
                <input
                  type="number"
                  min="100"
                  required
                  className="form-control"
                  value={timeoutMs}
                  onChange={e => setTimeoutMs(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Rate Limit (per min)</label>
                <input
                  type="number"
                  min="10"
                  required
                  className="form-control"
                  value={rateLimitPerMinute}
                  onChange={e => setRateLimitPerMinute(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Supported Features (Comma separated)</label>
              <input
                type="text"
                className="form-control"
                placeholder="nameMatch, dobMatch"
                value={featuresInput}
                onChange={e => setFeaturesInput(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button type="submit" className="btn btn-primary">Save Vendor</button>
              <button type="button" className="btn btn-secondary" onClick={handleCancel}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div style={{ color: 'var(--color-muted)', fontSize: '14px' }}>Loading registered providers...</div>
      ) : error ? (
        <div style={{ color: 'var(--color-danger)', fontSize: '14px' }}>Error: {error}</div>
      ) : vendors.length === 0 ? (
        <div className="panel-card" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)' }}>
          <p>No vendors registered yet. Use the "Add Provider" button above to get started.</p>
        </div>
      ) : (
        <div className="panel-card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Capability</th>
                <th>Priority</th>
                <th>Weight</th>
                <th>Cost</th>
                <th>Timeout</th>
                <th>Rate Limit</th>
                <th>Features</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map(vendor => (
                <tr key={vendor.id}>
                  <td style={{ fontWeight: 600 }}>{vendor.name}</td>
                  <td>
                    <span className="chip">{vendor.capability}</span>
                  </td>
                  <td className="telemetry">{vendor.priority}</td>
                  <td className="telemetry">{vendor.weight}%</td>
                  <td className="telemetry">₹{vendor.costPerRequest}</td>
                  <td className="telemetry">{vendor.timeoutMs}ms</td>
                  <td className="telemetry">{vendor.rateLimitPerMinute}/m</td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {vendor.supportedFeatures.map(f => (
                        <span key={f} className="chip" style={{ fontSize: '10px', padding: '1px 6px' }}>{f}</span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <StatusDot status={vendor.enabled ? 'healthy' : 'down'} label={vendor.enabled ? 'Enabled' : 'Disabled'} />
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => startEdit(vendor)}
                      >
                        <Edit2 size={12} /> Edit
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => handleDeleteVendor(vendor.name)}
                      >
                        <Trash2 size={12} /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
