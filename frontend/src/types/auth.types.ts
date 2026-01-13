/**
 * Tipos de Autenticación
 * =====================
 */

export interface Usuario {
  id: number;
  nombre_usuario: string;
  email?: string;
  rol: string;
  activo: boolean;
  base_datos_mysql?: string;
  modulos: Array<{
    slug: string;
    nombre: string;
  }>;
}

export interface LoginRequest {
  nombre_usuario: string;
  contrasena: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_sesion: string;
  usuario: Usuario;
}

export interface AuthState {
  usuario: Usuario | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
