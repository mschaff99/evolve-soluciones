import api from './client';
import type { EmpresasPaginadas, EmpresaEstadisticas, Empresa } from '../types/empresa';

export const empresasApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<EmpresasPaginadas>('/empresas/', { params }).then((r) => r.data),

  get: (rut: string, base_datos?: string) =>
    api.get<Empresa>(`/empresas/${rut}`, { params: { base_datos } }).then((r) => r.data),

  create: (data: { run_rut: string; empresa: string; auditor?: string; grupo?: string }) =>
    api.post<Empresa>('/empresas/', data).then((r) => r.data),

  update: (rut: string, data: Record<string, string>) =>
    api.put<Empresa>(`/empresas/${rut}`, data).then((r) => r.data),

  delete: (rut: string) =>
    api.delete(`/empresas/${rut}`).then((r) => r.data),

  estadisticas: (base_datos?: string) =>
    api.get<EmpresaEstadisticas>('/empresas/estadisticas', { params: { base_datos } }).then((r) => r.data),

  auditores: (base_datos?: string) =>
    api.get<string[]>('/empresas/auditores', { params: { base_datos } }).then((r) => r.data),

  grupos: (base_datos?: string) =>
    api.get<string[]>('/empresas/grupos', { params: { base_datos } }).then((r) => r.data),
};
