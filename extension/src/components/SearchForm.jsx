import React, { useState, useEffect } from 'react';
import {
  Search, RotateCcw, Sparkles, MapPin, Briefcase, Tag,
  Compass, ChevronDown, ChevronUp, Layers, SlidersHorizontal
} from 'lucide-react';

const COMMON_SERVICES = [
  { id: 'Website Development', label: '🌐 Website Dev' },
  { id: 'Mobile Application', label: '📱 Mobile App' },
  { id: 'Logo / Branding', label: '🎨 Branding' },
  { id: 'Video Editing', label: '🎬 Video Editing' },
  { id: 'SEO & Digital Marketing', label: '🔍 SEO Marketing' },
  { id: 'Social Media Management', label: '📱 Social Media' },
];

const COMMON_CATEGORIES = [
  { id: 'Restaurants', label: '🍽️ Restaurants' },
  { id: 'Bakeries & Cafes', label: '☕ Cafes' },
  { id: 'Salons & Spas', label: '💇 Salons & Spas' },
  { id: 'Healthcare & Clinics', label: '🏥 Healthcare' },
  { id: 'Real Estate', label: '🏢 Real Estate' },
  { id: 'Fitness & Gyms', label: '🏋️ Fitness' },
];

const RADIUS_OPTIONS = ['5 km', '10 km', '20 km', '50 km'];

export default function SearchForm({ onSearch, isLoading, initialValues }) {
  const [service, setService] = useState(initialValues?.service || 'Website Development');
  const [category, setCategory] = useState(initialValues?.category || 'Restaurants');
  const [location, setLocation] = useState(initialValues?.location || 'Vijayawada');
  const [radius, setRadius] = useState(initialValues?.radius || '20 km');
  const [keywords, setKeywords] = useState(initialValues?.keywords || '');
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (initialValues) {
      if (initialValues.service) setService(initialValues.service);
      if (initialValues.category) setCategory(initialValues.category);
      if (initialValues.location) setLocation(initialValues.location);
      if (initialValues.radius) setRadius(initialValues.radius);
      if (initialValues.keywords !== undefined) setKeywords(initialValues.keywords || '');
    }
  }, [initialValues]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!service || !category || !location) return;
    onSearch({
      service,
      category,
      location,
      radius,
      keywords: keywords.trim() || null,
    });
  };

  const handleClear = () => {
    setService('Website Development');
    setCategory('Restaurants');
    setLocation('');
    setRadius('20 km');
    setKeywords('');
  };

  return (
    <form className="search-card" onSubmit={handleSubmit}>
      {/* Top Section: Quick-Select Service Pills */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <label className="form-label" style={{ margin: 0 }}>
            <span>Your Agency Service</span>
          </label>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Quick Select</span>
        </div>
        <div className="preset-pills-row">
          {COMMON_SERVICES.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`preset-pill ${service === s.id ? 'active' : ''}`}
              onClick={() => setService(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick-Select Category Pills */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <label className="form-label" style={{ margin: 0 }}>
            <span>Target Industry</span>
          </label>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Popular Niches</span>
        </div>
        <div className="preset-pills-row">
          {COMMON_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`preset-pill ${category === c.id ? 'active' : ''}`}
              onClick={() => setCategory(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Form Fields Grid */}
      <div className="search-grid">
        {/* Service Input */}
        <div className="form-group">
          <label className="form-label">
            <span>Service Name</span>
            <Briefcase size={12} color="var(--primary)" />
          </label>
          <input
            type="text"
            className="form-input"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="e.g. Website Development"
            required
          />
        </div>

        {/* Category Input */}
        <div className="form-group">
          <label className="form-label">
            <span>Business Category</span>
            <Tag size={12} color="var(--accent-cyan)" />
          </label>
          <input
            type="text"
            className="form-input"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g. Restaurants"
            required
          />
        </div>

        {/* Location Input */}
        <div className="form-group">
          <label className="form-label">
            <span>Target City / Area</span>
            <MapPin size={12} color="var(--accent-emerald)" />
          </label>
          <input
            type="text"
            className="form-input"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Vijayawada, Austin, London"
            required
          />
        </div>

        {/* Radius */}
        <div className="form-group">
          <label className="form-label">
            <span>Radius Range</span>
            <Compass size={12} color="var(--accent-amber)" />
          </label>
          <select
            className="form-select"
            value={radius}
            onChange={(e) => setRadius(e.target.value)}
          >
            {RADIUS_OPTIONS.map((r) => (
              <option key={r} value={r} style={{ background: 'var(--bg-card)', color: 'var(--text-primary)' }}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Advanced Keywords Toggle */}
      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="btn btn-ghost btn-sm"
          style={{ padding: '2px 0', fontSize: '11px', color: 'var(--text-secondary)' }}
        >
          <SlidersHorizontal size={12} />
          <span>{showAdvanced ? 'Hide Advanced Filters' : 'Add Optional Keywords or Specialty Filter'}</span>
        </button>

        {showAdvanced && (
          <div className="form-group" style={{ marginTop: 8 }}>
            <label className="form-label">
              <span>Keywords (comma-separated)</span>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>e.g. fine-dining, rooftop, new</span>
            </label>
            <input
              type="text"
              className="form-input"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g. rooftop, family, boutique..."
            />
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="search-actions">
        <button
          type="button"
          onClick={handleClear}
          className="btn btn-ghost btn-sm"
          disabled={isLoading}
        >
          <RotateCcw size={13} />
          <span>Reset</span>
        </button>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading || !location.trim()}
          style={{ padding: '9px 18px' }}
        >
          {isLoading ? (
            <>
              <span className="spin">⚡</span>
              <span>Scanning Public Listings...</span>
            </>
          ) : (
            <>
              <Sparkles size={15} />
              <span>Find High-Value Clients</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
