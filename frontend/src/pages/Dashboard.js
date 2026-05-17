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
  AlertCircle,
  User,
  Eye,
  X
} from 'lucide-react';

const Dashboard = () => {
  const { utilizador, hospital } = usarAutenticacao();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ waiting: 0, critical: 0, stats: [] });
  const [meusEpisodios, setMeusEpisodios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedJourney, setSelectedJourney] = useState(null);

  useEffect(() => {
    if (utilizador?.role === 'UTENTE') {
      fetchMeusEpisodios();
    } else {
      fetchStats();
      const interval = setInterval(fetchStats, 60000);
      return () => clearInterval(interval);
    }
  }, [hospital, utilizador]);

  const fetchStats = async () => {
    try {
      const params = hospital ? { id_hospital: hospital } : {};
      const res = await axios.get('/analytics/dashboard-summary', { params });
      setStats(res.data);
    } catch (e) { console.error('Erro ao carregar stats', e); }
  };

  const fetchMeusEpisodios = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/clinical/episodes');
      setMeusEpisodios(res.data);
    } catch (e) {
      console.error('Erro ao carregar episódios', e);
    } finally {
      setLoading(false);
    }
  };

  const verDetalhesEpisodio = async (codEpis) => {
    try {
      const res = await axios.get(`/clinical/episodes/${codEpis}/journey`);
      setSelectedJourney(res.data);
    } catch (e) {
      console.error('Erro ao carregar percurso', e);
      alert('Não foi possível carregar os detalhes do episódio.');
    }
  };

  if (utilizador?.role === 'UTENTE') {
    return (
      <div className="dashboard">
        <header className="page-header">
          <div>
            <h1 className="page-title">Olá, {utilizador?.nome_utilizador}</h1>
            <p style={{ color: 'var(--text-muted)' }}>Consulte aqui o seu histórico de episódios de urgência.</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/profile')}>
            <User size={18} /> O Meu Perfil
          </button>
        </header>

        <section className="admin-card">
          <div className="card-header">
            <Clipboard size={20} />
            <h3>Os Meus Episódios</h3>
          </div>
          <div className="card-body p-0">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Data de Entrada</th>
                  <th>Hospital</th>
                  <th>Estado</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {meusEpisodios.map(ep => (
                  <tr key={ep.cod_epis}>
                    <td><strong>{ep.cod_epis}</strong></td>
                    <td>{new Date(ep.data_h_entrada).toLocaleString()}</td>
                    <td>{ep.id_hospital}</td>
                    <td>
                      <span className={`status-pill ${ep.data_h_saida ? 'active' : 'pending'}`}>
                        {ep.data_h_saida ? 'Concluído' : 'Em Curso'}
                      </span>
                    </td>
                    <td>
                      <button className="btn-icon primary" onClick={() => verDetalhesEpisodio(ep.cod_epis)} title="Ver Detalhes">
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
                {meusEpisodios.length === 0 && !loading && (
                  <tr>
                    <td colSpan="5" className="text-center p-5 text-muted">
                      Não foram encontrados episódios clínicos no seu histórico.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* MODAL DE DETALHES (Utente) */}
        {selectedJourney && (
          <div className="admin-modal-overlay">
            <div className="admin-modal-content" style={{ maxWidth: '800px' }}>
              <div className="modal-header">
                <h3>Detalhes do Episódio {selectedJourney.episodio.cod_epis}</h3>
                <button className="close-btn" onClick={() => setSelectedJourney(null)}><X size={24}/></button>
              </div>
              <div className="modal-body">
                <div className="journey-summary">
                  <div className="summary-item">
                    <label>Data de Entrada:</label>
                    <span>{new Date(selectedJourney.episodio.data_h_entrada).toLocaleString()}</span>
                  </div>
                  <div className="summary-item">
                    <label>Hospital:</label>
                    <span>{selectedJourney.episodio.id_hospital}</span>
                  </div>
                  <div className="summary-item">
                    <label>Sintomas Iniciais:</label>
                    <p>{selectedJourney.episodio.sintomas || 'Não registados'}</p>
                  </div>
                </div>

                <hr className="divider" />

                <div className="timeline">
                  <h4 className="section-title"><Activity size={18} /> Percurso Clínico</h4>
                  
                  {/* Triagem */}
                  {selectedJourney.triagem && (
                    <div className="timeline-item">
                      <div className="timeline-marker"></div>
                      <div className="timeline-content">
                        <h5>Triagem ({selectedJourney.triagem.prioridade})</h5>
                        <p><strong>Data:</strong> {new Date(selectedJourney.triagem.data_h_triagem).toLocaleString()}</p>
                        <p><strong>Sintomas:</strong> {selectedJourney.triagem.sintomas}</p>
                        <p><strong>Sinais Vitais:</strong> Temp: {selectedJourney.triagem.temperatura}ºC | TA: {selectedJourney.triagem.tensao_arterial}</p>
                      </div>
                    </div>
                  )}

                  {/* Atos Clínicos */}
                  {selectedJourney.atos.map((ato, idx) => (
                    <div className="timeline-item" key={idx}>
                      <div className="timeline-marker blue"></div>
                      <div className="timeline-content">
                        <h5>Ato Clínico: {ato.tipo}</h5>
                        <p><strong>Início:</strong> {new Date(ato.data_h_inicio).toLocaleString()}</p>
                        {ato.data_h_fim && <p><strong>Fim:</strong> {new Date(ato.data_h_fim).toLocaleString()}</p>}
                        <p><strong>Decisão:</strong> {ato.decisao_clinica}</p>
                      </div>
                    </div>
                  ))}

                  {/* Prescrições */}
                  {selectedJourney.prescricoes.map((p, idx) => (
                    <div className="timeline-item" key={idx}>
                      <div className="timeline-marker green"></div>
                      <div className="timeline-content">
                        <h5>Prescrição Médica</h5>
                        <p><strong>Data:</strong> {new Date(p.data_h_presc).toLocaleString()}</p>
                        <p><strong>Medicação:</strong> {p.medicamento} ({p.dosagem})</p>
                      </div>
                    </div>
                  ))}

                  {/* Internamento */}
                  {selectedJourney.internamento && (
                    <div className="timeline-item">
                      <div className="timeline-marker red"></div>
                      <div className="timeline-content">
                        <h5>Internamento</h5>
                        <p><strong>Entrada:</strong> {new Date(selectedJourney.internamento.data_h_entrada).toLocaleString()}</p>
                        <p><strong>Cama:</strong> {selectedJourney.internamento.num_cama}</p>
                      </div>
                    </div>
                  )}

                  {selectedJourney.episodio.data_h_saida && (
                    <div className="timeline-item">
                      <div className="timeline-marker black"></div>
                      <div className="timeline-content">
                        <h5>Alta / Conclusão</h5>
                        <p><strong>Data:</strong> {new Date(selectedJourney.episodio.data_h_saida).toLocaleString()}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn-secondary" onClick={() => setSelectedJourney(null)}>Fechar</button>
              </div>
            </div>
          </div>
        )}

        <style jsx>{`
          .timeline { margin-top: 1.5rem; }
          .timeline-item { position: relative; padding-left: 30px; margin-bottom: 1.5rem; }
          .timeline-marker { position: absolute; left: 0; top: 5px; width: 12px; height: 12px; border-radius: 50%; background: var(--primary); }
          .timeline-marker.blue { background: #3b82f6; }
          .timeline-marker.green { background: #10b981; }
          .timeline-marker.red { background: #ef4444; }
          .timeline-marker.black { background: #000; }
          .timeline-item::before { content: ''; position: absolute; left: 5px; top: 20px; bottom: -20px; width: 2px; background: #e2e8f0; }
          .timeline-item:last-child::before { display: none; }
          .timeline-content h5 { margin-bottom: 0.25rem; color: var(--text-main); }
          .timeline-content p { font-size: 0.85rem; color: var(--text-muted); margin: 0; }
          .journey-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
          .summary-item label { display: block; font-size: 0.75rem; font-weight: bold; color: var(--text-muted); text-transform: uppercase; }
          .divider { margin: 1.5rem 0; border: none; border-top: 1px solid #e2e8f0; }
        `}</style>
      </div>
    );
  }

  // DASHBOARD PARA STAFF (Original)
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
      title: 'Analítica',
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
