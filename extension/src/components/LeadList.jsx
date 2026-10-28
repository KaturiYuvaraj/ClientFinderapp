import React from 'react';
import LeadCard from './LeadCard';
import { SearchX, Sparkles } from 'lucide-react';

export default function LeadList({
  leads,
  isLoading,
  service,
  onSaveLead,
  onViewDetails,
  onGenerateMessage,
  savingLeadId
}) {
  if (isLoading) {
    return (
      <div className="lead-cards-container">
        {[1, 2, 3].map((n) => (
          <div key={n} className="lead-card" style={{ gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div style={{ width: '60%' }}>
                <div className="skeleton" style={{ height: 18, width: '80%', marginBottom: 6 }} />
                <div className="skeleton" style={{ height: 12, width: '50%' }} />
              </div>
              <div className="skeleton" style={{ height: 32, width: 48, borderRadius: 8 }} />
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <div className="skeleton" style={{ height: 22, width: 110 }} />
              <div className="skeleton" style={{ height: 22, width: 140 }} />
            </div>
            <div className="skeleton" style={{ height: 48, width: '100%', borderRadius: 8 }} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <div className="skeleton" style={{ height: 28, width: 90 }} />
              <div className="skeleton" style={{ height: 28, width: 120 }} />
              <div className="skeleton" style={{ height: 28, width: 80 }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <Sparkles />
        </div>
        <h4 style={{ color: 'var(--text-primary)', fontSize: '15px' }}>Discover Business Clients</h4>
        <p style={{ fontSize: '12px', maxWidth: '300px' }}>
          Select your service and target city above, then click <strong>Find Clients</strong> to uncover verified opportunities.
        </p>
      </div>
    );
  }

  return (
    <div className="lead-cards-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 2px' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Discovered Opportunities ({leads.length})
        </span>
        <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 600 }}>
          Sorted by AI Score
        </span>
      </div>

      {leads.map((lead, idx) => {
        const leadKey = lead.provider_id || lead.id || lead.name || lead.business_name;
        return (
          <LeadCard
            key={leadKey || idx}
            lead={lead}
            service={service}
            onSaveLead={onSaveLead}
            onViewDetails={onViewDetails}
            onGenerateMessage={onGenerateMessage}
            isSaving={Boolean(savingLeadId && savingLeadId === leadKey)}
          />
        );
      })}
    </div>
  );
}
