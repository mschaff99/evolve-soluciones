/**
 * Página de Dashboard
 * ===================
 */
import React from 'react';
import { useAppSelector } from '@/store/hooks';

export const DashboardPage: React.FC = () => {
  const { usuario } = useAppSelector((state) => state.auth);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Bienvenido, {usuario?.nombre_usuario}</p>
      </div>

      <div className="dashboard-content">
        <div className="info-card">
          <h2>Sistema Evolve Soluciones</h2>
          <p>Base de datos: {usuario?.base_datos_mysql || 'No asignada'}</p>
          <p>Rol: {usuario?.rol}</p>
        </div>

        <div className="modules-card">
          <h3>Módulos Disponibles</h3>
          {usuario?.modulos && usuario.modulos.length > 0 ? (
            <ul>
              {usuario.modulos.map((modulo) => (
                <li key={modulo.slug}>{modulo.nombre}</li>
              ))}
            </ul>
          ) : (
            <p>No hay módulos disponibles</p>
          )}
        </div>
      </div>
    </div>
  );
};
