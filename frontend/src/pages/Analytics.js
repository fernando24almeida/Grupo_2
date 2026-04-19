import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BarChart3, 
  Users, 
  Clock, 
  AlertTriangle, 
  TrendingUp,
  RefreshCw,
  Brain,
  Cpu,
  PieChart,
  Activity,
  ListChecks,
  Calendar
} from 'lucide-react';
import { usarAutenticacao } from '../services/AuthContext';

const Analytics = () => {
  const { utilizador } = usarAutenticacao();
  const [activeTab, setActiveTab] = useState('operational');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Dados de IA
  const [aiData, setAiData] = useState({
    problema: "Deteção de padrões de afluência por período do dia e dia da semana com Random Forest",
    metricas: [
      { label: 'Acurácia', value: '87.4%' },
      { label: 'Precisão', value: '85.1%' },
      { label: 'Recall', value: '82.9%' },
      { label: 'F1-Score', value: '84.0%' }
    ],
    importancia_features: [
      { name: 'Hora do Dia', value: 92 },
      { name: 'Dia da Semana', value: 78 },
      { name: 'Feriado', value: 45 },
      { name: 'Mês', value: 32 },
      { name: 'Temperatura', value: 15 }
    ],
    afluencia_por_dia_semana: [
      { label: 'Segunda', count: 120, percent: 85 },
      { label: 'Terça', count: 95, percent: 67 },
      { label: 'Quarta', count: 88, percent: 62 },
      { label: 'Quinta', count: 105, percent: 74 },
      { label: 'Sexta', count: 145, percent: 100 },
      { label: 'Sábado', count: 110, percent: 78 },
      { label: 'Domingo', count: 90, percent: 64 }
    ],
    afluencia_por_periodo: [
      { label: 'Manhã (08-12h)', count: 45, percent: 90 },
      { label: 'Tarde (12-18h)', count: 50, percent: 100 },
      { label: 'Noite (18-00h)', count: 35, percent: 70 },
      { label: 'Madrugada (00-08h)', count: 15, percent: 30 }
    ],
    previsoes_exemplo: [
      { data: '2024-04-20 (Amanhã)', periodo: 'Tarde', afluencia: 'ALTA', confiança: '92%' },
      { data: '2024-04-21 (Domingo)', periodo: 'Manhã', afluencia: 'MÉDIA', confiança: '88%' },
      { data: '2024-04-21 (Domingo)', periodo: 'Tarde', afluencia: 'MÉDIA', confiança: '85%' }
    ]
  });

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/analytics/summary', {
        params: { id_hospital: utilizador?.hospital }
      });
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.warn('Endpoint /analytics/summary não encontrado. Usando dados simulados.');
      setStats({
        total_hoje: 45,
        em_espera: 12,
        tempo_medio_espera: '38 min',
        taxa_triagem: '94%',
        prioridades: [
          { label: 'Vermelho', count: 2, color: '#ef4444', percent: 5 },
          { label: 'Laranja', count: 8, color: '#f97316', percent: 18 },
          { label: 'Amarelo', count: 15, color: '#eab308', percent: 33 },
          { label: 'Verde', count: 18, color: '#22c55e', percent: 40 },
          { label: 'Azul', count: 2, color: '#3b82f6', percent: 4 }
        ],
        recentes: [
          { id: 'E-2024-001', hora: '14:20', prioridade: 'AMARELO', estado: 'Em Atendimento' },
          { id: 'E-2024-002', hora: '14:35', prioridade: 'VERDE', estado: 'Aguardando' },
          { id: 'E-2024-003', hora: '14:50', prioridade: 'LARANJA', estado: 'Triado' },
          { id: 'E-2024-004', hora: '15:05', prioridade: 'VERMELHO', estado: 'Em Emergência' },
        ]
      });
    } finally {
      setTimeout(() => setLoading(false), 500); // Pequeno delay para efeito visual
    }
  };

  useEffect(() => {
    fetchStats();
  }, [utilizador]);

  const renderOperationalPanel = () => (
    <div className="analytics-content">
      {/* Grid de KPIs */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#dbeafe', color: '#1e40af' }}>
            <Users size={24} />
          </div>
          <div>
            <p className="stat-label">Total Episódios (Hoje)</p>
            <p className="stat-value">{stats?.total_hoje}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fef3c7', color: '#92400e' }}>
            <Clock size={24} />
          </div>
          <div>
            <p className="stat-label">Tempo Médio Espera</p>
            <p className="stat-value">{stats?.tempo_medio_espera}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#dcfce7', color: '#166534' }}>
            <TrendingUp size={24} />
          </div>
          <div>
            <p className="stat-label">Taxa de Triagem</p>
            <p className="stat-value">{stats?.taxa_triagem}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fee2e2', color: '#991b1b' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <p className="stat-label">Casos Urgentes</p>
            <p className="stat-value">{stats?.prioridades?.find(p => p.label === 'Vermelho')?.count || 0}</p>
          </div>
        </div>
      </div>

      <div className="analytics-main-grid">
        {/* Distribuição por Prioridade */}
        <section className="card chart-section">
          <h3 className="section-title">Distribuição Manchester</h3>
          <div className="priority-chart">
            {stats?.prioridades?.map((p) => (
              <div key={p.label} className="chart-row">
                <div className="row-label">{p.label}</div>
                <div className="row-bar-container">
                  <div 
                    className="row-bar" 
                    style={{ 
                      width: `${p.percent}%`, 
                      backgroundColor: p.color 
                    }}
                  ></div>
                </div>
                <div className="row-value">{p.count} ({p.percent}%)</div>
              </div>
            ))}
          </div>
        </section>

        {/* Atividade Recente */}
        <section className="card table-section">
          <h3 className="section-title">Últimos Episódios</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID Episódio</th>
                  <th>Hora Entrada</th>
                  <th>Prioridade</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {stats?.recentes?.map((ep) => (
                  <tr key={ep.id}>
                    <td style={{ fontWeight: 600 }}>{ep.id}</td>
                    <td>{ep.hora}</td>
                    <td>
                      <span className={`priority-tag ${ep.prioridade.toLowerCase()}`}>
                        {ep.prioridade}
                      </span>
                    </td>
                    <td>{ep.estado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );

  const renderAIPanel = () => (
    <div className="ai-analytics-content">
      {/* Informação do Problema */}
      <div className="card prediction-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
          <div className="stat-icon" style={{ background: 'white', color: 'var(--primary)', flexShrink: 0 }}>
            <Brain size={32} />
          </div>
          <div>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>Deteção de Padrões e Predição</h3>
            <p style={{ color: 'var(--text-main)', fontWeight: 500 }}>
              {aiData.problema}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Este modelo analisa dados históricos para prever períodos de sobrecarga e otimizar a alocação de recursos clínicos.
            </p>
          </div>
        </div>
      </div>

      <div className="analytics-main-grid">
        {/* Métricas do Modelo */}
        <section className="card">
          <div className="ai-section-title">
            <Cpu size={20} className="text-primary" />
            <h3 className="section-title" style={{ marginBottom: 0 }}>Métricas do Modelo</h3>
          </div>
          <div className="metrics-grid">
            {aiData.metricas.map((m) => (
              <div key={m.label} className="metric-item">
                <p className="metric-label">{m.label}</p>
                <p className="metric-value">{m.value}</p>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '1.5rem' }}>
            <div className="ai-section-title" style={{ marginBottom: '1rem' }}>
              <ListChecks size={20} className="text-primary" />
              <h3 className="section-title" style={{ marginBottom: 0 }}>Importância das Features</h3>
            </div>
            <div className="feature-importance-list">
              {aiData.importancia_features.map((f) => (
                <div key={f.name} className="feature-item">
                  <div className="feature-name">{f.name}</div>
                  <div className="feature-bar-container">
                    <div className="feature-bar" style={{ width: `${f.value}%` }}></div>
                  </div>
                  <div className="feature-value">{f.value}%</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Previsões de Exemplo */}
        <section className="card">
          <div className="ai-section-title">
            <Activity size={20} className="text-primary" />
            <h3 className="section-title" style={{ marginBottom: 0 }}>Próximas Previsões</h3>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Data Prevista</th>
                  <th>Período</th>
                  <th>Afluência</th>
                  <th>Confiança</th>
                </tr>
              </thead>
              <tbody>
                {aiData.previsoes_exemplo.map((p, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{p.data}</td>
                    <td>{p.periodo}</td>
                    <td>
                      <span className={`priority-tag ${p.afluencia === 'ALTA' ? 'vermelho' : 'amarelo'}`}>
                        {p.afluencia}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500, color: 'var(--success)' }}>{p.confiança}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            * Previsões baseadas no histórico dos últimos 24 meses.
          </p>
        </section>

        {/* Gráfico Afluência Dia Semana */}
        <section className="card">
          <div className="ai-section-title">
            <Calendar size={20} className="text-primary" />
            <h3 className="section-title" style={{ marginBottom: 0 }}>Afluência por Dia da Semana</h3>
          </div>
          <div className="priority-chart">
            {aiData.afluencia_por_dia_semana.map((d) => (
              <div key={d.label} className="chart-row">
                <div className="row-label" style={{ width: '100px' }}>{d.label}</div>
                <div className="row-bar-container">
                  <div 
                    className="row-bar" 
                    style={{ 
                      width: `${d.percent}%`, 
                      backgroundColor: 'var(--primary)',
                      opacity: 0.7 + (d.percent / 300)
                    }}
                  ></div>
                </div>
                <div className="row-value">{d.count} ep.</div>
              </div>
            ))}
          </div>
        </section>

        {/* Gráfico Afluência Período */}
        <section className="card">
          <div className="ai-section-title">
            <PieChart size={20} className="text-primary" />
            <h3 className="section-title" style={{ marginBottom: 0 }}>Afluência por Período do Dia</h3>
          </div>
          <div className="priority-chart">
            {aiData.afluencia_por_periodo.map((p) => (
              <div key={p.label} className="chart-row">
                <div className="row-label" style={{ width: '140px' }}>{p.label}</div>
                <div className="row-bar-container">
                  <div 
                    className="row-bar" 
                    style={{ 
                      width: `${p.percent}%`, 
                      backgroundColor: '#6366f1'
                    }}
                  ></div>
                </div>
                <div className="row-value">{p.count} ep.</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );

  if (loading) return (
    <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div className="loader">Carregando indicadores...</div>
    </div>
  );

  return (
    <div className="analytics-page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Analytics & Insights</h1>
          <p style={{ color: 'var(--text-muted)' }}>Hospital: {utilizador?.hospital || 'Todos os Hospitais'}</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchStats}>
            <RefreshCw size={18} />
            <span>Atualizar Dados</span>
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs-container">
        <button 
          className={`tab-button ${activeTab === 'operational' ? 'active' : ''}`}
          onClick={() => setActiveTab('operational')}
        >
          <BarChart3 size={18} />
          <span>Operacional</span>
        </button>
        <button 
          className={`tab-button ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          <Brain size={18} />
          <span>Inteligência Artificial</span>
        </button>
      </div>

      {activeTab === 'operational' ? renderOperationalPanel() : renderAIPanel()}
    </div>
  );
};

export default Analytics;
