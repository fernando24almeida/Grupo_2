import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { usarAutenticacao } from '../services/AuthContext';
import { 
  Layout as LayoutIcon, 
  UserPlus, 
  Clipboard, 
  Settings, 
  LogOut, 
  Activity,
  UserCog,
  BarChart3,
  User,
  Hotel
} from 'lucide-react';

const Layout = ({ children }) => {
  const { utilizador, hospital, definirHospital, sair } = usarAutenticacao();
  const location = useLocation();
  const navigate = useNavigate();
  const [listaHospitais, setListaHospitais] = useState([]);

  useEffect(() => {
    if (utilizador && utilizador.role !== 'UTENTE') {
      const carregarHospitais = async () => {
        try {
          const res = await axios.get('/clinical/hospitals');
          setListaHospitais(res.data);
        } catch (e) {
          console.error('Erro ao carregar lista de hospitais no Layout', e);
        }
      };
      carregarHospitais();
    }
  }, [utilizador]);

  const handleLogout = () => {
    sair();
    navigate('/login');
  };

  const handleHospitalChange = (e) => {
    const novoHosp = e.target.value;
    definirHospital(novoHosp === 'todos' ? null : novoHosp);
  };

  if (!utilizador) return <>{children}</>;

  const menuItems = [
    { path: '/dashboard', label: utilizador.role === 'UTENTE' ? 'Meus Episódios' : 'Visão Geral', icon: LayoutIcon, roles: ['ADMIN', 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA', 'UTENTE'] },
    { path: '/new-episode', label: 'Admissão', icon: UserPlus, roles: ['ADMIN', 'RECECIONISTA'] },
    { path: '/triage', label: 'Triagem', icon: Activity, roles: ['ENFERMEIRO'] },
    { path: '/clinical-acts', label: 'Atos Clínicos', icon: Clipboard, roles: ['MEDICO'] },
    { path: '/analytics', label: 'Analítica', icon: BarChart3, roles: ['ADMIN', 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA'] },
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

        {/* Global Hospital Selector for Staff/Admin */}
        {utilizador.role !== 'UTENTE' && (
          <div className="hospital-selector-container" style={{ padding: '0 15px 20px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              background: '#1e293b', 
              padding: '10px', 
              borderRadius: '8px',
              border: '1px solid #334155'
            }}>
              <Hotel size={18} color="#94a3b8" />
              <select 
                value={hospital || 'todos'} 
                onChange={handleHospitalChange}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: 'white', 
                  fontSize: '0.85rem', 
                  width: '100%',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                {utilizador.role === 'ADMIN' && (
                  <option value="todos" style={{ background: '#1e293b' }}>Todos os Hospitais</option>
                )}
                {listaHospitais.map(h => (
                  <option key={h.nome_hosp} value={h.nome_hosp} style={{ background: '#1e293b' }}>
                    {h.nome_hosp}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
        
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
          <Link
            to="/profile"
            className={`nav-item ${location.pathname === '/profile' ? 'active' : ''}`}
            style={{ marginBottom: '0.5rem' }}
          >
            <User size={20} />
            <span>O Meu Perfil</span>
          </Link>
          <div className="user-info" style={{ marginBottom: '1rem', padding: '0 1rem', fontSize: '0.875rem', color: '#94a3b8' }}>
            <p style={{ color: 'white', fontWeight: 600 }}>{utilizador.nome_utilizador}</p>
            <p style={{ fontSize: '0.75rem', opacity: 0.8 }}>{utilizador.role}</p>
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
