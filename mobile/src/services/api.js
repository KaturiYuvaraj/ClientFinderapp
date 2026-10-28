/**
 * AI Client Finder — React Native API Service
 * Uses AsyncStorage instead of chrome.storage / localStorage
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, NativeModules } from 'react-native';

// ── Machine's local Wi-Fi IP for real mobile device testing ──
// Dynamically extracts the host IP from Metro bundler if running on real device via Expo LAN,
// falling back to current machine Wi-Fi IP 192.168.1.11
export const getDevServerHost = () => {
  const scriptURL = NativeModules?.SourceCode?.scriptURL;
  if (scriptURL) {
    const match = scriptURL.match(/https?:\/\/([^:/]+)/);
    if (match && match[1] && match[1] !== 'localhost' && match[1] !== '127.0.0.1') {
      return match[1];
    }
  }
  return '192.168.1.11';
};

export const getDefaultApiBaseUrl = () => {
  const host = getDevServerHost();
  return Platform.select({
    ios: `http://${host}:8000`,
    android: `http://${host}:8000`,
    default: 'http://localhost:8000',
  });
};

class ApiService {
  constructor() {
    this.token = null;
    this.baseUrl = getDefaultApiBaseUrl();
  }

  async init() {
    try {
      this.token = await AsyncStorage.getItem('client_finder_token');
      let customUrl = await AsyncStorage.getItem('client_finder_api_url');
      // If user had the old stale IP 192.168.1.6 saved, auto-upgrade it to the new IP
      if (customUrl && customUrl.includes('192.168.1.6:8000')) {
        customUrl = getDefaultApiBaseUrl();
        await AsyncStorage.setItem('client_finder_api_url', customUrl);
      }
      if (customUrl) {
        this.baseUrl = customUrl;
      } else {
        this.baseUrl = getDefaultApiBaseUrl();
      }
    } catch (_) {}
    return this.token;
  }

  async setBaseUrl(url) {
    this.baseUrl = url.replace(/\/+$/, '');
    await AsyncStorage.setItem('client_finder_api_url', this.baseUrl);
  }

  async getBaseUrl() {
    const saved = await AsyncStorage.getItem('client_finder_api_url');
    if (saved && saved.includes('192.168.1.6:8000')) {
      const updated = getDefaultApiBaseUrl();
      await AsyncStorage.setItem('client_finder_api_url', updated);
      return updated;
    }
    return saved || getDefaultApiBaseUrl();
  }

  async setToken(token) {
    this.token = token;
    if (token) {
      await AsyncStorage.setItem('client_finder_token', token);
    } else {
      await AsyncStorage.removeItem('client_finder_token');
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const timeoutMs = options.timeout || (endpoint.includes('/search') ? 35000 : 8000);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        await this.setToken(null);
        throw new Error('Session expired. Please log in again.');
      }
      if (response.status === 204) return null;

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const errorMsg = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
          : data.detail || `Server error (${response.status})`;
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        throw new Error('Network request timed out. Please verify backend is running.');
      }
      throw err;
    }
  }

  // Auth
  async register(name, email, password) {
    const res = await this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    await this.setToken(res.access_token);
    return res;
  }

  async login(email, password) {
    const res = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    await this.setToken(res.access_token);
    return res;
  }

  async logout() {
    await this.setToken(null);
  }

  async getMe() {
    return this.request('/api/auth/me');
  }

  // Leads & Search
  async searchBusinesses(params) {
    const payload = {
      service: params.service || params.service_offered || 'Website Design',
      category: params.category || '',
      location: params.location || '',
      radius: params.radius || '20 km',
      keywords: params.keywords || null,
    };
    return this.request('/api/leads/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getSavedLeads(params = {}) {
    const q = new URLSearchParams();
    if (params.status && params.status !== 'All') q.append('status', params.status);
    if (params.service && params.service !== 'All') q.append('service', params.service);
    if (params.city) q.append('city', params.city);
    if (params.minScore) q.append('min_score', params.minScore);
    if (params.search) q.append('search', params.search);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return this.request(`/api/leads${qs}`);
  }

  async saveLead(leadData) {
    const payload = {
      business_name: leadData.business_name || leadData.name,
      category: leadData.category || '',
      phone: leadData.phone || '',
      website: leadData.website || '',
      address: leadData.address || '',
      city: leadData.city || '',
      latitude: leadData.latitude || null,
      longitude: leadData.longitude || null,
      rating: leadData.rating || 0.0,
      review_count: leadData.review_count || 0,
      source: leadData.source || 'OpenStreetMap',
      source_url: leadData.source_url || '',
      provider_id: leadData.provider_id || null,
      service: leadData.service || leadData.service_offered || 'Website Design',
      lead_score: leadData.lead_score || leadData.score || leadData.opportunity_score || 0,
      opportunity_type: leadData.opportunity_type || '',
      opportunity_reason: leadData.opportunity_reason || '',
      confidence: leadData.confidence || 'Moderate',
      status: leadData.status || 'New',
    };
    return this.request('/api/leads', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateLead(id, data) {
    return this.request(`/api/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteLead(id) {
    return this.request(`/api/leads/${id}`, { method: 'DELETE' });
  }

  async enrichSavedLead(id) {
    return this.request(`/api/leads/${id}/enrich`, {
      method: 'POST',
    });
  }

  async enrichPreview(leadData) {
    return this.request('/api/leads/enrich-preview', {
      method: 'POST',
      body: JSON.stringify({
        name: leadData.name || leadData.business_name || '',
        category: leadData.category || '',
        location: leadData.city || '',
        address: leadData.address || '',
        phone: leadData.phone || '',
        website: leadData.website || '',
      }),
    });
  }

  // AI
  async analyzeLead(business, service) {
    return this.request('/api/ai/analyze-lead', {
      method: 'POST',
      body: JSON.stringify({ business, service }),
    });
  }

  async generateMessage(params) {
    return this.request('/api/ai/generate-message', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/api/dashboard/stats');
  }

  async checkHealth() {
    return this.request('/health');
  }
}

export const api = new ApiService();
