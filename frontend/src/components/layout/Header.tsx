import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.nombre_usuario?.substring(0, 2).toUpperCase() || 'US';

  return (
    <header style={{
      background: '#1a1a1a',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      padding: '12px 24px',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        maxWidth: '1400px',
        margin: '0 auto',
      }}>
        {/* Logo */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #7A007B 0%, #E13278 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '20px',
            color: 'white',
            fontWeight: 700,
          }}>
            E
          </div>
          <div>
            <div style={{ color: 'white', fontSize: '18px', fontWeight: 700, letterSpacing: '0.3px' }}>
              Evolve Soluciones
            </div>
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', fontWeight: 500 }}>
              Inteligencia Tributaria
            </div>
          </div>
        </div>

        {/* Right section */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            style={{
              width: '44px',
              height: '44px',
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              color: theme === 'dark' ? '#6366F1' : '#F59E0B',
              fontSize: '18px',
            }}
          >
            <i className={theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun'} />
          </button>

          {/* User badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '8px 16px',
            background: 'rgba(255,255,255,0.08)',
            backdropFilter: 'blur(10px)',
            borderRadius: '14px',
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #7A007B 0%, #E13278 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '13px',
              fontWeight: 700,
            }}>
              {initials}
            </div>
            <div>
              <div style={{ color: 'white', fontSize: '14px', fontWeight: 600 }}>
                {user?.nombre_usuario}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px' }}>
                {user?.rol === 'administrador' ? 'Administrador' : 'Usuario'}
              </div>
            </div>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            style={{
              background: '#E13278',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '10px',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: 500,
              fontFamily: 'var(--font-family)',
              transition: 'all 0.3s ease',
            }}
          >
            <i className="fas fa-sign-out-alt" />
            <span className="logout-text">Salir</span>
          </button>
        </div>
      </div>
    </header>
  );
}
