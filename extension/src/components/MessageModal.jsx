import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Sparkles, RefreshCw, Send, SlidersHorizontal, MessageSquare } from 'lucide-react';
import { api } from '../services/api';

const TONES = [
  { id: 'professional', label: '💼 Professional' },
  { id: 'friendly', label: '🤝 Friendly & Warm' },
  { id: 'direct', label: '⚡ Direct & Value-First' },
];

export default function MessageModal({ lead, service, user, onClose, onShowToast }) {
  if (!lead) return null;

  const [message, setMessage] = useState('');
  const [selectedTone, setSelectedTone] = useState('professional');
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const fetchMessage = async (tone = selectedTone) => {
    setIsLoading(true);
    setCopied(false);
    try {
      const res = await api.generateMessage({
        business_name: lead.name || lead.business_name,
        category: lead.category,
        location: lead.city,
        service: lead.service || service || 'Digital Services',
        opportunity_reason: lead.opportunity_reason,
        verified_facts: lead.verified_facts || [],
        sender_name: user?.name,
        lead_id: lead.id || null,
      });

      let tailoredMessage = res.message;
      if (tone === 'friendly') {
        tailoredMessage = tailoredMessage
          .replace(/^Dear\s+/i, 'Hi ')
          .replace(/^To the management of\s+/i, 'Hello team at ');
      } else if (tone === 'direct') {
        tailoredMessage = tailoredMessage
          .replace(/^Dear\s+/i, 'Hey ')
          .replace(/I hope this message finds you well\.\s*/i, '');
      }

      setMessage(tailoredMessage);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMessage(selectedTone);
  }, [lead]);

  const handleToneChange = (toneId) => {
    setSelectedTone(toneId);
    fetchMessage(toneId);
  };

  const handleCopy = () => {
    if (!message) return;
    navigator.clipboard.writeText(message);
    setCopied(true);
    onShowToast('Outreach message copied to clipboard!', 'success');
    setTimeout(() => setCopied(false), 2500);
  };

  const wordCount = message.trim() ? message.trim().split(/\s+/).length : 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="logo-icon" style={{ width: 28, height: 28 }}>
              <Sparkles size={15} />
            </div>
            <div>
              <h3 className="modal-title">Personalized Outreach Message</h3>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Target: {lead.name || lead.business_name} • {lead.category}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost btn-icon" aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Tone Selector */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Outreach Tone
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {wordCount} words
              </span>
            </div>
            <div className="preset-pills-row">
              {TONES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={`preset-pill ${selectedTone === t.id ? 'active' : ''}`}
                  onClick={() => handleToneChange(t.id)}
                  disabled={isLoading}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            {isLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '36px 0', alignItems: 'center', justifyContent: 'center' }}>
                <span className="spin" style={{ fontSize: 24 }}>✨</span>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Synthesizing personalized message grounded in verified signals...</span>
              </div>
            ) : (
              <textarea
                className="form-textarea"
                style={{
                  minHeight: '200px',
                  lineHeight: '1.55',
                  fontFamily: 'var(--font-main)',
                  fontSize: '13px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px',
                }}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Drafting tailored outreach message..."
              />
            )}
          </div>

          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px dashed var(--border-medium)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <MessageSquare size={13} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
            <span>
              <strong>Professional Tip:</strong> Review and tailor the greeting and closing before dispatching. Always send genuine, individual messages.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button
            type="button"
            onClick={() => fetchMessage(selectedTone)}
            className="btn btn-ghost btn-sm"
            disabled={isLoading}
          >
            <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
            <span>Regenerate</span>
          </button>

          <button
            type="button"
            onClick={handleCopy}
            className="btn btn-primary btn-sm"
            disabled={isLoading || !message}
            style={{ minWidth: 120 }}
          >
            {copied ? (
              <>
                <Check size={14} color="#86efac" />
                <span style={{ color: '#ffffff', fontWeight: 600 }}>Copied!</span>
              </>
            ) : (
              <>
                <Copy size={13} />
                <span>Copy Message</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
