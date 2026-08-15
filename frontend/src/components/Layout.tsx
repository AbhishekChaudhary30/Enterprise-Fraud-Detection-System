import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/history', label: 'History', icon: '📜' },
  { path: '/predict', label: 'Predict', icon: '🎯' },
  { path: '/batch', label: 'Batch', icon: '📁' },
  { path: '/investigations', label: 'Investigations', icon: '🔍' },
  { path: '/models', label: 'Models', icon: '🧠' },
  { path: '/monitoring', label: 'Monitoring', icon: '📡' },
];

export default function Layout() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="app-container">
      {/* Mobile Header */}
      <div className="mobile-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '20px' }}>🛡️</span>
          <h1 style={{ fontSize: '16px', fontWeight: 700, color: '#f1f5f9' }}>Fraud Intelligence</h1>
        </div>
        <button 
          onClick={() => setSidebarOpen(true)}
          style={{ background: 'transparent', border: 'none', color: '#f1f5f9', fontSize: '24px', cursor: 'pointer' }}
        >
          ☰
        </button>
      </div>

      {/* Sidebar Overlay for Mobile */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} 
        onClick={closeSidebar}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div style={{ padding: '24px 20px', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>🛡️</span>
            <div>
              <h1 style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.02em' }}>
                Fraud Intelligence
              </h1>
              <p style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Enterprise Platform</p>
            </div>
          </div>
          {/* Close button for mobile inside sidebar */}
          <button 
            className="mobile-header" 
            style={{ position: 'relative', padding: 0, background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer', zIndex: 60 }}
            onClick={closeSidebar}
          >
            ✕
          </button>
        </div>

        <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '2px', overflowY: 'auto' }}>
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={closeSidebar}
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
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
