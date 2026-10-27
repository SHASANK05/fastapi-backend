import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user_role', response.data.role);
    }
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_role');
  },
  getToken: () => localStorage.getItem('token'),
  getStoredRole: () => localStorage.getItem('user_role') || 'EMPLOYEE',
};

export const analyticsService = {
  getAnalytics: async () => {
    const response = await api.get('/predictions/analytics');
    return response.data;
  },
  getDepartmentRisk: async () => {
    const response = await api.get('/predictions/department-risk');
    return response.data;
  },
  getHighRiskEmployees: async () => {
    const response = await api.get('/predictions/high-risk');
    return response.data;
  },
  triggerBulkPredict: async () => {
    const response = await api.post('/predictions/bulk-predict');
    return response.data;
  },
  predictIndividual: async (employeeId) => {
    const response = await api.post(`/predictions/predict/${employeeId}`);
    return response.data;
  },
  downloadCSV: async () => {
    const token = localStorage.getItem('token');
    const response = await api.get('/predictions/export-csv', {
      responseType: 'blob',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `workforce_attrition_report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};

export const employeeService = {
  getAll: async () => {
    const response = await api.get('/employees/');
    return response.data;
  },
  create: async (employeeData) => {
    const response = await api.post('/employees/', employeeData);
    return response.data;
  }
};

export const departmentService = {
  getAll: async () => {
    const response = await api.get('/departments/');
    return response.data;
  },
  getDeepDive: async (code) => {
    const response = await api.get(`/departments/${code}/deep-dive`);
    return response.data;
  }
};

export const leaveService = {
  getAll: async () => {
    const response = await api.get('/leaves/');
    return response.data;
  },
  create: async (payload) => {
    const response = await api.post('/leaves/', payload);
    return response.data;
  },
  updateStatus: async (leaveId, status) => {
    const response = await api.put(`/leaves/${leaveId}/status?status=${status}`);
    return response.data;
  }
};

export const auditService = {
  getAll: async (limit = 50) => {
    const response = await api.get(`/audit-logs/?limit=${limit}`);
    return response.data;
  }
};

export const retentionService = {
  getDiagnostics: async (employeeId) => {
    const response = await api.get(`/retention/diagnostics/${employeeId}`);
    return response.data;
  },
  saveCase: async (payload) => {
    const response = await api.post('/retention/save-case', payload);
    return response.data;
  }
};

export const datasetService = {
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/datasets/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};

export default api;
