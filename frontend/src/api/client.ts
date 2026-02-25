import axios, { AxiosError, AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private readonly disableAuth: boolean;

  constructor() {
    this.disableAuth = import.meta.env.VITE_DISABLE_AUTH === 'true';
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - adiciona token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        const locale = localStorage.getItem('saas-impacto-locale') || 'pt-BR';
        config.headers['Accept-Language'] = locale;
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - trata erros
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (this.disableAuth) {
          return Promise.reject(error);
        }

        // Se for 401, tenta fazer refresh token
        if (error.response?.status === 401 && !error.config?.url?.includes('/auth/')) {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
                refresh_token: refreshToken,
              });
              localStorage.setItem('access_token', data.access_token);
              // Retenta a requisição original
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${data.access_token}`;
                return this.client.request(error.config);
              }
            } catch {
              // Se refresh falhar, faz logout
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get instance() {
    return this.client;
  }
}

export const apiClient = new ApiClient().instance;
