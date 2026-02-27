export interface Empresa {
  run_rut: string;
  empresa: string | null;
  auditor: string | null;
  grupo: string | null;
  tiene_credencial: boolean;
  rut_credencial: string | null;
}

export interface EmpresasPaginadas {
  empresas: Empresa[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
}

export interface EmpresaEstadisticas {
  total_empresas: number;
  total_auditores: number;
  total_grupos: number;
  con_credencial: number;
  sin_credencial: number;
}
