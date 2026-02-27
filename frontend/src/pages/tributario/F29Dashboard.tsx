import { useState, useEffect } from 'react';
import { f29Api } from '../../api/tributario';
import PageHeader from '../../components/ui/PageHeader';
import StatCard from '../../components/ui/StatCard';
import DataTable from '../../components/ui/DataTable';
import Modal from '../../components/ui/Modal';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import type { F29Empresa, F29Datos } from '../../types/tributario';

export default function F29Dashboard() {
  const [empresas, setEmpresas] = useState<F29Empresa[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [periodos, setPeriodos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filtroAuditor, setFiltroAuditor] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState<F29Empresa | null>(null);
  const [datosF29, setDatosF29] = useState<F29Datos | null>(null);
  const [loadingDatos, setLoadingDatos] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [empresasData, statsData, periodosData] = await Promise.all([
          f29Api.empresas(),
          f29Api.estadisticas(),
          f29Api.periodos(),
        ]);
        setEmpresas(empresasData);
        setStats(statsData);
        setPeriodos(periodosData);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search) params.busqueda = search;
      if (filtroAuditor) params.auditor = filtroAuditor;
      const data = await f29Api.empresas(params);
      setEmpresas(data);
    } finally {
      setLoading(false);
    }
  };

  const openDatos = async (empresa: F29Empresa) => {
    setSelectedEmpresa(empresa);
    setModalOpen(true);
    if (empresa.ultimo_periodo) {
      setLoadingDatos(true);
      try {
        const datos = await f29Api.datos(empresa.run_rut, empresa.ultimo_periodo);
        setDatosF29(datos);
      } catch {
        setDatosF29(null);
      } finally {
        setLoadingDatos(false);
      }
    }
  };

  const columns = [
    {
      key: 'run_rut', header: 'RUT',
      render: (e: F29Empresa) => <span className="font-mono" style={{ fontWeight: 600 }}>{e.run_rut}</span>,
    },
    { key: 'empresa', header: 'Empresa' },
    {
      key: 'auditor', header: 'Auditor',
      render: (e: F29Empresa) => e.auditor ? <span className="badge badge-primary">{e.auditor}</span> : <span className="text-muted">-</span>,
    },
    {
      key: 'total_periodos', header: 'Periodos',
      render: (e: F29Empresa) => (
        <span className="badge badge-teal">{e.total_periodos}</span>
      ),
    },
    {
      key: 'ultimo_periodo', header: 'Ultimo Periodo',
      render: (e: F29Empresa) => e.ultimo_periodo
        ? <span className="badge badge-blue">{e.ultimo_periodo}</span>
        : <span className="text-muted">Sin datos</span>,
    },
    {
      key: 'acciones', header: 'Acciones',
      render: (e: F29Empresa) => (
        <button className="btn btn-sm btn-gradient" onClick={(ev) => { ev.stopPropagation(); openDatos(e); }}>
          <i className="fas fa-eye" /> Ver
        </button>
      ),
    },
  ];

  if (loading) return <LoadingSpinner text="Cargando Formulario F29..." />;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Formulario F29"
        subtitle="Consulta integral de formularios F29"
        icon="fas fa-chart-line"
      />

      {/* Stats */}
      <div className="grid grid-4 mb-3">
        <StatCard value={stats.total_empresas || 0} label="Empresas" icon="fas fa-building" gradient="var(--gradient-primary)" />
        <StatCard value={stats.total_periodos || 0} label="Periodos" icon="fas fa-calendar" gradient="var(--color-teal)" />
        <StatCard value={stats.con_observaciones || 0} label="Con Datos" icon="fas fa-check-circle" gradient="var(--color-blue)" />
        <StatCard value={periodos.length} label="Periodos Unicos" icon="fas fa-clock" gradient="var(--color-cyan)" />
      </div>

      {/* Search */}
      <div className="card mb-3">
        <div className="card-body">
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <div className="search-bar" style={{ maxWidth: 'none' }}>
                <i className="fas fa-search icon" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar por RUT o nombre..."
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleSearch}>
              <i className="fas fa-search" /> Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={empresas as unknown as Record<string, unknown>[]}
        loading={loading}
        emptyText="No se encontraron datos F29"
        onRowClick={(item) => openDatos(item as unknown as F29Empresa)}
      />

      {/* Detail Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setDatosF29(null); }}
        title={`F29 - ${selectedEmpresa?.empresa || selectedEmpresa?.run_rut || ''}`}
        maxWidth="1200px"
      >
        {loadingDatos ? (
          <LoadingSpinner text="Cargando datos F29..." />
        ) : datosF29 ? (
          <div>
            <div className="flex-between mb-2">
              <div>
                <span className="badge badge-primary" style={{ marginRight: '8px' }}>
                  RUT: {datosF29.rut}
                </span>
                <span className="badge badge-teal">
                  Periodo: {datosF29.periodo}
                </span>
              </div>
            </div>

            {/* Periodos buttons */}
            {selectedEmpresa && selectedEmpresa.periodos.length > 1 && (
              <div className="mb-2" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {selectedEmpresa.periodos.slice(0, 12).map((p) => (
                  <button
                    key={p}
                    className={`btn btn-sm ${p === datosF29.periodo ? 'btn-gradient' : 'btn-outline'}`}
                    onClick={async () => {
                      setLoadingDatos(true);
                      try {
                        const d = await f29Api.datos(selectedEmpresa.run_rut, p);
                        setDatosF29(d);
                      } finally {
                        setLoadingDatos(false);
                      }
                    }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}

            {/* Data display */}
            <div className="card">
              <div className="card-body" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {typeof datosF29.datos === 'object' && Object.keys(datosF29.datos).length > 0 ? (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Codigo</th>
                        <th>Valor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(datosF29.datos).map(([key, val]) => (
                        <tr key={key}>
                          <td className="font-mono" style={{ fontWeight: 600 }}>{key}</td>
                          <td>{String(val)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-muted text-center" style={{ padding: '20px' }}>
                    Datos disponibles en formato raw
                  </p>
                )}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-muted text-center" style={{ padding: '40px' }}>
            <i className="fas fa-inbox" style={{ fontSize: '32px', display: 'block', marginBottom: '12px' }} />
            No hay datos F29 disponibles para esta empresa
          </p>
        )}
      </Modal>
    </div>
  );
}
