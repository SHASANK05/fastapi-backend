import axios from 'axios';

export const DJANGO_BASE_URL = 'http://127.0.0.1:8000';
export const FASTAPI_BASE_URL = 'http://127.0.0.1:8001';

export const api = axios.create();

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Admin Fraud Review APIs (FastAPI Gateway)
export const getFlaggedTransactions = async (limit = 50, offset = 0) => {
  const res = await api.get(`${FASTAPI_BASE_URL}/api/admin/transactions/flagged/`, {
    params: { limit, offset }
  });
  return res.data;
};

export const reviewTransaction = async (transactionId, action, notes = '') => {
  const res = await api.post(
    `${FASTAPI_BASE_URL}/api/admin/transactions/${transactionId}/review/`,
    { action, notes }
  );
  return res.data;
};