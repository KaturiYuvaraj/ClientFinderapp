import React, { useState } from 'react';
import {
  Star, Phone, Globe, Bookmark, BookmarkCheck,
  Mail, Eye, ChevronDown, ChevronUp, MapPin, Sparkles,
  ShieldCheck, Cpu, AlertTriangle
} from 'lucide-react';

export default function LeadCard({
  lead,
  service,
  onSaveLead,
  onViewDetails,
  onGenerateMessage,
  isSaving
}) {
  const [showAnalysis, setShowAnalysis] = useState(false);

  const getScoreInfo = (score) => {
    if (score >= 90) return { cls: 'score-high', label: 'High Match' };
    if (score >= 75) return { cls: 'score-good', label: 'Strong' };
    if (score >= 50) return { cls: 'score-moderate', label: 'Moderate' };
    return { cls: 'score-low', label: 'Low Match' };
  };

  const score = lead.lead_score || 0;
  const { cls: scoreClass, label: scoreLabel } = getScoreInfo(score);
  const isSaved = lead.is_saved || Boolean(lead.id);

  return (
    <div className="lead-card">
      {/* Header with Title & Lead Score */}
      <div className="lead-card-header">
        <div className="lead-title-area">
          <h3 className="lead-name">{lead.name || lead.business_name}</h3>
          <div className="lead-submeta">
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {lead.category || 'Local Business'}
            </span>
            <span>•</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
              <MapPin size={11} color="var(--accent-emerald)" /> {lead.city || 'Local Area'}
            </span>
            {lead.rating > 0 && (
              <>
                <span>•</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, color: '#d97706', fontWeight: 600 }}>
                  <Star size={11} fill="#f59e0b" strokeWidth={0} /> {lead.rating.toFixed(1)}
                  <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({lead.review_count})</span>
                </span>
              </>
            )}
          </div>
        </div>

        {/* Lead Score Pill */}
        <div className={`lead-score-pill ${scoreClass}`} title={`Confidence: ${lead.confidence || 'Moderate'}`}>
          <span>{score}</span>
          <span className="score-label">{scoreLabel}</span>
        </div>
      </div>

      {/* Public Contact & Presence Chips */}
      <div className="chips-row">
        {lead.phone ? (
          <a
            href={`tel:${lead.phone}`}
            className="chip"
            title="Click to call public number"
            style={{ textDecoration: 'none' }}
          >
            <Phone size={11} color="var(--accent-emerald)" />
            <span>{lead.phone}</span>
          </a>
        ) : (
          <span className="chip" style={{ opacity: 0.55 }}>
            <Phone size={11} /> No phone listed
          </span>
        )}

        {lead.website ? (
          <a
            href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
            target="_blank"
            rel="noopener noreferrer"
            className="chip chip-website-ok"
            title="Open verified website"
          >
            <Globe size={11} />
            <span>{lead.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '').slice(0, 24)}</span>
          </a>
        ) : (
          <span className="chip chip-website-none" title="High opportunity: Business has no web presence">
            <AlertTriangle size={11} />
            <span>No Website Listed (Opportunity)</span>
          </span>
        )}
      </div>

      {/* Opportunity Analysis Box */}
      <div className="opportunity-box">
        <div className="opportunity-title">
          <Sparkles size={13} color="var(--primary)" />
          <span>Opportunity: {lead.opportunity_type || service}</span>
        </div>
        <p className="opportunity-desc">
          {lead.opportunity_reason || 'Service gap identified based on verified directory records.'}
        </p>

        {/* Expandable Facts vs Inference */}
        <button
          type="button"
          onClick={() => setShowAnalysis(!showAnalysis)}
          className="btn btn-ghost btn-sm"
          style={{ padding: '3px 0', fontSize: '11px', alignSelf: 'flex-start', color: 'var(--accent-cyan)' }}
        >
          {showAnalysis ? (
            <>
              <ChevronUp size={12} /> Hide Verified Facts & Reasoning
            </>
          ) : (
            <>
              <ChevronDown size={12} /> View Facts vs AI Inferences ({lead.verified_facts?.length || 0} facts)
            </>
          )}
        </button>

        {showAnalysis && (
          <div className="fact-inference-box">
            <div style={{ fontWeight: 700, color: 'var(--accent-emerald)', fontSize: '10px', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 4 }}>
              <ShieldCheck size={11} /> Verified Facts:
            </div>
            {lead.verified_facts && lead.verified_facts.length > 0 ? (
              lead.verified_facts.map((fact, idx) => (
                <div key={idx} className="fact-item">{fact}</div>
              ))
            ) : (
              <div className="fact-item">Registered business entry located in directory</div>
            )}

            <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '10px', textTransform: 'uppercase', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Cpu size={11} /> AI Opportunity Inferences:
            </div>
            {lead.inferences && lead.inferences.length > 0 ? (
              lead.inferences.map((inf, idx) => (
                <div key={idx} className="inference-item">{inf}</div>
              ))
            ) : (
              <div className="inference-item">Service gap identified from public presence</div>
            )}
          </div>
        )}
      </div>

      {/* Card Action Buttons */}
      <div className="card-actions">
        <button
          type="button"
          onClick={() => onViewDetails(lead)}
          className="btn btn-secondary btn-sm"
          title="Inspect full business details"
        >
          <Eye size={13} />
          <span>Inspect</span>
        </button>

        <button
          type="button"
          onClick={() => onGenerateMessage(lead)}
          className="btn btn-secondary btn-sm"
          title="Generate AI outreach pitch"
          style={{ color: 'var(--accent-cyan)' }}
        >
          <Mail size={13} />
          <span>Outreach Message</span>
        </button>

        <button
          type="button"
          onClick={() => onSaveLead(lead)}
          className={`btn btn-sm ${isSaved ? 'btn-ghost' : 'btn-primary'}`}
          disabled={isSaving || isSaved}
          title={isSaved ? 'Saved to CRM' : 'Save to your lead pipeline'}
        >
          {isSaved ? (
            <>
              <BookmarkCheck size={13} color="var(--accent-emerald)" />
              <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>Saved</span>
            </>
          ) : (
            <>
              <Bookmark size={13} />
              <span>Save Lead</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
