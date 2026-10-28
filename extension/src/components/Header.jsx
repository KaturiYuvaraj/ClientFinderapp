import React, { useState, useEffect } from 'react';
import {
  Target, ExternalLink, LogOut, User, Sparkles,
  LayoutDashboard, BookmarkCheck, Settings as SettingsIcon,
  Activity
} from 'lucide-react';
import { api } from '../services/api';

export default function Header({ activeTab, setActiveTab, user, onLogout }) {
  const [isBackendOnline, setIsBackendOnline] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.checkHealth()
      .then(() => {
        if (mounted) setIsBackendOnline(true);
      })
      .catch(() => {
        if (mounted) setIsBackendOnline(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleOpenFullTab = () => {
    if (typeof chrome !== 'undefined' && chrome.tabs && chrome.runtime) {
      chrome.tabs.create({ url: chrome.runtime.getURL('index.html') });
    } else {
      window.open(window.location.href, '_blank');
    }
  };

  const tabs = [
    { id: 'find', label: 'Find Clients', icon: Sparkles },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'leads', label: 'Saved Leads', icon: BookmarkCheck },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <header className="app-header">
      <div className="header-top">
        <div className="logo-badge">
          <div className="logo-icon">
            <Target size={17} />
          </div>
          <div className="logo-title-wrap">
            <span className="logo-title">AI Client Finder</span>
            <span className="logo-subtitle">Opportunity Intelligence</span>
          </div>
        </div>

        <div className="header-actions">
          {/* Backend Status Ping */}
          <div
            className="status-pill-online"
            title={isBackendOnline ? 'FastAPI Backend is operational' : 'Backend offline'}
            style={!isBackendOnline ? { background: 'rgba(225, 29, 72, 0.08)', borderColor: 'rgba(225, 29, 72, 0.22)', color: '#e11d48' } : {}}
          >
            <span
              className="pulse-dot"
              style={!isBackendOnline ? { background: '#e11d48', boxShadow: '0 0 6px #e11d48' } : {}}
            />
            <span>{isBackendOnline ? 'Live Engine' : 'Offline'}</span>
          </div>

          {user && (
            <div className="chip" title={`Signed in as ${user.email}`} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-medium)' }}>
              <User size={12} color="var(--primary)" />
              <span style={{ fontWeight: 600 }}>{user.name.split(' ')[0]}</span>
            </div>
          )}

          <button
            onClick={handleOpenFullTab}
            className="btn btn-ghost btn-icon"
            title="Open in Full Browser Tab"
            aria-label="Open Full Tab"
          >
            <ExternalLink size={15} />
          </button>

          {user && (
            <button
              onClick={onLogout}
              className="btn btn-ghost btn-icon"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut size={15} />
            </button>
          )}
        </div>
      </div>

      <nav className="nav-tabs" aria-label="Main Navigation">
        {tabs.map((tab) => {
          const IconComponent = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <IconComponent size={13} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
