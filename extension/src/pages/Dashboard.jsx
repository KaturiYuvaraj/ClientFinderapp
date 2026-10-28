import React, { useState, useEffect } from 'react';
import StatsCards from '../components/StatsCards';
import { api } from '../services/api';
import { Sparkles, ArrowRight, Eye, Mail, Star, MapPin, Layers, Building2 } from 'lucide-react';

export default function Dashboard({
  onNavigate,
  onViewDetails,
  onGenerateMessage,
  onShowToast,
  refreshTrigger,
}) {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [refreshTrigger]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="stats-grid">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="stat-card" style={{ gap: 8 }}>
              <div className="skeleton" style={{ height: 12, width: '50%' }} />
              <div className="skeleton" style={{ height: 26, width: '35%' }} />
              <div className="skeleton" style={{ height: 10, width: '70%' }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Top Metrics Cards & Pipeline Funnel */}
      <StatsCards stats={stats} />

      {/* Services Breakdown */}
      {stats?.service_distribution && stats.service_distribution.length > 0 && (
        <div
          style={{
            background: 'var(--bg-card)',
            padding: '16px',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-medium)',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <Layers size={14} color="var(--accent-cyan)" />
            <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Service Opportunities Distribution
            </h4>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {stats.service_distribution.map((s, idx) => (
              <div
                key={idx}
                className="chip"
                style={{
                  fontSize: '12px',
                  padding: '5px 12px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.service}</span>
                <span
                  style={{
                    background: 'rgba(6, 182, 212, 0.15)',
                    padding: '2px 7px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '11px',
                    color: 'var(--accent-cyan)',
                    fontWeight: 700,
                  }}
                >
                  {s.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Priority Opportunities */}
      <div
        style={{
          background: 'var(--bg-card)',
          padding: '16px',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-medium)',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={15} color="var(--accent-emerald)" />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Top Priority Opportunities
            </h4>
          </div>
          <button
            onClick={() => onNavigate('leads')}
            className="btn btn-ghost btn-sm"
            style={{ color: 'var(--accent-cyan)', fontSize: '12px', gap: 4 }}
          >
            <span>View All Leads</span>
            <ArrowRight size={13} />
          </button>
        </div>

        {stats?.recent_high_opportunity && stats.recent_high_opportunity.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {stats.recent_high_opportunity.map((item) => (
              <div
                key={item.id}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  padding: '11px 14px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'border-color 0.15s ease',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.business_name}
                    </span>
                    <span className="badge-new status-badge">{item.status}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: 3 }}>
                    {item.category} • {item.city} • <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{item.opportunity_type}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    className={`lead-score-pill ${item.lead_score >= 85 ? 'score-high' : 'score-good'}`}
                    style={{ padding: '3px 8px', fontSize: '12px' }}
                  >
                    {item.lead_score}
                  </span>
                  <button
                    onClick={() => onViewDetails(item)}
                    className="btn btn-secondary btn-sm"
                    title="Inspect details"
                  >
                    <Eye size={12} />
                    <span>Inspect</span>
                  </button>
                  <button
                    onClick={() => onGenerateMessage(item)}
                    className="btn btn-primary btn-sm"
                    title="Outreach message"
                  >
                    <Mail size={12} />
                    <span>Outreach</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '28px 16px' }}>
            <Building2 size={24} color="var(--text-muted)" />
            <p style={{ fontSize: '12px', maxWidth: '320px', margin: 0 }}>
              No saved opportunities yet. Switch to <strong>Find Clients</strong> to discover and save high-potential leads!
            </p>
            <button
              onClick={() => onNavigate('find')}
              className="btn btn-primary btn-sm"
              style={{ marginTop: 6 }}
            >
              <Sparkles size={13} />
              <span>Discover Clients Now</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
