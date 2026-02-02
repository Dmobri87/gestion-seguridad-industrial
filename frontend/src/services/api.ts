import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // No redirigir a /login durante el flujo de autenticación 2FA
      const requestUrl = error.config?.url || '';
      const isAuthEndpoint =
        requestUrl.includes('/auth/login') ||
        requestUrl.includes('/auth/verify-otp');

      if (!isAuthEndpoint) {
        // Limpiar todo el estado de autenticación de forma consistente
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth-storage');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ==========================================
// AUTH
// ==========================================

export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  verifyOtp: async (email: string, otpCode: string) => {
    const response = await api.post('/auth/verify-otp', {
      email,
      otp_code: otpCode,
    });
    return response.data;
  },

  me: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  register: async (userData: any) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  updateProfile: async (data: { full_name?: string; phone?: string }) => {
    const response = await api.put('/auth/me', data);
    return response.data;
  },
};

// ==========================================
// USERS
// ==========================================

export const usersApi = {
  getAll: async (params?: any) => {
    const response = await api.get('/users/', { params });
    return response.data;
  },

  getTAEs: async () => {
    const response = await api.get('/users/taes');
    return response.data;
  },

  getAssignable: async () => {
    const response = await api.get('/users/assignable');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/users/', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.put(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/users/${id}`);
    return response.data;
  },
};

// ==========================================
// WORK GROUPS
// ==========================================

export const workGroupsApi = {
  getAll: async () => {
    const response = await api.get('/work-groups/');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/work-groups/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/work-groups/', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.put(`/work-groups/${id}`, data);
    return response.data;
  },

  addMember: async (groupId: number, userId: number) => {
    const response = await api.post(`/work-groups/${groupId}/members/${userId}`);
    return response.data;
  },

  removeMember: async (groupId: number, userId: number) => {
    const response = await api.delete(`/work-groups/${groupId}/members/${userId}`);
    return response.data;
  },
};

// ==========================================
// ACTIVITY TEMPLATES
// ==========================================

export const activityApi = {
  // Categorías
  getCategories: async () => {
    const response = await api.get('/activity-categories/');
    return response.data;
  },

  createCategory: async (data: any) => {
    const response = await api.post('/activity-categories/', data);
    return response.data;
  },

  updateCategory: async (id: number, data: any) => {
    const response = await api.put(`/activity-categories/${id}`, data);
    return response.data;
  },

  deleteCategory: async (id: number) => {
    const response = await api.delete(`/activity-categories/${id}`);
    return response.data;
  },

  // Templates
  getTemplates: async (categoryId?: number) => {
    const response = await api.get('/activity-templates/', {
      params: { category_id: categoryId },
    });
    return response.data;
  },

  getTemplatesGrouped: async () => {
    const response = await api.get('/activity-templates/by-category');
    return response.data;
  },

  createTemplate: async (data: any) => {
    const response = await api.post('/activity-templates/', data);
    return response.data;
  },

  updateTemplate: async (id: number, data: any) => {
    const response = await api.put(`/activity-templates/${id}`, data);
    return response.data;
  },

  deleteTemplate: async (id: number) => {
    const response = await api.delete(`/activity-templates/${id}`);
    return response.data;
  },
};

// ==========================================
// PLANNING
// ==========================================

export const planningApi = {
  getPlans: async (year: number, month?: number, userId?: number) => {
    const response = await api.get('/planning/plans', {
      params: { year, month, user_id: userId },
    });
    return response.data;
  },

  getPlan: async (planId: number) => {
    const response = await api.get(`/planning/plans/${planId}`);
    return response.data;
  },

  createPlan: async (data: any) => {
    const response = await api.post('/planning/plans', data);
    return response.data;
  },

  updatePlan: async (planId: number, data: any) => {
    const response = await api.put(`/planning/plans/${planId}`, data);
    return response.data;
  },

  approvePlan: async (planId: number) => {
    const response = await api.post(`/planning/plans/${planId}/approve`);
    return response.data;
  },

  addActivity: async (planId: number, data: any) => {
    const response = await api.post(`/planning/plans/${planId}/activities`, data);
    return response.data;
  },

  bulkAddActivities: async (planId: number, activities: any[]) => {
    const response = await api.post(`/planning/plans/${planId}/activities/bulk`, {
      monthly_plan_id: planId,
      activities,
    });
    return response.data;
  },

  bulkCreatePlans: async (data: any) => {
    const response = await api.post('/planning/plans/bulk', data);
    return response.data;
  },

  updateActivity: async (activityId: number, data: any) => {
    const response = await api.put(`/planning/activities/${activityId}`, data);
    return response.data;
  },

  getMyPlan: async (year: number, month: number) => {
    const response = await api.get('/planning/my-plan', {
      params: { year, month },
    });
    return response.data;
  },
};

// ==========================================
// EXECUTIONS
// ==========================================

export const executionsApi = {
  getAll: async (year: number, month: number, userId?: number) => {
    const response = await api.get('/executions/', {
      params: { year, month, user_id: userId },
    });
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/executions/', data);
    return response.data;
  },

  getMyToday: async () => {
    const response = await api.get('/executions/my-today');
    return response.data;
  },

  approve: async (executionId: number, approved: boolean, reason?: string) => {
    const response = await api.post(`/executions/${executionId}/approve`, {
      approved,
      rejection_reason: reason,
    });
    return response.data;
  },

  getStats: async (year: number, month: number) => {
    const response = await api.get('/executions/stats', {
      params: { year, month },
    });
    return response.data;
  },

  uploadFile: async (executionId: number, file: File, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    const params = description ? { description } : {};
    const response = await api.post(`/executions/${executionId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    });
    return response.data;
  },

  getFiles: async (executionId: number) => {
    const response = await api.get(`/executions/${executionId}/files`);
    return response.data;
  },

  deleteFile: async (executionId: number, fileId: number) => {
    const response = await api.delete(`/executions/${executionId}/files/${fileId}`);
    return response.data;
  },
};

// ==========================================
// DASHBOARD
// ==========================================

export const dashboardApi = {
  getData: async (year: number, month: number) => {
    const response = await api.get('/dashboard/', {
      params: { year, month },
    });
    return response.data;
  },

  getComplianceChart: async (year: number) => {
    const response = await api.get('/dashboard/compliance-chart', {
      params: { year },
    });
    return response.data;
  },
};

// ==========================================
// EMERGENCIES
// ==========================================

export const emergenciesApi = {
  getTypes: async () => {
    const response = await api.get('/emergencies/types');
    return response.data;
  },

  getAll: async (year: number, month?: number) => {
    const response = await api.get('/emergencies/', {
      params: { year, month },
    });
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/emergencies/', data);
    return response.data;
  },

  registerArrival: async (emergencyId: number) => {
    const response = await api.post(`/emergencies/${emergencyId}/arrival`);
    return response.data;
  },

  close: async (emergencyId: number, actionsTaken: string, result: string) => {
    const response = await api.post(`/emergencies/${emergencyId}/close`, null, {
      params: { actions_taken: actionsTaken, result },
    });
    return response.data;
  },

  getSummary: async (year: number, month?: number) => {
    const response = await api.get('/emergencies/summary', {
      params: { year, month },
    });
    return response.data;
  },
};

// ==========================================
// EQUIPMENT
// ==========================================

export const equipmentApi = {
  getCategories: async () => {
    const response = await api.get('/equipment/categories');
    return response.data;
  },

  getAll: async (categoryId?: number) => {
    const response = await api.get('/equipment/', {
      params: { category_id: categoryId },
    });
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/equipment/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/equipment/', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await api.put(`/equipment/${id}`, data);
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/equipment/summary');
    return response.data;
  },

  getFleet: async () => {
    const response = await api.get('/equipment/fleet');
    return response.data;
  },

  getNovelties: async (equipmentId: number) => {
    const response = await api.get(`/equipment/${equipmentId}/novelties`);
    return response.data;
  },

  createNovelty: async (equipmentId: number, data: any) => {
    const response = await api.post(`/equipment/${equipmentId}/novelties`, data);
    return response.data;
  },

  resolveNovelty: async (equipmentId: number, noveltyId: number, data: any) => {
    const response = await api.put(`/equipment/${equipmentId}/novelties/${noveltyId}/resolve`, data);
    return response.data;
  },
};

// ==========================================
// CERTIFICATIONS
// ==========================================

export const certificationsApi = {
  getTypes: async () => {
    const response = await api.get('/certifications/types');
    return response.data;
  },

  getUserCertifications: async (userId: number) => {
    const response = await api.get(`/certifications/user/${userId}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/certifications/', data);
    return response.data;
  },

  getExpiring: async (days: number = 30) => {
    const response = await api.get('/certifications/expiring', {
      params: { days },
    });
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/certifications/summary');
    return response.data;
  },
};

export default api;
