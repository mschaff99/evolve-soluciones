/**
 * Página de Login
 * ===============
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { login, clearError } from '@/store/slices/authSlice';
import { Button } from '@/components/Button';

export const LoginPage: React.FC = () => {
  const [credentials, setCredentials] = useState({
    nombre_usuario: '',
    contrasena: '',
  });

  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isLoading, error, isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Limpiar errores al montar el componente
    dispatch(clearError());
  }, [dispatch]);

  useEffect(() => {
    // Redirigir si ya está autenticado
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!credentials.nombre_usuario || !credentials.contrasena) {
      return;
    }

    await dispatch(login(credentials));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>Evolve Soluciones</h1>
            <p>Sistema de Gestión Empresarial</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {error && (
              <div className="alert alert-danger">
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="nombre_usuario">Usuario</label>
              <input
                type="text"
                id="nombre_usuario"
                name="nombre_usuario"
                value={credentials.nombre_usuario}
                onChange={handleChange}
                placeholder="Ingrese su usuario"
                disabled={isLoading}
                autoComplete="username"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                type="password"
                id="contrasena"
                name="contrasena"
                value={credentials.contrasena}
                onChange={handleChange}
                placeholder="Ingrese su contraseña"
                disabled={isLoading}
                autoComplete="current-password"
                required
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              className="btn-block"
            >
              {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>

          <div className="login-footer">
            <p>v2.0.0 - React + Flask API</p>
          </div>
        </div>
      </div>
    </div>
  );
};
