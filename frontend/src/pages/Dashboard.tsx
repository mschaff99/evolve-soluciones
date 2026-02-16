import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { empresasApi } from '../api/empresas';
import { authApi } from '../api/auth';
import StatCard from '../components/ui/StatCard';
import PageHeader from '../components/ui/PageHeader';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import type { EmpresaEstadisticas } from '../types/empresa';
import type { Modulo } from '../types/auth';

export default function Dashboard() {
  const { user, setModules } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<EmpresaEstadisticas | null>(null);
  const [modules, setLocalModules] = useState<Modulo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsData, modulesData] = await Promise.all([
          empresasApi.estadisticas().catch(() => null),
          authApi.getModules().catch(() => []),
        ]);
        if (statsData) setStats(statsData);
        setLocalModules(modulesData);
        setModules(modulesData);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [setModules]);

  if (loading) return <LoadingSpinner text="Cargando dashboard..." />;

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Buenos dias' : now.getHours() < 18 ? 'Buenas tardes' : 'Buenas noches';

  // Quick access items
  const quickAccess = [
    { icon: 'fas fa-building', color: '#7A007B', title: 'Empresas', desc: 'Gestion de cartera', path: '/empresas' },
    { icon: 'fas fa-chart-line', color: '#16A39A', title: 'Formulario F29', desc: 'Consulta integral', path: '/f29' },
    { icon: 'fas fa-file-alt', color: '#2268AD', title: 'Declaraciones Juradas', desc: 'DJ integral', path: '/dj' },
    { icon: 'fas fa-shield-alt', color: '#E13278', title: 'Situacion Tributaria', desc: 'Estado SII', path: '/situacion-tributaria' },
    { icon: 'fas fa-robot', color: '#53BED3', title: 'Inteligencia Artificial', desc: 'Analisis con IA', path: '/ia' },
  ];

  return (
    <div className="animate-fade-in">
      <PageHeader
        title={`${greeting}, ${user?.nombre_usuario}`}
        subtitle={`Base de datos: ${user?.base_datos_mysql || 'No asignada'}`}
        icon="fas fa-home"
      />

      {/* Stats */}
      {stats && (
        <div className="grid grid-4 mb-3">
          <StatCard
            value={stats.total_empresas}
            label="Empresas"
            icon="fas fa-building"
            gradient="var(--gradient-primary)"
          />
          <StatCard
            value={stats.total_auditores}
            label="Auditores"
            icon="fas fa-user-tie"
            gradient="var(--color-teal)"
          />
          <StatCard
            value={stats.con_credencial}
            label="Con Credencial"
            icon="fas fa-check-circle"
            gradient="var(--color-blue)"
          />
          <StatCard
            value={stats.sin_credencial}
            label="Sin Credencial"
            icon="fas fa-exclamation-triangle"
            gradient="var(--color-orange)"
          />
        </div>
      )}

      {/* Quick Access */}
      <div className="card mb-3">
        <div className="card-header">
          <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
            <i className="fas fa-bolt" style={{ marginRight: '10px', color: 'var(--color-primary)' }} />
            Acceso Rapido
          </h3>
        </div>
        <div className="card-body">
          <div className="grid grid-3" style={{ gap: '12px' }}>
            {quickAccess.map((item, i) => (
              <button
                key={i}
                className="quick-access-btn"
                onClick={() => navigate(item.path)}
              >
                <div className="quick-access-icon" style={{ background: item.color }}>
                  <i className={item.icon} />
                </div>
                <div className="quick-access-text">
                  <h4>{item.title}</h4>
                  <p>{item.desc}</p>
                </div>
                <div className="quick-access-arrow">
                  <i className="fas fa-arrow-right" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Modules info */}
      {modules.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
              <i className="fas fa-puzzle-piece" style={{ marginRight: '10px', color: 'var(--color-teal)' }} />
              Modulos Habilitados
            </h3>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {modules.map((m) => (
                <span key={m.id} className="badge badge-gradient" style={{ padding: '8px 14px', fontSize: '13px' }}>
                  <i className={m.icono || 'fas fa-cube'} style={{ marginRight: '6px' }} />
                  {m.nombre}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
