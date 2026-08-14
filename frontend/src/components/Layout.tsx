import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/predict', label: 'Predict', icon: '🎯' },
  { path: '/batch', label: 'Batch', icon: '📁' },
  { path: '/investigations', label: 'Investigations', icon: '🔍' },
  { path: '/models', label: 'Models', icon: '🧠' },
  { path: '/monitoring', label: 'Monitoring', icon: '📡' },
];

export default function Layout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{
        width: '240px',
        background: 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)',
        borderRight: '1px solid #334155',
        padding: '0',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: 50,
      }}>
        <div style={{
          padding: '24px 20px',
          borderBottom: '1px solid #334155',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>🛡️</span>
            <div>
              <h1 style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.02em' }}>
                Fraud Intelligence
              </h1>
              <p style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Enterprise Platform</p>
            </div>
          </div>
        </div>

        <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? '#f1f5f9' : '#94a3b8',
                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s ease',
                borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
              })}
            >
              <span style={{ fontSize: '16px' }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ padding: '12px 8px', borderTop: '1px solid #334155' }}>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              fontSize: '13px',
              color: '#94a3b8',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <span>🚪</span> Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        marginLeft: '240px',
        padding: '32px',
        minHeight: '100vh',
        background: '#020617',
      }}>
        <Outlet />
      </main>
    </div>
  );
}
