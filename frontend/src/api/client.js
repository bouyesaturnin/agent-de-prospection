import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const TOKEN_STORAGE_KEY = 'prospectai_token';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Authentification
export const getStoredToken = () => localStorage.getItem(TOKEN_STORAGE_KEY);
export const setStoredToken = (token) => localStorage.setItem(TOKEN_STORAGE_KEY, token);
export const clearStoredToken = () => localStorage.removeItem(TOKEN_STORAGE_KEY);
export const login = (username, password) => apiClient.post('/auth/login/', { username, password });
export const logout = () => apiClient.post('/auth/logout/');
export const getMe = () => apiClient.get('/auth/me/');

// Leads
export const getLeads = (params) => apiClient.get('/leads/', { params });
export const getLead = (leadId) => apiClient.get(`/leads/${leadId}/`);
export const createLead = (payload) => apiClient.post('/leads/', payload);
export const updateLead = (leadId, payload) => apiClient.patch(`/leads/${leadId}/`, payload);
export const deleteLead = (leadId) => apiClient.delete(`/leads/${leadId}/`);
export const generateAiMessage = (leadId) => apiClient.post(`/leads/${leadId}/generate_ai_message/`);
export const checkReplies = () => apiClient.post('/leads/check_replies/');
export const processFollowups = () => apiClient.post('/leads/process_followups/');
export const importLeadsCsv = (file, campaignId) => {
  const formData = new FormData();
  formData.append('file', file);
  if (campaignId) formData.append('campaign', campaignId);
  return apiClient.post('/leads/import_csv/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Campagnes
export const getCampaigns = (params) => apiClient.get('/campaigns/', { params });
export const createCampaign = (payload) => apiClient.post('/campaigns/', payload);
export const updateCampaign = (campaignId, payload) => apiClient.patch(`/campaigns/${campaignId}/`, payload);
export const deleteCampaign = (campaignId) => apiClient.delete(`/campaigns/${campaignId}/`);
export const startCampaign = (campaignId) => apiClient.post(`/campaigns/${campaignId}/start/`);
export const pauseCampaign = (campaignId) => apiClient.post(`/campaigns/${campaignId}/pause/`);

// Messages
export const sendMessage = (messageId) => apiClient.post(`/messages/${messageId}/send/`);

// Journaux
export const getLogs = (params) => apiClient.get('/logs/', { params });

export default apiClient;
