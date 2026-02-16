import { useState, useEffect } from 'react';
import { empresasApi } from '../../api/empresas';
import PageHeader from '../../components/ui/PageHeader';
import StatCard from '../../components/ui/StatCard';
import DataTable from '../../components/ui/DataTable';
import Modal from '../../components/ui/Modal';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import type { Empresa, EmpresaEstadisticas } from '../../types/empresa';

export default function EmpresasList() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [stats, setStats] = useState<EmpresaEstadisticas | null>(null);
  const [auditores, setAuditores] = useState<string[]>([]);
  const [grupos, setGrupos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filtroAuditor, setFiltroAuditor] = useState('');
  const [filtroGrupo, setFiltroGrupo] = useState('');
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState<Empresa | null>(null);

  // Form state
  const [formRut, setFormRut] = useState('');
  const [formNombre, setFormNombre] = useState('');
  const [formAuditor, setFormAuditor] = useState('');
  const [formGrupo, setFormGrupo] = useState('');
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');

  const loadData = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { pagina, por_pagina: 50 };
      if (search) params.busqueda = search;
      if (filtroAuditor) params.auditor = filtroAuditor;
      if (filtroGrupo) params.grupo = filtroGrupo;

      const [data, statsData, auditoresData, gruposData] = await Promise.all([
        empresasApi.list(params),
        empresasApi.estadisticas(),
        empresasApi.auditores(),
        empresasApi.grupos(),
      ]);

      setEmpresas(data.empresas);
      setTotalPaginas(data.total_paginas);
      setStats(statsData);
      setAuditores(auditoresData);
      setGrupos(gruposData);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [pagina, filtroAuditor, filtroGrupo]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPagina(1);
    loadData();
  };

  const openCreate = () => {
    setFormMode('create');
    setFormRut(''); setFormNombre(''); setFormAuditor(''); setFormGrupo('');
    setModalOpen(true);
  };

  const openEdit = (emp: Empresa) => {
    setFormMode('edit');
    setSelectedEmpresa(emp);
    setFormRut(emp.run_rut);
    setFormNombre(emp.empresa || '');
    setFormAuditor(emp.auditor || '');
    setFormGrupo(emp.grupo || '');
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      if (formMode === 'create') {
        await empresasApi.create({
          run_rut: formRut, empresa: formNombre, auditor: formAuditor, grupo: formGrupo,
        });
      } else {
        await empresasApi.update(formRut, {
          empresa: formNombre, auditor: formAuditor, grupo: formGrupo,
        });
      }
      setModalOpen(false);
      loadData();
    } catch {
      // handle error
    }
  };

  const columns = [
    {
      key: 'run_rut', header: 'RUT',
      render: (e: Empresa) => <span className="font-mono" style={{ fontWeight: 600 }}>{e.run_rut}</span>,
    },
    { key: 'empresa', header: 'Empresa' },
    {
      key: 'auditor', header: 'Auditor',
      render: (e: Empresa) => e.auditor ? <span className="badge badge-primary">{e.auditor}</span> : <span className="text-muted">-</span>,
    },
    {
      key: 'grupo', header: 'Grupo',
      render: (e: Empresa) => e.grupo ? <span className="badge badge-blue">{e.grupo}</span> : <span className="text-muted">-</span>,
    },
    {
      key: 'tiene_credencial', header: 'Credencial',
      render: (e: Empresa) => e.tiene_credencial
        ? <span className="badge badge-teal"><i className="fas fa-check" style={{ marginRight: '4px' }} />Si</span>
        : <span className="badge badge-outline"><i className="fas fa-times" style={{ marginRight: '4px' }} />No</span>,
    },
    {
      key: 'acciones', header: 'Acciones',
      render: (e: Empresa) => (
        <button className="btn btn-sm btn-outline" onClick={(ev) => { ev.stopPropagation(); openEdit(e); }}>
          <i className="fas fa-edit" /> Editar
        </button>
      ),
    },
  ];

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Empresas"
        subtitle="Gestion de cartera de clientes"
        icon="fas fa-building"
        actions={
          <button className="btn btn-gradient" onClick={openCreate}>
            <i className="fas fa-plus" /> Nueva Empresa
          </button>
        }
      />

      {/* Stats */}
      {stats && (
        <div className="grid grid-4 mb-3">
          <StatCard value={stats.total_empresas} label="Total Empresas" icon="fas fa-building" gradient="var(--gradient-primary)" />
          <StatCard value={stats.total_auditores} label="Auditores" icon="fas fa-user-tie" gradient="var(--color-teal)" />
          <StatCard value={stats.con_credencial} label="Con Credencial" icon="fas fa-check-circle" gradient="var(--color-blue)" />
          <StatCard value={stats.sin_credencial} label="Sin Credencial" icon="fas fa-exclamation-triangle" gradient="var(--color-orange)" />
        </div>
      )}

      {/* Filters */}
      <div className="card mb-3">
        <div className="card-body">
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'end' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <div className="search-bar" style={{ maxWidth: 'none' }}>
                <i className="fas fa-search icon" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar por RUT o nombre..."
                />
              </div>
            </div>
            <select
              className="form-control form-select"
              value={filtroAuditor}
              onChange={(e) => { setFiltroAuditor(e.target.value); setPagina(1); }}
              style={{ width: '200px' }}
            >
              <option value="">Todos los auditores</option>
              {auditores.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <select
              className="form-control form-select"
              value={filtroGrupo}
              onChange={(e) => { setFiltroGrupo(e.target.value); setPagina(1); }}
              style={{ width: '200px' }}
            >
              <option value="">Todos los grupos</option>
              {grupos.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
            <button type="submit" className="btn btn-primary">
              <i className="fas fa-search" /> Buscar
            </button>
          </form>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={empresas as unknown as Record<string, unknown>[]}
        loading={loading}
        emptyText="No se encontraron empresas"
        onRowClick={(item) => openEdit(item as unknown as Empresa)}
      />

      {/* Pagination */}
      {totalPaginas > 1 && (
        <div className="flex-center gap-md mt-2">
          <button className="btn btn-sm btn-outline" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
            <i className="fas fa-chevron-left" /> Anterior
          </button>
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Pagina {pagina} de {totalPaginas}
          </span>
          <button className="btn btn-sm btn-outline" disabled={pagina >= totalPaginas} onClick={() => setPagina(pagina + 1)}>
            Siguiente <i className="fas fa-chevron-right" />
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={formMode === 'create' ? 'Nueva Empresa' : 'Editar Empresa'}
        maxWidth="600px"
        footer={
          <>
            <button className="btn btn-outline" onClick={() => setModalOpen(false)}>Cancelar</button>
            <button className="btn btn-gradient" onClick={handleSave}>
              <i className="fas fa-save" /> {formMode === 'create' ? 'Crear' : 'Guardar'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">RUT</label>
          <input
            className="form-control font-mono"
            value={formRut}
            onChange={(e) => setFormRut(e.target.value)}
            disabled={formMode === 'edit'}
            placeholder="Ej: 76.123.456-7"
          />
        </div>
        <div className="form-group">
          <label className="form-label">Nombre Empresa</label>
          <input className="form-control" value={formNombre} onChange={(e) => setFormNombre(e.target.value)} placeholder="Nombre de la empresa" />
        </div>
        <div className="form-group">
          <label className="form-label">Auditor</label>
          <input className="form-control" value={formAuditor} onChange={(e) => setFormAuditor(e.target.value)} placeholder="Auditor asignado" />
        </div>
        <div className="form-group">
          <label className="form-label">Grupo</label>
          <input className="form-control" value={formGrupo} onChange={(e) => setFormGrupo(e.target.value)} placeholder="Grupo empresarial" />
        </div>
      </Modal>
    </div>
  );
}
