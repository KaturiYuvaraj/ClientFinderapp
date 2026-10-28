import React, { useState, useEffect, useMemo } from 'react';
import {
  Search, Download, Trash2, Eye, Mail, Phone, Globe,
  Calendar, Star, Filter, Sparkles, X, PlusCircle
} from 'lucide-react';
import { api } from '../services/api';

const STATUS_FILTERS = ['All', 'New', 'Contacted', 'Interested', 'Follow-up', 'Converted', 'Not Interested'];

export default function Leads({
  onViewDetails,
  onGenerateMessage,
  onShowToast,
  refreshTrigger
}) {
  const [leads, setLeads] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('All');
  const [minScoreFilter, setMinScoreFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  const fetchLeads = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSavedLeads({
        status: statusFilter,
        minScore: minScoreFilter || null,
        search: searchQuery.trim() || null,
      });
      setLeads(data);
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [statusFilter, minScoreFilter, refreshTrigger]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchLeads();
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    fetchLeads();
  };

  const handleStatusChange = async (leadId, newStatus) => {
    try {
      await api.updateLead(leadId, { status: newStatus });
      setLeads(leads.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
      onShowToast(`Pipeline status changed to "${newStatus}"`, 'success');
    } catch (err) {
      onShowToast(err.message, 'error');
    }
  };

  const handleDelete = async (leadId, name) => {
    if (!window.confirm(`Remove "${name}" from your CRM leads?`)) {
      return;
    }
    try {
      await api.deleteLead(leadId);
      setLeads(leads.filter((l) => l.id !== leadId));
      onShowToast(`Lead removed.`, 'info');
    } catch (err) {
      onShowToast(err.message, 'error');
    }
  };

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      await api.downloadExportCsv({ status: statusFilter });
      onShowToast('CSV file exported successfully!', 'success');
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsExporting(false);
    }
  };

  const getStatusBadge = (st) => {
    switch (st) {
      case 'New': return 'badge-new';
      case 'Contacted': return 'badge-contacted';
      case 'Interested': return 'badge-interested';
      case 'Follow-up':
      case 'Follow Up':
        return 'badge-follow-up';
      case 'Converted': return 'badge-converted';
      default: return 'badge-not-interested';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Top Search & Actions Bar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <form onSubmit={handleSearchSubmit} style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '36px', paddingRight: searchQuery ? '32px' : '12px', height: '38px' }}
              placeholder="Search leads by name, phone, city, notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Search size={15} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                style={{
                  position: 'absolute',
                  right: 10,
                  top: 10,
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                <X size={14} />
              </button>
            )}
          </form>

          <button
            type="button"
            onClick={handleExportCsv}
            className="btn btn-secondary btn-sm"
            style={{ height: '38px', whiteSpace: 'nowrap', padding: '0 14px' }}
            disabled={isExporting || leads.length === 0}
            title="Download CSV spreadsheet"
          >
            <Download size={14} />
            <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
          </button>
        </div>

        {/* Status Filter Tabs */}
        <div className="nav-tabs" style={{ background: 'var(--bg-card)', padding: '3px' }}>
          {STATUS_FILTERS.map((st) => (
            <button
              key={st}
              type="button"
              className={`nav-tab ${statusFilter === st ? 'active' : ''}`}
              style={{ fontSize: '11px', padding: '5px 10px' }}
              onClick={() => setStatusFilter(st)}
            >
              <span>{st}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Leads List Area */}
      {isLoading ? (
        <div className="lead-cards-container">
          {[1, 2, 3].map((n) => (
            <div key={n} className="lead-card" style={{ gap: 10 }}>
              <div className="skeleton" style={{ height: 20, width: '45%' }} />
              <div className="skeleton" style={{ height: 14, width: '60%' }} />
              <div className="skeleton" style={{ height: 36, width: '100%' }} />
            </div>
          ))}
        </div>
      ) : leads.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Filter size={24} />
          </div>
          <h4 style={{ color: 'var(--text-primary)', fontSize: '15px' }}>No Leads Found</h4>
          <p style={{ fontSize: '12px', maxWidth: '300px' }}>
            {statusFilter !== 'All'
              ? `No saved leads found with status "${statusFilter}".`
              : 'You have not saved any leads to your CRM yet. Head to "Find Clients" to discover business leads.'}
          </p>
        </div>
      ) : (
        <div className="lead-cards-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', padding: '0 2px' }}>
            <span><strong>{leads.length}</strong> leads tracked in view</span>
            <span>Click status badge to update pipeline</span>
          </div>

          {leads.map((lead) => (
            <div key={lead.id} className="lead-card" style={{ padding: '14px' }}>
              <div className="lead-card-header">
                <div className="lead-title-area">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <h3 className="lead-name" style={{ fontSize: '15px' }}>
                      {lead.business_name}
                    </h3>
                    <select
                      className={`status-badge ${getStatusBadge(lead.status)}`}
                      style={{ border: 'none', cursor: 'pointer', outline: 'none', padding: '2px 8px' }}
                      value={lead.status}
                      onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                    >
                      {STATUS_FILTERS.filter((s) => s !== 'All').map((st) => (
                        <option key={st} value={st} style={{ background: 'var(--bg-card)', color: 'var(--text-primary)' }}>
                          {st}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="lead-submeta" style={{ fontSize: '12px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{lead.category}</span>
                    <span>•</span>
                    <span>{lead.city}</span>
                    <span>•</span>
                    <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{lead.service}</span>
                  </div>
                </div>

                <div
                  className={`lead-score-pill ${lead.lead_score >= 85 ? 'score-high' : 'score-good'}`}
                  style={{ padding: '3px 8px', fontSize: '12px' }}
                >
                  <span>{lead.lead_score}</span>
                  <span className="score-label">/ 100</span>
                </div>
              </div>

              {/* Contact Chips */}
              <div className="chips-row">
                {lead.phone ? (
                  <a href={`tel:${lead.phone}`} className="chip" style={{ fontSize: '11px', textDecoration: 'none', borderColor: 'var(--accent-emerald)', color: 'var(--accent-emerald)' }}>
                    <Phone size={11} />
                    <span>✓ Phone: {lead.phone}</span>
                  </a>
                ) : (
                  <span className="chip" style={{ fontSize: '11px', color: 'var(--text-muted)', borderStyle: 'dashed' }}>
                    <Phone size={11} /> No phone listed
                  </span>
                )}
                {lead.website ? (
                  <a
                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="chip chip-website-ok"
                    style={{ fontSize: '11px' }}
                  >
                    <Globe size={11} />
                    <span>✓ Website: {lead.website.replace(/^https?:\/\/(www\.)?/, '').slice(0, 24)}</span>
                  </a>
                ) : (
                  <span className="chip chip-website-none" style={{ fontSize: '11px', color: 'var(--accent-amber)', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
                    <Globe size={11} /> ❌ No website (Opportunity!)
                  </span>
                )}
                {lead.follow_up_date && (
                  <span className="chip" style={{ fontSize: '11px', color: 'var(--accent-amber)', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
                    <Calendar size={11} /> Next: {String(lead.follow_up_date).slice(0, 10)}
                  </span>
                )}
              </div>

              {/* Notes Preview if present */}
              {lead.notes && (
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--text-secondary)',
                    fontStyle: 'italic',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: '2px solid var(--primary)',
                  }}
                >
                  "{lead.notes.slice(0, 120)}{lead.notes.length > 120 ? '...' : ''}"
                </div>
              )}

              {/* Action Buttons */}
              <div className="card-actions" style={{ marginTop: 0, paddingTop: 10 }}>
                <button
                  type="button"
                  onClick={() => onViewDetails(lead)}
                  className="btn btn-secondary btn-sm"
                >
                  <Eye size={12} />
                  <span>Inspect & Notes</span>
                </button>

                <button
                  type="button"
                  onClick={() => onGenerateMessage(lead)}
                  className="btn btn-secondary btn-sm"
                  style={{ color: 'var(--accent-cyan)' }}
                >
                  <Mail size={12} />
                  <span>Generate Pitch</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDelete(lead.id, lead.business_name)}
                  className="btn btn-ghost btn-icon"
                  style={{ color: 'var(--accent-rose)' }}
                  title="Remove from CRM"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
