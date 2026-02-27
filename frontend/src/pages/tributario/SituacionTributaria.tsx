import { useState, useEffect } from 'react';
import { situacionApi } from '../../api/tributario';
import PageHeader from '../../components/ui/PageHeader';
import DataTable from '../../components/ui/DataTable';
import Modal from '../../components/ui/Modal';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import type { SituacionEmpresa, SituacionTributaria as SitTrib } from '../../types/tributario';

export default function SituacionTributaria() {
  const [empresas, setEmpresas] = useState<SituacionEmpresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState<SituacionEmpresa | null>(null);
  const [situacion, setSituacion] = useState<SitTrib | null>(null);
  const [loadingSit, setLoadingSit] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await situacionApi.empresas();
        setEmpresas(data);
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
      const data = await situacionApi.empresas(params);
      setEmpresas(data);
    } finally {
      setLoading(false);
    }
  };

  const openSituacion = async (empresa: SituacionEmpresa) => {
    setSelectedEmpresa(empresa);
    setModalOpen(true);
    setLoadingSit(true);
    try {
      const data = await situacionApi.get(empresa.run_rut);
      setSituacion(data);
    } catch {
      setSituacion(null);
    } finally {
      setLoadingSit(false);
    }
  };

  const columns = [
    {
      key: 'run_rut', header: 'RUT',
      render: (e: SituacionEmpresa) => <span className="font-mono" style={{ fontWeight: 600 }}>{e.run_rut}</span>,
    },
    { key: 'empresa', header: 'Empresa' },
    {
      key: 'auditor', header: 'Auditor',
      render: (e: SituacionEmpresa) => e.auditor ? <span className="badge badge-primary">{e.auditor}</span> : <span className="text-muted">-</span>,
    },
    {
      key: 'tiene_situacion', header: 'Estado',
      render: (e: SituacionEmpresa) => e.tiene_situacion
        ? <span className="badge badge-teal"><i className="fas fa-check" style={{ marginRight: '4px' }} />Disponible</span>
        : <span className="badge badge-outline">Sin datos</span>,
    },
    {
      key: 'acciones', header: 'Acciones',
      render: (e: SituacionEmpresa) => (
        <button className="btn btn-sm btn-gradient" onClick={(ev) => { ev.stopPropagation(); openSituacion(e); }}>
          <i className="fas fa-eye" /> Ver
        </button>
      ),
    },
  ];

  if (loading) return <LoadingSpinner text="Cargando Situacion Tributaria..." />;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Situacion Tributaria"
        subtitle="Estado tributario de empresas ante el SII"
        icon="fas fa-shield-alt"
      />

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
        emptyText="No se encontraron datos de situacion tributaria"
        onRowClick={(item) => openSituacion(item as unknown as SituacionEmpresa)}
      />

      {/* Detail Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setSituacion(null); }}
        title={`Situacion Tributaria - ${selectedEmpresa?.empresa || selectedEmpresa?.run_rut || ''}`}
        maxWidth="900px"
      >
        {loadingSit ? (
          <LoadingSpinner text="Cargando situacion tributaria..." />
        ) : situacion ? (
          <div>
            <div className="grid grid-2 mb-2">
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-muted mb-1">Razon Social</div>
                  <div style={{ fontWeight: 600, fontSize: '16px' }}>{situacion.razon_social || '-'}</div>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-muted mb-1">Estado Contribuyente</div>
                  <div>
                    <span className={`badge ${situacion.estado_contribuyente?.toLowerCase().includes('activ') ? 'badge-teal' : 'badge-orange'}`}
                      style={{ fontSize: '14px', padding: '6px 12px' }}>
                      {situacion.estado_contribuyente || '-'}
                    </span>
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-muted mb-1">Inicio Actividades</div>
                  <div style={{ fontWeight: 600 }}>{situacion.inicio_actividades || '-'}</div>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-muted mb-1">RUT</div>
                  <div className="font-mono" style={{ fontWeight: 600, fontSize: '16px' }}>{situacion.rut}</div>
                </div>
              </div>
            </div>

            {/* Additional data */}
            {Object.keys(situacion.datos_adicionales).length > 0 && (
              <div className="card">
                <div className="card-header">
                  <h4 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>
                    <i className="fas fa-info-circle" style={{ marginRight: '8px', color: 'var(--color-cyan)' }} />
                    Datos Adicionales
                  </h4>
                </div>
                <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Campo</th>
                        <th>Valor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(situacion.datos_adicionales).map(([key, val]) => (
                        <tr key={key}>
                          <td style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}
                          </td>
                          <td>{typeof val === 'object' ? JSON.stringify(val) : String(val ?? '-')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted text-center" style={{ padding: '40px' }}>
            <i className="fas fa-inbox" style={{ fontSize: '32px', display: 'block', marginBottom: '12px' }} />
            No hay datos de situacion tributaria disponibles
          </p>
        )}
      </Modal>
    </div>
  );
}
