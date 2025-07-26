import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Search documents in a project
export const searchProjectDocuments = async (projectId, query, limit = 10) => {
  const token = localStorage.getItem('token');
  const response = await api.get(`/projects/${projectId}/search`, {
    params: { query, limit },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
};

export default api;