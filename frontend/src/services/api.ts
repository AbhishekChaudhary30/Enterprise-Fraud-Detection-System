const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

class ApiService {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Authentication expired');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) throw new Error('Invalid credentials');
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(username: string, password: string) {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail);
    }
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async loginGuest() {
    const response = await fetch(`${API_BASE}/guest`, {
      method: 'POST',
    });

    if (!response.ok) throw new Error('Guest login failed');
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  // Predictions
  async predict(features: Record<string, number>, threshold?: number) {
    return this.request('POST', '/predict', { features, threshold });
  }

  async predictBatch(records: Record<string, number>[]) {
    return this.request('POST', '/predict/batch', { records });
  }

  async uploadCsv(file: File): Promise<Blob> {
    const token = this.getToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail);
    }
    return response.blob();
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('GET', '/dashboard/stats');
  }

  async getRecentPredictions() {
    return this.request('GET', '/dashboard/recent');
  }

  async getHighRiskPredictions() {
    return this.request('GET', '/dashboard/high-risk');
  }

  // History & Reset
  async resetDashboard() {
    return this.request('POST', '/dashboard/reset');
  }

  async getHistory(limit = 100) {
    return this.request('GET', `/history?limit=${limit}`);
  }

  async deletePrediction(predictionId: string) {
    return this.request('DELETE', `/predictions/${predictionId}`);
  }

  // Investigations
  async getInvestigations(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request('GET', `/investigations${params}`);
  }

  async getInvestigation(id: number) {
    return this.request('GET', `/investigations/${id}`);
  }

  async createInvestigation(predictionId: string, priority = 'MEDIUM') {
    return this.request('POST', '/investigations', { prediction_id: predictionId, priority });
  }

  async updateInvestigation(id: number, status: string, notes?: string) {
    return this.request('PATCH', `/investigations/${id}`, { status, notes });
  }

  // Models
  async getModels() {
    return this.request('GET', '/models');
  }

  async getLatestModel() {
    return this.request('GET', '/models/latest');
  }

  async getModelVersion(version: string) {
    return this.request('GET', `/models/${version}`);
  }

  // Monitoring
  async getMonitoringOverview() {
    return this.request('GET', '/monitoring/overview');
  }

  async getDriftReport() {
    return this.request('GET', '/monitoring/drift');
  }

  async getModelMetrics() {
    return this.request('GET', '/monitoring/model-metrics');
  }

  // Health
  async getHealth() {
    return this.request('GET', '/health');
  }

  async getReady() {
    return this.request('GET', '/ready');
  }

  // Batch Jobs
  async getBatchJobs() {
    return this.request('GET', '/batch-jobs');
  }
}

export const api = new ApiService();
