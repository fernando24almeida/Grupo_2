import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
  const { utilizador, hospital } = usarAutenticacao();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ waiting: 0, critical: 0, stats: [] });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const params = hospital ? { id_hospital: hospital } : {};
        const res = await axios.get('/analytics/dashboard-summary', { params });
        setStats(res.data);
      } catch (e) { console.error('Erro ao carregar stats', e); }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Atualizar a cada minuto
    return () => clearInterval(interval);
  }, [hospital]);

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

  const getPriorityColor = (prioridade) => {
    const colors = {
      'VERMELHO': '#ef4444',
      'LARANJA': '#f97316',
      'AMARELO': '#eab308',
      'VERDE': '#22c55e',
      'AZUL': '#3b82f6'
    };
    return colors[prioridade] || '#94a3b8';
  };

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
            <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats.waiting}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fee2e2', color: '#991b1b' }}>
            <AlertCircle size={24} />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Casos Críticos</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats.critical}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f1f5f9', color: '#475569' }}>
            <Clock size={24} />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Última Atualização</p>
            <p style={{ fontSize: '1rem', fontWeight: 600 }}>{stats.updatedAt ? new Date(stats.updatedAt).toLocaleTimeString() : '...'}</p>
          </div>
        </div>
      </div>

      {/* Priority Breakdown */}
      <div className="priority-breakdown admin-card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Activity size={20} color="var(--primary)" />
          Estado da Urgência (Sistema Manchester)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
          {stats.stats?.map((item) => (
            <div key={item.prioridade} style={{ 
              background: '#fff', 
              border: `1px solid ${getPriorityColor(item.prioridade)}40`, 
              borderRadius: '12px',
              padding: '1rem',
              borderLeft: `4px solid ${getPriorityColor(item.prioridade)}`
            }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 700, color: getPriorityColor(item.prioridade), marginBottom: '0.25rem' }}>{item.prioridade}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800 }}>{item.quantidade}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.tempo_medio} min</span>
              </div>
            </div>
          ))}
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
        .admin-card { 
          background: white; 
          border-radius: 12px; 
          border: 1px solid #e2e8f0; 
          box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .stat-card {
          background: white;
          padding: 1.5rem;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 1rem;
          border: 1px solid #e2e8f0;
        }
        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
