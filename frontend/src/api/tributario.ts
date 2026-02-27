import api from './client';
import type { F29Empresa, F29Datos, F29Observacion, DJEmpresa, SituacionEmpresa, SituacionTributaria } from '../types/tributario';

export const f29Api = {
  empresas: (params?: Record<string, string>) =>
    api.get<F29Empresa[]>('/f29/empresas', { params }).then((r) => r.data),

  datos: (rut: string, periodo: string, base_datos?: string) =>
    api.get<F29Datos>(`/f29/datos/${rut}/${periodo}`, { params: { base_datos } }).then((r) => r.data),

  observaciones: (rut: string, periodo: string, base_datos?: string) =>
    api.get<F29Observacion[]>(`/f29/observaciones/${rut}/${periodo}`, { params: { base_datos } }).then((r) => r.data),

  estadisticas: (base_datos?: string) =>
    api.get('/f29/estadisticas', { params: { base_datos } }).then((r) => r.data),

  periodos: (base_datos?: string) =>
    api.get<string[]>('/f29/periodos', { params: { base_datos } }).then((r) => r.data),
};

export const djApi = {
  empresas: (params?: Record<string, string>) =>
    api.get<DJEmpresa[]>('/dj/empresas', { params }).then((r) => r.data),

  empresa: (rut: string, base_datos?: string) =>
    api.get(`/dj/empresa/${rut}`, { params: { base_datos } }).then((r) => r.data),

  estadisticas: (base_datos?: string) =>
    api.get('/dj/estadisticas', { params: { base_datos } }).then((r) => r.data),
};

export const situacionApi = {
  empresas: (params?: Record<string, string>) =>
    api.get<SituacionEmpresa[]>('/situacion-tributaria/empresas', { params }).then((r) => r.data),

  get: (rut: string, base_datos?: string) =>
    api.get<SituacionTributaria>(`/situacion-tributaria/${rut}`, { params: { base_datos } }).then((r) => r.data),
};
