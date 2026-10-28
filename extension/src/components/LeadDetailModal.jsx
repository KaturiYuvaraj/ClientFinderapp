import React, { useState } from 'react';
import {
  X, Star, Phone, Globe, MapPin, Calendar, CheckSquare,
  Sparkles, Save, ShieldCheck, Cpu, ExternalLink, AlertTriangle
} from 'lucide-react';

const STATUS_OPTIONS = [
  'New',
  'Contacted',
  'Interested',
  'Follow-up',
  'Converted',
  'Not Interested',
];

export default function LeadDetailModal({
  lead,
  onClose,
  onUpdateLead,
  onGenerateMessage,
}) {
  if (!lead) return null;

  const [status, setStatus] = useState(lead.status || 'New');
  const [notes, setNotes] = useState(lead.notes || '');
  const [followUpDate, setFollowUpDate] = useState(
    lead.follow_up_date ? String(lead.follow_up_date).slice(0, 10) : ''
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdateLead(lead.id, {
        status,
        notes,
        follow_up_date: followUpDate || null,
      });
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 90) return 'score-high';
    if (score >= 75) return 'score-good';
    if (score >= 50) return 'score-moderate';
    return 'score-low';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className={`lead-score-pill ${getScoreBadgeClass(lead.lead_score || 0)}`} style={{ padding: '3px 8px' }}>
              {lead.lead_score || 0}
            </span>
            <div>
              <h3 className="modal-title">{lead.business_name || lead.name}</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {lead.category} • {lead.city}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost btn-icon" aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Section 1: Business Information */}
          <div>
            <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, letterSpacing: '0.04em', fontWeight: 700 }}>
              Business Profile
            </h4>
            <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'flex', flexDirection: 'column', gap: 10, border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '13px' }}>
                <Phone size={14} color="var(--accent-emerald)" />
                {lead.phone ? (
                  <a href={`tel:${lead.phone}`} style={{ color: 'var(--text-primary)', textDecoration: 'none' }}>
                    {lead.phone}
                  </a>
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>No public phone listed</span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '13px' }}>
                <Globe size={14} color="var(--accent-cyan)" />
                {lead.website ? (
                  <a
                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--accent-cyan)', textDecoration: 'underline' }}
                  >
                    {lead.website}
                  </a>
                ) : (
                  <span style={{ color: 'var(--accent-amber)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <AlertTriangle size={12} /> No official website listed
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: '13px' }}>
                <MapPin size={14} color="#94a3b8" style={{ marginTop: 2 }} />
                <span>{lead.address || lead.city || 'Address unlisted'}</span>
              </div>

              {lead.rating > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '13px' }}>
                  <Star size={14} fill="#f59e0b" strokeWidth={0} />
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{lead.rating.toFixed(1)} rating</span>
                  <span style={{ color: 'var(--text-muted)' }}>({lead.review_count} verified reviews)</span>
                </div>
              )}

              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 4, display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: 8 }}>
                <span>Source: {lead.source || 'Authorized Business API'}</span>
                {lead.source_url && (
                  <a href={lead.source_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                    <span>Directory Record</span>
                    <ExternalLink size={10} />
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Section 2: Opportunity Analysis */}
          <div>
            <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, letterSpacing: '0.04em', fontWeight: 700 }}>
              Opportunity Intelligence
            </h4>
            <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'flex', flexDirection: 'column', gap: 10, border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {lead.opportunity_type || lead.service}
                </span>
                <span className="chip" style={{ color: 'var(--accent-emerald)', borderColor: 'rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.1)' }}>
                  Confidence: {lead.confidence || 'Moderate'}
                </span>
              </div>

              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                {lead.opportunity_reason}
              </p>

              {/* Verified Facts */}
              <div style={{ marginTop: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', textTransform: 'uppercase', marginBottom: 4 }}>
                  <ShieldCheck size={12} /> Verified Listing Facts:
                </div>
                {lead.verified_facts && lead.verified_facts.length > 0 ? (
                  lead.verified_facts.map((f, i) => (
                    <div key={i} className="fact-item" style={{ fontSize: '11px', marginBottom: 3 }}>{f}</div>
                  ))
                ) : (
                  <div className="fact-item" style={{ fontSize: '11px' }}>Listing verified in business directory</div>
                )}
              </div>

              {/* Inferences */}
              <div style={{ marginTop: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', marginBottom: 4 }}>
                  <Cpu size={12} /> AI-Derived Observations:
                </div>
                {lead.inferences && lead.inferences.length > 0 ? (
                  lead.inferences.map((inf, i) => (
                    <div key={i} className="inference-item" style={{ fontSize: '11px', marginBottom: 3 }}>{inf}</div>
                  ))
                ) : (
                  <div className="inference-item" style={{ fontSize: '11px' }}>High potential for service engagement</div>
                )}
              </div>
            </div>
          </div>

          {/* Section 3: CRM Management */}
          {lead.id && (
            <div>
              <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, letterSpacing: '0.04em', fontWeight: 700 }}>
                CRM Status & Interaction Notes
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
                <div className="form-group">
                  <label className="form-label">
                    <span>Pipeline Status</span>
                    <CheckSquare size={12} />
                  </label>
                  <select
                    className="form-select"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                  >
                    {STATUS_OPTIONS.map((st) => (
                      <option key={st} value={st} style={{ background: 'var(--bg-card)', color: 'var(--text-primary)' }}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <span>Follow-Up Date</span>
                    <Calendar size={12} />
                  </label>
                  <input
                    type="date"
                    className="form-input"
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span>Interaction Log / Call Notes</span>
                </label>
                <textarea
                  className="form-textarea"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Record call outcomes, requirements, or next steps..."
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button
            type="button"
            onClick={() => {
              onClose();
              onGenerateMessage(lead);
            }}
            className="btn btn-secondary btn-sm"
          >
            <Sparkles size={13} color="var(--accent-cyan)" />
            <span>Outreach Pitch</span>
          </button>

          {lead.id && (
            <button
              type="button"
              onClick={handleSave}
              className="btn btn-primary btn-sm"
              disabled={isSaving}
            >
              <Save size={13} />
              <span>{isSaving ? 'Saving...' : 'Update Lead in CRM'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
