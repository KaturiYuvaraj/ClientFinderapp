import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Server, Shield, User, CheckCircle2, AlertCircle, HelpCircle, Key, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function Settings({ user, onLogout, onShowToast }) {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  useEffect(() => {
    api.getBaseUrl().then((url) => setApiUrl(url));
  }, []);

  const handleSaveApiUrl = async (e) => {
    e.preventDefault();
    await api.setBaseUrl(apiUrl);
    onShowToast('Backend API URL saved!', 'success');
    handleTestConnection();
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus(null);
    try {
      const health = await api.checkHealth();
      setConnectionStatus({ ok: true, msg: `Connected! Engine status: ${health.status} • Provider: ${health.business_provider}` });
    } catch (err) {
      setConnectionStatus({ ok: false, msg: err.message });
    } finally {
      setTestingConnection(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* User Profile Card */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          padding: '18px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 7 }}>
            <User size={15} color="var(--primary)" />
            <span>Account Profile</span>
          </h4>
          <span className="chip" style={{ background: 'var(--primary-light)', color: 'var(--primary)', borderColor: 'rgba(79, 70, 229, 0.25)', fontWeight: 600 }}>
            Active Session
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, fontSize: '12px' }}>
          <div style={{ background: 'var(--bg-elevated)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: 2 }}>USER NAME</div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{user?.name}</div>
          </div>
          <div style={{ background: 'var(--bg-elevated)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: 2 }}>EMAIL</div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{user?.email}</div>
          </div>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="btn btn-secondary btn-sm"
          style={{ marginTop: 14 }}
        >
          Sign Out of Workspace
        </button>
      </div>

      {/* Backend API Configuration */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          padding: '18px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 7 }}>
          <Server size={15} color="var(--accent-cyan)" />
          <span>FastAPI Engine Connection</span>
        </h4>

        <form onSubmit={handleSaveApiUrl} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Backend Host URL</label>
            <input
              type="text"
              className="form-input"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              required
            />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button type="submit" className="btn btn-primary btn-sm">
              Save Configuration
            </button>
            <button
              type="button"
              onClick={handleTestConnection}
              className="btn btn-secondary btn-sm"
              disabled={testingConnection}
            >
              <RefreshCw size={12} className={testingConnection ? 'spin' : ''} />
              <span>{testingConnection ? 'Checking...' : 'Ping Engine'}</span>
            </button>
          </div>

          {connectionStatus && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: '12px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                background: connectionStatus.ok ? 'rgba(5, 150, 105, 0.08)' : 'rgba(225, 29, 72, 0.08)',
                color: connectionStatus.ok ? '#059669' : '#e11d48',
                border: `1px solid ${connectionStatus.ok ? 'rgba(5, 150, 105, 0.22)' : 'rgba(225, 29, 72, 0.22)'}`,
              }}
            >
              {connectionStatus.ok ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
              <span>{connectionStatus.msg}</span>
            </div>
          )}
        </form>
      </div>

      {/* Chrome Extension Load Instructions */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          padding: '18px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 7 }}>
          <HelpCircle size={15} color="var(--accent-amber)" />
          <span>Running in Google Chrome Toolbar</span>
        </h4>
        <ol style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: 6, lineHeight: 1.5 }}>
          <li>Compile production assets: <code>npm run build</code> inside the <code>extension</code> folder.</li>
          <li>Open Chrome and navigate to <code>chrome://extensions</code>.</li>
          <li>Enable <strong>Developer mode</strong> in the top-right corner.</li>
          <li>Click <strong>Load unpacked</strong>.</li>
          <li>Select the <code>extension/dist</code> directory.</li>
          <li>Pin <strong>AI Client Finder</strong> to your Chrome toolbar for 1-click access!</li>
        </ol>
      </div>

      {/* Compliance Note */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          padding: '14px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          lineHeight: 1.5,
        }}
      >
        <Shield size={16} color="var(--accent-emerald)" style={{ flexShrink: 0, marginTop: 2 }} />
        <span>
          <strong>Ethical Directory Intelligence</strong>: This software queries authorized public business POIs and directories. Private personal information is strictly excluded. Outreach communication is drafted for manual human review and transmission.
        </span>
      </div>
    </div>
  );
}
