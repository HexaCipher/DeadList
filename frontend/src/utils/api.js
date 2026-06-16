import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error(`API Error: ${message}`);
    return Promise.reject(error);
  }
);

// ─── Upload ─────────────────────────────────────────────────
export const uploadDump = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress?.(percent);
    },
  });
};

// ─── Analysis ───────────────────────────────────────────────
export const getAnalysis = (id) => api.get(`/analysis/${id}`);
export const getProcesses = (id, params = {}) => api.get(`/analysis/${id}/processes`, { params });
export const getProcessDetail = (id, pid) => api.get(`/analysis/${id}/process/${pid}`);
export const getNetwork = (id) => api.get(`/analysis/${id}/network`);
export const downloadReport = (id) => api.get(`/analysis/${id}/report/pdf`, { responseType: 'blob' });
export const deleteAnalysis = (id) => api.delete(`/analysis/${id}`);

// ─── History ────────────────────────────────────────────────
export const getHistory = (page = 1, limit = 20) => api.get('/history', { params: { page, limit } });

// ─── Health ─────────────────────────────────────────────────
export const getHealth = () => api.get('/health');

export default api;
