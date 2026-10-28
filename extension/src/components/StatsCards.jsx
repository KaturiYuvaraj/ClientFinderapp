import React from 'react';
import { Users, UserPlus, PhoneCall, Heart, CheckCircle2, TrendingUp, Sparkles, Filter } from 'lucide-react';

export default function StatsCards({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      title: 'Total In Pipeline',
      value: stats.total_leads || 0,
      sub: `${stats.high_opportunity_leads || 0} high opportunity`,
      icon: Users,
      color: '#4f46e5',
      bg: 'rgba(79, 70, 229, 0.08)',
    },
    {
      title: 'New Leads',
      value: stats.new_leads || 0,
      sub: 'Awaiting outreach',
      icon: UserPlus,
      color: '#6366f1',
      bg: 'rgba(99, 102, 241, 0.08)',
    },
    {
      title: 'Contacted',
      value: stats.contacted || 0,
      sub: 'Pitch dispatched',
      icon: PhoneCall,
      color: '#0284c7',
      bg: 'rgba(2, 132, 199, 0.08)',
    },
    {
      title: 'Interested',
      value: stats.interested || 0,
      sub: 'In discussions',
      icon: Heart,
      color: '#d97706',
      bg: 'rgba(217, 119, 6, 0.08)',
    },
    {
      title: 'Converted',
      value: stats.converted || 0,
      sub: `${stats.conversion_rate || 0}% close rate`,
      icon: CheckCircle2,
      color: '#059669',
      bg: 'rgba(5, 150, 105, 0.08)',
    },
    {
      title: 'Avg Match Score',
      value: `${stats.avg_lead_score || 0}`,
      sub: 'AI confidence index',
      icon: TrendingUp,
      color: '#0284c7',
      bg: 'rgba(2, 132, 199, 0.08)',
    },
  ];

  const total = stats.total_leads || 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Metrics Grid */}
      <div className="stats-grid">
        {cards.map((card, idx) => {
          const IconComponent = card.icon;
          return (
            <div key={idx} className="stat-card">
              <div className="stat-header">
                <span className="stat-title">{card.title}</span>
                <div className="stat-icon-wrap" style={{ background: card.bg }}>
                  <IconComponent size={14} color={card.color} />
                </div>
              </div>
              <div className="stat-value" style={{ color: card.color }}>
                {card.value}
              </div>
              <span className="stat-sub">{card.sub}</span>
            </div>
          );
        })}
      </div>

      {/* Visual Pipeline Funnel */}
      {stats.total_leads > 0 && (
        <div
          style={{
            background: 'var(--bg-card)',
            padding: '14px 16px',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-medium)',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
              <Filter size={13} color="var(--primary)" />
              <span>Conversion Funnel</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              {stats.total_leads} Active Leads Tracked
            </span>
          </div>

          <div
            style={{
              height: '8px',
              width: '100%',
              borderRadius: 'var(--radius-full)',
              overflow: 'hidden',
              display: 'flex',
              background: 'var(--bg-elevated)',
              gap: '2px',
            }}
          >
            {stats.status_distribution?.map((item) => {
              const widthPct = (item.count / total) * 100;
              if (widthPct === 0) return null;
              return (
                <div
                  key={item.status}
                  style={{
                    width: `${widthPct}%`,
                    background: item.color,
                    transition: 'width 0.4s ease',
                  }}
                  title={`${item.status}: ${item.count} (${widthPct.toFixed(1)}%)`}
                />
              );
            })}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 10 }}>
            {stats.status_distribution?.map((item) => (
              <div key={item.status} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '11px', color: 'var(--text-secondary)' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: item.color }} />
                <span><strong>{item.status}</strong>: {item.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
