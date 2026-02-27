import { useState, useEffect } from 'react';
import { djApi } from '../../api/tributario';
import PageHeader from '../../components/ui/PageHeader';
import StatCard from '../../components/ui/StatCard';
import DataTable from '../../components/ui/DataTable';
import Modal from '../../components/ui/Modal';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import type { DJEmpresa } from '../../types/tributario';

export default function DJDashboard() {
  const [empresas, setEmpresas] = useState<DJEmpresa[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState<DJEmpresa | null>(null);
  const [djData, setDjData] = useState<Record<string, unknown>[]>([]);
  const [loadingDj, setLoadingDj] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [empresasData, statsData] = await Promise.all([
          djApi.empresas(),
          djApi.estadisticas(),
        ]);
        setEmpresas(empresasData);
        setStats(statsData);
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
      const data = await djApi.empresas(params);
      setEmpresas(data);
    } finally {
      setLoading(false);
    }
  };

  const openDJ = async (empresa: DJEmpresa) => {
    setSelectedEmpresa(empresa);
    setModalOpen(true);
    setLoadingDj(true);
    try {
      const data = await djApi.empresa(empresa.run_rut);
      setDjData(data);
    } catch {
      setDjData([]);
    } finally {
      setLoadingDj(false);
    }
  };

  const columns = [
    {
      key: 'run_rut', header: 'RUT',
      render: (e: DJEmpresa) => <span className="font-mono" style={{ fontWeight: 600 }}>{e.run_rut}</span>,
    },
    { key: 'empresa', header: 'Empresa' },
    {
      key: 'auditor', header: 'Auditor',
      render: (e: DJEmpresa) => e.auditor ? <span className="badge badge-primary">{e.auditor}</span> : <span className="text-muted">-</span>,
    },
    {
      key: 'total_dj', header: 'Declaraciones',
      render: (e: DJEmpresa) => (
        <span className={`badge ${e.total_dj > 0 ? 'badge-teal' : 'badge-outline'}`}>
          {e.total_dj}
        </span>
      ),
    },
    {
      key: 'acciones', header: 'Acciones',
      render: (e: DJEmpresa) => (
        <button className="btn btn-sm btn-gradient" onClick={(ev) => { ev.stopPropagation(); openDJ(e); }}>
          <i className="fas fa-eye" /> Ver DJ
        </button>
      ),
    },
  ];

  if (loading) return <LoadingSpinner text="Cargando Declaraciones Juradas..." />;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Declaraciones Juradas"
        subtitle="Consulta integral de DJ"
        icon="fas fa-file-alt"
      />

      {/* Stats */}
      <div className="grid grid-4 mb-3">
        <StatCard value={stats.total_empresas || 0} label="Empresas" icon="fas fa-building" gradient="var(--gradient-primary)" />
        <StatCard value={stats.total_declaraciones || 0} label="Declaraciones" icon="fas fa-file-alt" gradient="var(--color-blue)" />
        <StatCard value={stats.presentadas || 0} label="Presentadas" icon="fas fa-check-circle" gradient="var(--color-teal)" />
        <StatCard value={stats.pendientes || 0} label="Pendientes" icon="fas fa-clock" gradient="var(--color-orange)" />
      </div>

      {/* Search */}
      <div className="card mb-3">
        <div className="card-body">
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1 }}>
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
        emptyText="No se encontraron declaraciones juradas"
        onRowClick={(item) => openDJ(item as unknown as DJEmpresa)}
      />

      {/* DJ Detail Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={`DJ - ${selectedEmpresa?.empresa || selectedEmpresa?.run_rut || ''}`}
        maxWidth="1000px"
      >
        {loadingDj ? (
          <LoadingSpinner text="Cargando declaraciones..." />
        ) : djData.length > 0 ? (
          <div className="table-container overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tipo DJ</th>
                  <th>Periodo</th>
                  <th>Estado</th>
                  <th>Fecha Presentacion</th>
                </tr>
              </thead>
              <tbody>
                {djData.map((dj, idx) => (
                  <tr key={idx}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>
                      {String(dj.tipo_dj || dj.tipo || '-')}
                    </td>
                    <td><span className="badge badge-blue">{String(dj.periodo || '-')}</span></td>
                    <td>
                      <span className={`badge ${dj.estado === 'presentada' ? 'badge-teal' : 'badge-orange'}`}>
                        {String(dj.estado || '-')}
                      </span>
                    </td>
                    <td>{String(dj.fecha_presentacion || dj.fecha || '-')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-muted text-center" style={{ padding: '40px' }}>
            <i className="fas fa-inbox" style={{ fontSize: '32px', display: 'block', marginBottom: '12px' }} />
            No hay declaraciones juradas para esta empresa
          </p>
        )}
      </Modal>
    </div>
  );
}
