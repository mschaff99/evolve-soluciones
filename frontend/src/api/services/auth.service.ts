/**
 * Servicio de Autenticación
 * =========================
 */
import apiClient from '../client';
import type { LoginRequest, LoginResponse, Usuario } from '@/types/auth.types';

export const authService = {
  /**
   * Inicia sesión de usuario
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', credentials);
    
    // Guardar tokens en localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    return data;
  },

  /**
   * Cierra sesión de usuario
   */
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      // Limpiar tokens siempre, incluso si falla la petición
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  /**
   * Obtiene datos del usuario actual
   */
  getCurrentUser: async (): Promise<Usuario> => {
    const { data } = await apiClient.get<Usuario>('/auth/me');
    return data;
  },

  /**
   * Verifica si el usuario está autenticado
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token');
  },
};
