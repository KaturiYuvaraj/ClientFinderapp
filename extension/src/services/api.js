/**
 * AI Client Finder API Service
 * Supports Chrome Extension storage (chrome.storage.local) with localStorage fallback
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

class StorageHelper {
  static async getItem(key) {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      return new Promise((resolve) => {
        chrome.storage.local.get([key], (result) => {
          resolve(result[key] || null);
        });
      });
    }
    return localStorage.getItem(key);
  }

  static async setItem(key, value) {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      return new Promise((resolve) => {
        chrome.storage.local.set({ [key]: value }, () => resolve());
      });
    }
    localStorage.setItem(key, value);
  }

  static async removeItem(key) {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      return new Promise((resolve) => {
        chrome.storage.local.remove([key], () => resolve());
      });
    }
    localStorage.removeItem(key);
  }
}

class ApiService {
  constructor() {
    this.token = null;
    this.baseUrl = DEFAULT_API_BASE_URL;
  }

  async init() {
    this.token = await StorageHelper.getItem('client_finder_token');
    const customUrl = await StorageHelper.getItem('client_finder_api_url');
    if (customUrl) {
      this.baseUrl = customUrl;
    }
    return this.token;
  }

  async setBaseUrl(url) {
    this.baseUrl = url.replace(/\/+$/, '');
    await StorageHelper.setItem('client_finder_api_url', this.baseUrl);
  }

  async getBaseUrl() {
    const customUrl = await StorageHelper.getItem('client_finder_api_url');
    return customUrl || DEFAULT_API_BASE_URL;
  }

  async setToken(token) {
    this.token = token;
    if (token) {
      await StorageHelper.setItem('client_finder_token', token);
    } else {
      await StorageHelper.removeItem('client_finder_token');
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        // Token expired or invalid
        await this.setToken(null);
        window.dispatchEvent(new CustomEvent('auth:expired'));
        throw new Error('Session expired. Please log in again.');
      }

      if (response.status === 204) {
        return null;
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
          : data.detail || `Server error (${response.status})`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        throw new Error(`Cannot connect to backend at ${this.baseUrl}. Please ensure FastAPI is running.`);
      }
      throw err;
    }
  }

  // --- Auth Endpoints ---
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

  // --- Leads & Search Endpoints ---
  async searchBusinesses(searchParams) {
    return this.request('/api/leads/search', {
      method: 'POST',
      body: JSON.stringify(searchParams),
    });
  }

  async getSearchHistory() {
    return this.request('/api/leads/search-history');
  }

  async getSavedLeads(params = {}) {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'All') query.append('status', params.status);
    if (params.service && params.service !== 'All') query.append('service', params.service);
    if (params.city) query.append('city', params.city);
    if (params.minScore) query.append('min_score', params.minScore);
    if (params.search) query.append('search', params.search);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/leads${queryString}`);
  }

  async getLead(id) {
    return this.request(`/api/leads/${id}`);
  }

  async saveLead(leadData) {
    return this.request('/api/leads', {
      method: 'POST',
      body: JSON.stringify(leadData),
    });
  }

  async updateLead(id, updateData) {
    return this.request(`/api/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteLead(id) {
    return this.request(`/api/leads/${id}`, {
      method: 'DELETE',
    });
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

  getExportCsvUrl(params = {}) {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'All') query.append('status', params.status);
    if (params.service && params.service !== 'All') query.append('service', params.service);
    return `${this.baseUrl}/api/leads/export?${query.toString()}`;
  }

  async downloadExportCsv(params = {}) {
    const url = this.getExportCsvUrl(params);
    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error('Failed to download CSV export');
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `client_finder_leads_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  }

  // --- AI Endpoints ---
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

  // --- Dashboard Endpoints ---
  async getDashboardStats() {
    return this.request('/api/dashboard/stats');
  }

  // --- Health Check ---
  async checkHealth() {
    return this.request('/health');
  }
}

export const api = new ApiService();
