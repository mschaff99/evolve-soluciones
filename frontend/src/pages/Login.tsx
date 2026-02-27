import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await authApi.login({
        nombre_usuario: username,
        contraseña: password,
      });
      setAuth(data.usuario, data.access_token, data.refresh_token);
      navigate('/');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Error al iniciar sesion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      background: '#000000',
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: window.innerWidth > 768 ? '1fr 1fr' : '1fr',
        maxWidth: '1200px',
        width: '100%',
        background: '#1a1a1a',
        borderRadius: '24px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
        overflow: 'hidden',
        minHeight: '700px',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        {/* Left - Login Form */}
        <div style={{ padding: '48px 40px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <div style={{
              width: '80px',
              height: '80px',
              background: 'linear-gradient(135deg, #7A007B 0%, #E13278 100%)',
              borderRadius: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '36px',
              color: 'white',
              margin: '0 auto 20px',
              fontWeight: 800,
            }}>
              E
            </div>
            <h1 style={{ color: 'white', fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
              Evolve Soluciones
            </h1>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '999px',
              fontSize: '12px',
              color: 'rgba(255,255,255,0.7)',
            }}>
              <span style={{
                width: '6px', height: '6px', borderRadius: '50%', background: '#E13278',
              }} />
              Plataforma de Inteligencia Tributaria
            </div>
          </div>

          <h2 style={{ color: 'white', fontSize: '22px', fontWeight: 600, marginBottom: '8px' }}>
            Iniciar Sesion
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px', marginBottom: '32px' }}>
            Ingresa tus credenciales para acceder
          </p>

          {error && (
            <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
              <i className="fas fa-exclamation-circle" style={{ marginRight: '8px' }} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block', color: 'rgba(255,255,255,0.7)', fontSize: '13px',
                fontWeight: 600, marginBottom: '8px', letterSpacing: '0.5px',
              }}>
                USUARIO
              </label>
              <div style={{ position: 'relative' }}>
                <i className="fas fa-user" style={{
                  position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
                  color: 'rgba(255,255,255,0.4)', fontSize: '14px',
                }} />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Ingresa tu usuario"
                  required
                  style={{
                    width: '100%',
                    padding: '14px 16px 14px 42px',
                    border: '2px solid rgba(255,255,255,0.06)',
                    borderRadius: '16px',
                    background: 'rgba(0,0,0,0.25)',
                    color: 'white',
                    fontSize: '15px',
                    fontFamily: 'var(--font-family)',
                    outline: 'none',
                    transition: 'border-color 0.15s ease',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#7A007B'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.06)'}
                />
              </div>
            </div>

            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'block', color: 'rgba(255,255,255,0.7)', fontSize: '13px',
                fontWeight: 600, marginBottom: '8px', letterSpacing: '0.5px',
              }}>
                CONTRASENA
              </label>
              <div style={{ position: 'relative' }}>
                <i className="fas fa-lock" style={{
                  position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
                  color: 'rgba(255,255,255,0.4)', fontSize: '14px',
                }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Ingresa tu contrasena"
                  required
                  style={{
                    width: '100%',
                    padding: '14px 48px 14px 42px',
                    border: '2px solid rgba(255,255,255,0.06)',
                    borderRadius: '16px',
                    background: 'rgba(0,0,0,0.25)',
                    color: 'white',
                    fontSize: '15px',
                    fontFamily: 'var(--font-family)',
                    outline: 'none',
                    transition: 'border-color 0.15s ease',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#7A007B'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.06)'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
                    cursor: 'pointer', fontSize: '14px',
                  }}
                >
                  <i className={showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'} />
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '16px',
                background: loading ? '#555' : 'linear-gradient(135deg, #7A007B 0%, #E13278 100%)',
                border: 'none',
                borderRadius: '16px',
                color: 'white',
                fontSize: '16px',
                fontWeight: 600,
                fontFamily: 'var(--font-family)',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
              }}
            >
              {loading ? (
                <>
                  <div style={{
                    width: '20px', height: '20px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTopColor: 'white',
                    borderRadius: '50%',
                    animation: 'spin 1s ease-in-out infinite',
                  }} />
                  Iniciando sesion...
                </>
              ) : (
                <>
                  <i className="fas fa-sign-in-alt" />
                  Iniciar Sesion
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right - Features */}
        <div style={{
          background: '#000000',
          padding: '48px 40px',
          borderLeft: '1px solid rgba(255,255,255,0.06)',
          position: 'relative',
          overflow: 'hidden',
          display: window.innerWidth > 768 ? 'flex' : 'none',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          {/* Gradient orbs */}
          <div style={{
            position: 'absolute', width: '400px', height: '400px',
            background: '#7A007B', borderRadius: '50%',
            filter: 'blur(80px)', opacity: 0.15, top: '-100px', left: '-100px',
            pointerEvents: 'none',
          }} />
          <div style={{
            position: 'absolute', width: '300px', height: '300px',
            background: '#16A39A', borderRadius: '50%',
            filter: 'blur(80px)', opacity: 0.15, bottom: '-50px', right: '-50px',
            pointerEvents: 'none',
          }} />

          <div style={{ position: 'relative', zIndex: 1 }}>
            <h2 style={{ color: 'white', fontSize: '24px', fontWeight: 700, marginBottom: '8px' }}>
              Todo en un solo lugar
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px', marginBottom: '32px' }}>
              Gestiona tu informacion tributaria de forma inteligente
            </p>

            <div style={{ display: 'grid', gap: '12px' }}>
              {[
                { icon: 'fas fa-chart-line', color: '#16A39A', title: 'Formulario F29', desc: 'Consulta y analisis integral' },
                { icon: 'fas fa-file-alt', color: '#2268AD', title: 'Declaraciones Juradas', desc: 'Control y seguimiento completo' },
                { icon: 'fas fa-building', color: '#E13278', title: 'Gestion de Empresas', desc: 'Administra tu cartera de clientes' },
                { icon: 'fas fa-robot', color: '#53BED3', title: 'Inteligencia Artificial', desc: 'Analisis con IA avanzada' },
                { icon: 'fas fa-shield-alt', color: '#16A39A', title: 'Situacion Tributaria', desc: 'Estado actualizado del SII' },
              ].map((feat, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '14px',
                  padding: '16px',
                  background: 'rgba(0,0,0,0.25)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '14px',
                  transition: 'all 0.3s ease',
                }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '10px',
                    background: feat.color, display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: '18px', color: 'white', flexShrink: 0,
                  }}>
                    <i className={feat.icon} />
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: 'white' }}>{feat.title}</div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>{feat.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
