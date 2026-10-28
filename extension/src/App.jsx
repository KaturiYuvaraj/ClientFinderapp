import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Toast from './components/Toast';
import LeadDetailModal from './components/LeadDetailModal';
import MessageModal from './components/MessageModal';
import Popup from './pages/Popup';
import Dashboard from './pages/Dashboard';
import Leads from './pages/Leads';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { api } from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [activeTab, setActiveTab] = useState('find'); // find, dashboard, leads, settings
  const [toasts, setToasts] = useState([]);
  const [selectedLeadForDetail, setSelectedLeadForDetail] = useState(null);
  const [selectedLeadForMessage, setSelectedLeadForMessage] = useState(null);
  const [savingLeadId, setSavingLeadId] = useState(null);
  const [refreshLeadsTrigger, setRefreshLeadsTrigger] = useState(0);

  // Toast Helper
  const showToast = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Check auth session on startup
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = await api.init();
        if (token) {
          const profile = await api.getMe();
          setUser(profile);
        }
      } catch (err) {
        setUser(null);
      } finally {
        setIsAuthChecking(false);
      }
    };

    checkAuth();

    const handleAuthExpired = () => {
      setUser(null);
      showToast('Session expired. Please sign in again.', 'info');
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, []);

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    showToast('Signed out successfully.', 'info');
  };

  const handleSaveLead = async (lead) => {
    const leadKey = lead.provider_id || lead.id || lead.name || lead.business_name;
    setSavingLeadId(leadKey);
    try {
      const saved = await api.saveLead({
        provider_id: lead.provider_id,
        business_name: lead.name || lead.business_name,
        category: lead.category,
        phone: lead.phone,
        website: lead.website,
        address: lead.address,
        city: lead.city,
        latitude: lead.latitude,
        longitude: lead.longitude,
        rating: lead.rating,
        review_count: lead.review_count,
        source: lead.source,
        source_url: lead.source_url,
        service: lead.service || lead.opportunity_type || 'Website Development',
        lead_score: lead.lead_score,
        opportunity_type: lead.opportunity_type,
        opportunity_reason: lead.opportunity_reason,
        confidence: lead.confidence,
        status: 'New',
      });
      lead.is_saved = true;
      lead.id = saved.id;
      showToast(`Saved "${saved.business_name}" to your leads!`, 'success');
      setRefreshLeadsTrigger((prev) => prev + 1);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setSavingLeadId(null);
    }
  };

  const handleUpdateLead = async (id, updateData) => {
    try {
      const updated = await api.updateLead(id, updateData);
      showToast('Lead updated successfully.', 'success');
      setRefreshLeadsTrigger((prev) => prev + 1);
      return updated;
    } catch (err) {
      showToast(err.message, 'error');
      throw err;
    }
  };

  if (isAuthChecking) {
    return (
      <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
        <div className="spinner" style={{ fontSize: 24 }}>⏳</div>
        <p style={{ marginTop: 10, fontSize: 12, color: 'var(--text-secondary)' }}>
          Loading AI Client Finder...
        </p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container">
        <Login onAuthSuccess={setUser} onShowToast={showToast} />
        <Toast toasts={toasts} onDismiss={dismissToast} />
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header with Navigation and Profile */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main Viewport */}
      <main className="app-main">
        {activeTab === 'find' && (
          <Popup
            onSaveLead={handleSaveLead}
            onViewDetails={setSelectedLeadForDetail}
            onGenerateMessage={setSelectedLeadForMessage}
            onShowToast={showToast}
            savingLeadId={savingLeadId}
          />
        )}

        {activeTab === 'dashboard' && (
          <Dashboard
            onNavigate={setActiveTab}
            onViewDetails={setSelectedLeadForDetail}
            onGenerateMessage={setSelectedLeadForMessage}
            onShowToast={showToast}
            refreshTrigger={refreshLeadsTrigger}
          />
        )}

        {activeTab === 'leads' && (
          <Leads
            onViewDetails={setSelectedLeadForDetail}
            onGenerateMessage={setSelectedLeadForMessage}
            onShowToast={showToast}
            refreshTrigger={refreshLeadsTrigger}
          />
        )}

        {activeTab === 'settings' && (
          <Settings
            user={user}
            onLogout={handleLogout}
            onShowToast={showToast}
          />
        )}
      </main>

      {/* Modals */}
      {selectedLeadForDetail && (
        <LeadDetailModal
          lead={selectedLeadForDetail}
          onClose={() => setSelectedLeadForDetail(null)}
          onUpdateLead={handleUpdateLead}
          onGenerateMessage={(l) => {
            setSelectedLeadForDetail(null);
            setSelectedLeadForMessage(l);
          }}
        />
      )}

      {selectedLeadForMessage && (
        <MessageModal
          lead={selectedLeadForMessage}
          service={selectedLeadForMessage.service || selectedLeadForMessage.opportunity_type}
          user={user}
          onClose={() => setSelectedLeadForMessage(null)}
          onShowToast={showToast}
        />
      )}

      {/* Toasts */}
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
