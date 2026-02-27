import api from './client';
import type { LoginRequest, TokenResponse, Modulo } from '../types/auth';

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  getMe: () => api.get('/auth/me').then((r) => r.data),

  getModules: () =>
    api.get<Modulo[]>('/auth/modules').then((r) => r.data),

  changePassword: (contraseña_actual: string, nueva_contraseña: string) =>
    api.post('/auth/change-password', { contraseña_actual, nueva_contraseña }).then((r) => r.data),
};
