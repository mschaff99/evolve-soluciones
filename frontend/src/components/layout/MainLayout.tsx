import { Outlet } from 'react-router-dom';
import Header from './Header';

export default function MainLayout() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <Header />
      <main style={{
        minHeight: 'calc(100vh - 80px)',
        position: 'relative',
      }}>
        {/* Background gradient overlay - like original */}
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 30%, rgba(22, 163, 154, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(225, 50, 120, 0.05) 0%, transparent 50%)
          `,
          opacity: 'var(--bg-gradient-opacity)',
          pointerEvents: 'none',
          zIndex: 0,
        }} />
        <div style={{
          position: 'relative',
          zIndex: 1,
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '24px',
        }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
