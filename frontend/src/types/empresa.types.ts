/**
 * Tipos de Empresa
 * ================
 */

export interface Empresa {
  id: number;
  rut: string;
  nombre: string;
  razon_social?: string;
  giro?: string;
  auditor?: string;
  grupo?: string;
  activo: boolean;
  tiene_credencial_sii: boolean;
  estado_credencial?: string;
}

export interface EmpresaListResponse {
  empresas: Empresa[];
  total: number;
}

export interface EmpresaFilters {
  base_datos?: string;
  buscar?: string;
  usuario_filtro?: string;
  grupo_filtro?: string;
}
