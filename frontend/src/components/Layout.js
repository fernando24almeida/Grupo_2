import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { 
  Layout as LayoutIcon, 
  UserPlus, 
  Clipboard, 
  Settings, 
  LogOut, 
  Activity,
  UserCog,
  BarChart3
} from 'lucide-react';

const Layout = ({ children }) => {
  const { utilizador, sair } = usarAutenticacao();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    sair();
    navigate('/login');
  };

  if (!utilizador) return <>{children}</>;

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutIcon, roles: ['ADMIN', 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA'] },
    { path: '/new-episode', label: 'Admissão', icon: UserPlus, roles: ['ADMIN', 'RECECIONISTA'] },
    { path: '/triage', label: 'Triagem', icon: Activity, roles: ['ENFERMEIRO'] },
    { path: '/clinical-acts', label: 'Atos Clínicos', icon: Clipboard, roles: ['MEDICO'] },
    { path: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['ADMIN', 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA'] },
  ];

  if (utilizador.role === 'ADMIN') {
    menuItems.push({ path: '/admin', label: 'Administração', icon: UserCog, roles: ['ADMIN'] });
  }

  const filteredMenuItems = menuItems.filter(item => item.roles.includes(utilizador.role));

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo">
          <Activity size={28} />
          <span>Gestão Clínica</span>
        </div>
        
        <nav className="nav-links">
          {filteredMenuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info" style={{ marginBottom: '1rem', padding: '0 1rem', fontSize: '0.875rem', color: '#94a3b8' }}>
            <p style={{ color: 'white', fontWeight: 600 }}>{utilizador.nome_utilizador}</p>
            <p>{utilizador.hospital}</p>
          </div>
          <button onClick={handleLogout} className="nav-item" style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer' }}>
            <LogOut size={20} />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;
