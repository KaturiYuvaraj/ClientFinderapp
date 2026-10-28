import React, { useState } from 'react';
import { Target, Lock, Mail, User, ArrowRight, ShieldCheck, Sparkles, KeyRound } from 'lucide-react';
import { api } from '../services/api';

export default function Login({ onAuthSuccess, onShowToast }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      if (isRegister) {
        if (!name.trim()) throw new Error('Please enter your full name.');
        const res = await api.register(name, email, password);
        onShowToast(`Welcome, ${res.user.name}! Account created.`, 'success');
        onAuthSuccess(res.user);
      } else {
        const res = await api.login(email, password);
        onShowToast(`Welcome back, ${res.user.name}!`, 'success');
        onAuthSuccess(res.user);
      }
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoFill = () => {
    setName('Yuvaraj Agency');
    setEmail('yuvaraj@agency.com');
    setPassword('password123');
    onShowToast('Demo credentials filled! Click Sign In to continue.', 'info');
  };

  return (
    <div style={{ maxWidth: 440, width: '100%', margin: '30px auto 20px auto', display: 'flex', flexDirection: 'column', gap: 20, padding: '0 16px' }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div
          className="logo-icon"
          style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', fontSize: 22, boxShadow: '0 8px 24px var(--primary-glow)' }}
        >
          <Target size={26} />
        </div>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            AI Client Finder
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.4 }}>
            Identify high-probability business leads from verified directories with automated opportunity scoring.
          </p>
        </div>
      </div>

      {/* Auth Card */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          padding: '22px',
          boxShadow: 'var(--shadow-lg)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, #6366f1, #06b6d4)' }} />

        {/* Segmented Switch */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            background: 'var(--bg-elevated)',
            padding: 3,
            borderRadius: 'var(--radius-sm)',
            marginBottom: 18,
            border: '1px solid var(--border-subtle)',
          }}
        >
          <button
            type="button"
            className={`btn btn-sm ${!isRegister ? 'btn-primary' : 'btn-ghost'}`}
            style={{ borderRadius: 'var(--radius-xs)', height: 32, fontSize: '12px' }}
            onClick={() => setIsRegister(false)}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`btn btn-sm ${isRegister ? 'btn-primary' : 'btn-ghost'}`}
            style={{ borderRadius: 'var(--radius-xs)', height: 32, fontSize: '12px' }}
            onClick={() => setIsRegister(true)}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {isRegister && (
            <div className="form-group">
              <label className="form-label">Full Name or Agency Name</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '34px' }}
                  placeholder="e.g. Apex Digital Studios"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
                <User size={15} style={{ position: 'absolute', left: 11, top: 12, color: 'var(--text-muted)' }} />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                className="form-input"
                style={{ paddingLeft: '34px' }}
                placeholder="you@agency.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Mail size={15} style={{ position: 'absolute', left: 11, top: 12, color: 'var(--text-muted)' }} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '34px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
              <Lock size={15} style={{ position: 'absolute', left: 11, top: 12, color: 'var(--text-muted)' }} />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: 6, height: 42, fontSize: '14px' }}
            disabled={isLoading}
          >
            {isLoading ? (
              <span>Authenticating Securely...</span>
            ) : (
              <>
                <span>{isRegister ? 'Register & Access Leads' : 'Sign In to Workspace'}</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        {/* Demo Fill Bar */}
        <div
          style={{
            marginTop: 18,
            paddingTop: 14,
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Testing local backend?</span>
          <button
            type="button"
            onClick={handleDemoFill}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: '11px', padding: '4px 9px', color: 'var(--accent-cyan)' }}
          >
            <Sparkles size={12} />
            <span>Fill Demo Account</span>
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: '11px', color: 'var(--text-muted)' }}>
        <ShieldCheck size={14} color="var(--accent-emerald)" />
        <span>JWT Bearer Authenticated • Ethical Public Data Engine</span>
      </div>
    </div>
  );
}
