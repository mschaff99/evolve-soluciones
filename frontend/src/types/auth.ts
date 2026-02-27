export interface Usuario {
  id: number;
  nombre_usuario: string;
  email: string | null;
  rol: string;
  base_datos_mysql: string | null;
  activo: boolean;
  auditor_mysql?: string | null;
  tipo_usuario_mysql?: string | null;
}

export interface LoginRequest {
  nombre_usuario: string;
  contraseña: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  usuario: Usuario;
}

export interface Modulo {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  icono: string | null;
  orden_menu: number;
  url_base: string | null;
  activo: boolean;
}
