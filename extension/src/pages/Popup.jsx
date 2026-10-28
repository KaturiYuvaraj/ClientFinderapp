import React, { useState, useEffect } from 'react';
import SearchForm from '../components/SearchForm';
import LeadList from '../components/LeadList';
import { api } from '../services/api';
import { History, Sparkles, Clock } from 'lucide-react';

export default function Popup({
  onSaveLead,
  onViewDetails,
  onGenerateMessage,
  onShowToast,
  savingLeadId,
}) {
  const [searchResults, setSearchResults] = useState([]);
  const [currentService, setCurrentService] = useState('Website Development');
  const [isLoading, setIsLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [initialFormValues, setInitialFormValues] = useState(null);

  const fetchHistory = async () => {
    try {
      const history = await api.getSearchHistory();
      setSearchHistory(history.slice(0, 5));
    } catch (err) {
      // Non-blocking
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSearch = async (params) => {
    setIsLoading(true);
    setCurrentService(params.service);
    try {
      const res = await api.searchBusinesses(params);
      setSearchResults(res.results || []);
      onShowToast(`Discovered ${res.total} potential clients in ${params.location}!`, 'success');
      fetchHistory();
    } catch (err) {
      onShowToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRepeatSearch = (item) => {
    setInitialFormValues({
      service: item.service,
      category: item.category,
      location: item.location,
      radius: item.radius,
      keywords: item.keywords || '',
    });
    handleSearch({
      service: item.service,
      category: item.category,
      location: item.location,
      radius: item.radius,
      keywords: item.keywords || null,
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Search Input Card */}
      <SearchForm
        onSearch={handleSearch}
        isLoading={isLoading}
        initialValues={initialFormValues}
      />

      {/* Previous Search History Quick Pills */}
      {searchHistory.length > 0 && (
        <div
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <Clock size={12} color="var(--accent-cyan)" />
            <span>Recent Queries:</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {searchHistory.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleRepeatSearch(item)}
                className="chip"
                style={{ cursor: 'pointer', background: 'var(--bg-elevated)', fontSize: '11px', padding: '3px 8px' }}
                title={`Repeat query: ${item.service} for ${item.category} in ${item.location}`}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.category}</span>
                <span style={{ opacity: 0.5, fontSize: '10px' }}>in</span>
                <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{item.location}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Discovered Leads List */}
      <LeadList
        leads={searchResults}
        isLoading={isLoading}
        service={currentService}
        onSaveLead={onSaveLead}
        onViewDetails={onViewDetails}
        onGenerateMessage={onGenerateMessage}
        savingLeadId={savingLeadId}
      />
    </div>
  );
}
