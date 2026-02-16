export interface F29Empresa {
  run_rut: string;
  empresa: string | null;
  auditor: string | null;
  grupo: string | null;
  periodos: string[];
  ultimo_periodo: string | null;
  total_periodos: number;
}

export interface F29Datos {
  rut: string;
  periodo: string;
  datos: Record<string, unknown>;
  tabla_resultados: string | null;
}

export interface F29Observacion {
  id: number | null;
  rut: string;
  periodo: string;
  observacion: string | null;
  estado: string | null;
  fecha: string | null;
}

export interface DJEmpresa {
  run_rut: string;
  empresa: string | null;
  auditor: string | null;
  grupo: string | null;
  total_dj: number;
}

export interface SituacionEmpresa {
  run_rut: string;
  empresa: string | null;
  auditor: string | null;
  grupo: string | null;
  tiene_situacion: boolean;
}

export interface SituacionTributaria {
  rut: string;
  empresa?: string | null;
  razon_social: string | null;
  actividades: Record<string, unknown>[];
  inicio_actividades: string | null;
  estado_contribuyente: string | null;
  datos_adicionales: Record<string, unknown>;
}
