/**
 * Servicio de Empresas
 * ====================
 */
import apiClient from '../client';
import type { Empresa, EmpresaListResponse, EmpresaFilters } from '@/types/empresa.types';

export const empresaService = {
  /**
   * Lista todas las empresas
   */
  listar: async (filters?: EmpresaFilters): Promise<EmpresaListResponse> => {
    const params = new URLSearchParams();
    
    if (filters?.base_datos) params.append('base_datos', filters.base_datos);
    if (filters?.buscar) params.append('buscar', filters.buscar);
    if (filters?.usuario_filtro) params.append('usuario_filtro', filters.usuario_filtro);
    if (filters?.grupo_filtro) params.append('grupo_filtro', filters.grupo_filtro);
    
    const { data } = await apiClient.get<EmpresaListResponse>(`/empresas?${params.toString()}`);
    return data;
  },

  /**
   * Obtiene una empresa por RUT
   */
  obtenerPorRut: async (rut: string, baseDatos?: string): Promise<Empresa> => {
    const params = baseDatos ? `?base_datos=${baseDatos}` : '';
    const { data } = await apiClient.get<Empresa>(`/empresas/${rut}${params}`);
    return data;
  },

  /**
   * Obtiene estadísticas de empresas
   */
  obtenerEstadisticas: async (baseDatos?: string): Promise<any> => {
    const params = baseDatos ? `?base_datos=${baseDatos}` : '';
    const { data } = await apiClient.get(`/empresas/estadisticas${params}`);
    return data;
  },
};
