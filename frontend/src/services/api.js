import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Interceptor: Her isteğe token ekle
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const authAPI = {
  register: (email, password) => api.post('/auth/register', { email, password }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
  ensureDemo: () => api.post('/auth/ensure-demo'),
};

// Folders
export const foldersAPI = {
  list: () => api.get('/folders/'),
  create: (name, parent_id = null) => api.post('/folders/', { name, parent_id }),
  update: (id, data) => api.put(`/folders/${id}`, data),
  delete: (id) => api.delete(`/folders/${id}`),
};

// Videos
export const videosAPI = {
  list: () => api.get('/videos/'),
  get: (id) => api.get(`/videos/${id}`),
  create: (source_url, folder_id) => api.post('/videos/', { source_url, folder_id }),
  createBulk: (source_urls, folder_id) => api.post('/videos/bulk', { source_urls, folder_id }),
  createFromPlaylist: (playlist_url, folder_id, max_entries = 50) =>
    api.post('/videos/from-playlist', { playlist_url, folder_id, max_entries }),
  update: (id, data) => api.put(`/videos/${id}`, data),
  delete: (id) => api.delete(`/videos/${id}`),
  retry: (id) => api.post(`/videos/${id}/retry`),
  retryAllPending: () => api.post('/videos/retry-all-pending'),
  reprocessAll: () => api.post('/videos/reprocess-all'),
};

// Search
export const searchAPI = {
  search: (query, limit = 20) => api.get('/chat/search', { params: { q: query, limit } }),
};

// Tags
export const tagsAPI = {
  list: () => api.get('/tags/'),
  create: (name, type = 'MANUAL') => api.post('/tags/', { name, type }),
  attach: (video_id, tag_id) => api.post('/tags/attach', { video_id, tag_id }),
  detach: (video_id, tag_id) => api.post('/tags/detach', { video_id, tag_id }),
  videoTags: (video_id) => api.get(`/tags/video/${video_id}`),
};

export default api;
