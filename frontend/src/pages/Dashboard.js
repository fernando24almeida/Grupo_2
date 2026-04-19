import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { 
  UserPlus, 
  Activity, 
  Clipboard, 
  BarChart3, 
  UserCog,
  Clock,
  Users,
  AlertCircle
} from 'lucide-react';

const Dashboard = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();

  const cards = [
    {
      title: 'Administração',
      desc: 'Gerir profissionais, permissões e hospitais.',
      icon: UserCog,
      path: '/admin',
      roles: ['ADMIN'],
      color: '#4f46e5'
    },
    {
      title: 'Admissão',
      desc: 'Registo de admissão de novo utente.',
      icon: UserPlus,
      path: '/new-episode',
      roles: ['ADMIN', 'RECECIONISTA'],
      color: '#2563eb'
    },
    {
      title: 'Triagem',
      desc: 'Triagem de episódios pendentes.',
      icon: Activity,
      path: '/triage',
      roles: ['ENFERMEIRO'],
      color: '#10b981'
    },
    {
      title: 'Atos Clínicos',
      desc: 'Consultas, prescrições e internamentos.',
      icon: Clipboard,
      path: '/clinical-acts',
      roles: ['MEDICO'],
      color: '#8b5cf6'
    },
    {
      title: 'Analytics',
      desc: 'Análise de tempos e fluxos operacionais.',
      icon: BarChart3,
      path: '/analytics',
      roles: ['ADMIN', 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA'],
      color: '#f59e0b'
    }
  ];

  const filteredCards = cards.filter(card => card.roles.includes(utilizador?.role));

  return (
    <div className="dashboard">
      <header className="page-header">
        <div>
          <h1 className="page-title">Bem-vindo, {utilizador?.nome_utilizador}</h1>
          <p style={{ color: 'var(--text-muted)' }}>Hospital: {utilizador?.hospital}</p>
        </div>
        <div className="date-display" style={{ textAlign: 'right' }}>
          <p style={{ fontWeight: 600 }}>{new Date().toLocaleDateString('pt-PT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
      </header>

      {/* Stats Summary */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#dbeafe', color: '#1e40af' }}>
            <Users size={24} />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Utentes em Espera</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>12</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fef3c7', color: '#92400e' }}>
            <Clock size={24} />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Tempo Médio</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>45 min</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fee2e2', color: '#991b1b' }}>
            <AlertCircle size={24} />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Casos Críticos</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>2</p>
          </div>
        </div>
      </div>

      <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-main)' }}>Ações Rápidas</h3>
      
      <div className="stats-grid">
        {filteredCards.map((card) => (
          <div 
            key={card.path} 
            className="card action-card" 
            onClick={() => navigate(card.path)}
            style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
          >
            <div style={{ 
              width: '48px', 
              height: '48px', 
              borderRadius: '12px', 
              background: card.color + '15', 
              color: card.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <card.icon size={24} />
            </div>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.125rem' }}>{card.title}</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{card.desc}</p>
          </div>
        ))}
      </div>

      <style jsx>{`
        .action-card:hover {
          transform: translateY(-5px);
          box-shadow: var(--shadow-lg);
          border-color: var(--primary);
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
