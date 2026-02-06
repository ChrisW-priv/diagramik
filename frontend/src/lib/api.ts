import axios from 'axios';
import {
  getAuthHeader,
  getStoredTokens,
  setTokens,
  clearTokens,
  isTokenExpired,
  setUser,
} from './auth';

const API_BASE_URL = import.meta.env.PROD
  ? 'https://diagramik.com'
  : 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// Add auth header dynamically on each request
apiClient.interceptors.request.use(async (config) => {
  const tokens = getStoredTokens();

  if (tokens) {
    // Check if access token is expired and we have a refresh token
    if (isTokenExpired(tokens.access) && !isTokenExpired(tokens.refresh)) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const response = await axios.post(
            `${API_BASE_URL}/api/v1/auth/token/refresh/`,
            { refresh: tokens.refresh }
          );
          const newTokens = {
            access: response.data.access,
            refresh: response.data.refresh || tokens.refresh,
          };
          setTokens(newTokens);
          onTokenRefreshed(newTokens.access);
          config.headers.Authorization = `Bearer ${newTokens.access}`;
        } catch (refreshError) {
          clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/login?reason=session_expired';
          }
        } finally {
          isRefreshing = false;
        }
      } else {
        // Wait for the token to be refreshed
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            config.headers.Authorization = `Bearer ${token}`;
            resolve(config);
          });
        });
      }
    } else {
      config.headers.Authorization = getAuthHeader();
    }
  }

  return config;
});

// Handle 401 responses by clearing credentials and redirecting to login
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      clearTokens();
      if (typeof window !== 'undefined') {
        const errorDetail = error.response?.data?.detail;
        const reason = errorDetail ? encodeURIComponent(errorDetail) : 'session_expired';
        window.location.href = `/login?reason=${reason}`;
      }
    }
    return Promise.reject(error);
  }
);

// Diagram API
export const getDiagrams = () => {
  return apiClient.get('/diagrams/');
};

export const getDiagram = (id: string) => {
  return apiClient.get(`/diagrams/${id}/`);
};

export const createDiagram = (text: string) => {
  return apiClient.post('/diagrams/', { text });
};

export const createDiagramVersion = (diagramId: string, text: string) => {
  return apiClient.post(`/diagrams/${diagramId}/versions/`, { text });
};

export const deleteDiagram = (id: string) => {
  return apiClient.delete(`/diagrams/${id}/`);
};

export const deleteDiagramVersion = (diagramId: string, versionId: string) => {
  return apiClient.delete(`/diagrams/${diagramId}/versions/${versionId}/`);
};

// Auth API
export const authApi = {
  async login(email: string, password: string) {
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login/`, {
      email,
      password,
    });
    const { access, refresh, user } = response.data;
    setTokens({ access, refresh });
    if (user) {
      setUser(user);
    }
    return response.data;
  },

  async register(
    email: string,
    password1: string,
    password2: string,
    firstName?: string,
    termsAccepted?: boolean
  ) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/registration/`,
      {
        email,
        password1,
        password2,
        first_name: firstName || '',
        terms_accepted: termsAccepted || false,
      }
    );
    const { access, refresh, user } = response.data;
    if (access && refresh) {
      setTokens({ access, refresh });
    }
    if (user) {
      setUser(user);
    }
    return response.data;
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout/');
    } catch {
      // Ignore errors during logout
    }
    clearTokens();
  },

  async getUser() {
    const response = await apiClient.get('/auth/user/');
    setUser(response.data);
    return response.data;
  },

  async updateUser(data: { first_name?: string; last_name?: string }) {
    const response = await apiClient.patch('/auth/user/', data);
    setUser(response.data);
    return response.data;
  },

  async requestPasswordReset(email: string) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/password/reset/`,
      { email }
    );
    return response.data;
  },

  async confirmPasswordReset(
    uid: string,
    token: string,
    newPassword1: string,
    newPassword2: string
  ) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/password/reset/confirm/`,
      {
        uid,
        token,
        new_password1: newPassword1,
        new_password2: newPassword2,
      }
    );
    return response.data;
  },

  async getGoogleAuthUrl() {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/auth/social/google/url/`
    );
    return response.data.auth_url;
  },

  async googleLogin(code: string) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/social/google/`,
      { code }
    );
    const { access, refresh, user } = response.data;
    if (access && refresh) {
      setTokens({ access, refresh });
    }
    if (user) {
      setUser(user);
    }
    return response.data;
  },

  async refreshToken() {
    const tokens = getStoredTokens();
    if (!tokens?.refresh) {
      throw new Error('No refresh token available');
    }
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/token/refresh/`,
      { refresh: tokens.refresh }
    );
    const newTokens = {
      access: response.data.access,
      refresh: response.data.refresh || tokens.refresh,
    };
    setTokens(newTokens);
    return newTokens;
  },

  async verifyEmail(uid: string, token: string) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/verify-email/`,
      { uid, token }
    );
    const { access, refresh, user } = response.data;
    if (access && refresh) {
      setTokens({ access, refresh });
    }
    if (user) {
      setUser(user);
    }
    return response.data;
  },

  async resendVerification(email: string) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/resend-verification/`,
      { email }
    );
    return response.data;
  },

  async requestPasswordResetNew(email: string) {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/password-reset-request/`,
      { email }
    );
    return response.data;
  },

  async setNewPassword(
    uid?: string,
    token?: string,
    email?: string,
    oldPassword?: string,
    newPassword?: string
  ) {
    const data: any = { new_password: newPassword };
    if (uid && token) {
      data.uid = uid;
      data.token = token;
    } else if (email && oldPassword) {
      data.email = email;
      data.old_password = oldPassword;
    }
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/set-new-password/`,
      data
    );
    const { access, refresh, user } = response.data;
    if (access && refresh) {
      setTokens({ access, refresh });
    }
    if (user) {
      setUser(user);
    }
    return response.data;
  },
};
