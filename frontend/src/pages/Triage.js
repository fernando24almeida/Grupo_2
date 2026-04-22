import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { ClipboardList, User, Clock, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

const Triage = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [episodes, setEpisodes] = useState([]);
  const [selectedEpisode, setSelectedEpisode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  
  const [formData, setFormData] = useState({
    cod_epis: '',
    prioridade: 'VERDE',
    sintomas: '',
    observacoes: '',
    num_func_enfermeiro: utilizador?.num_func || 1001 
  });

  const fetchAwaitingEpisodes = async () => {
    try {
      const params = {};
      if (utilizador?.hospital) {
        params.id_hospital = utilizador.hospital;
      }
      const res = await axios.get('/clinical/episodes/awaiting-triage', { params });
      setEpisodes(res.data);
    } catch (error) {
      console.error('Erro ao carregar episódios', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAwaitingEpisodes();
  }, [utilizador]);

  const handleCallPatient = (episode) => {
    setSelectedEpisode(episode);
    setFormData(prev => ({ 
      ...prev, 
      cod_epis: episode.cod_epis,
      sintomas: episode.sintomas || '',
      observacoes: episode.observacoes || ''
    }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/triagens', {
        ...formData,
        num_func_enfermeiro: utilizador?.num_func || 1001
      });
      setMessage({ type: 'success', text: `Triagem do episódio ${formData.cod_epis} registada com sucesso!` });
      setSelectedEpisode(null);
      setFormData({
        cod_epis: '',
        prioridade: 'VERDE',
        sintomas: '',
        observacoes: '',
        num_func_enfermeiro: utilizador?.num_func || 1001
      });
      fetchAwaitingEpisodes();
    } catch (error) {
      console.error('Erro ao registar triagem', error);
      setMessage({ type: 'error', text: 'Erro ao registar triagem. Verifique se os dados estão corretos.' });
    }
  };

  if (loading) return <div className="loading-container">Carregando fila de espera...</div>;

  return (
    <div className="triage-page">
      <header className="page-header">
        <div className="header-title">
          <ClipboardList size={28} className="icon-primary" />
          <h1>Triagem de Manchester</h1>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/dashboard')}>Sair</button>
      </header>

      <div className="triage-container">
        {/* COLUNA DA ESQUERDA: FILA DE ESPERA */}
        <div className="triage-sidebar">
          <div className="card shadow-sm">
            <div className="card-header bg-light">
              <h3 className="h5 mb-0"><Clock size={18} /> Fila de Espera</h3>
              <span className="badge bg-primary">{episodes.length}</span>
            </div>
            <div className="queue-list">
              {episodes.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle size={40} className="text-success" />
                  <p>Não há pacientes a aguardar triagem.</p>
                </div>
              ) : (
                episodes.map((ep, index) => (
                  <div 
                    key={ep.cod_epis} 
                    className={`queue-item ${selectedEpisode?.cod_epis === ep.cod_epis ? 'active' : ''}`}
                    onClick={() => handleCallPatient(ep)}
                  >
                    <div className="queue-info">
                      <span className="order-number">#{index + 1}</span>
                      <div className="patient-meta">
                        <strong>{ep.cod_epis}</strong>
                        <small>{new Date(ep.data_h_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                      </div>
                    </div>
                    <ArrowRight size={18} className="arrow-icon" />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* COLUNA DA DIREITA: FORMULÁRIO DE TRIAGEM */}
        <div className="triage-main">
          {message && (
            <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} mb-4`}>
              {message.text}
            </div>
          )}

          {selectedEpisode ? (
            <div className="card shadow">
              <div className="card-header bg-primary text-white">
                <h3 className="h5 mb-0">Avaliação do Episódio: {selectedEpisode.cod_epis}</h3>
              </div>
              <div className="card-body">
                <div className="patient-context mb-4">
                  <div className="context-item">
                    <User size={16} /> <span>Utente: <strong>{selectedEpisode.id_utente}</strong></span>
                  </div>
                  <div className="context-item">
                    <Clock size={16} /> <span>Entrada: {new Date(selectedEpisode.data_h_entrada).toLocaleString()}</span>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="triage-form">
                  <div className="form-section">
                    <label className="section-label">Sistema Manchester (Prioridade)</label>
                    <div className="priority-grid">
                      {[
                        { val: 'VERMELHO', label: 'Emergência', color: '#dc3545' },
                        { val: 'LARANJA', label: 'Muito Urgente', color: '#fd7e14' },
                        { val: 'AMARELO', label: 'Urgente', color: '#ffc107' },
                        { val: 'VERDE', label: 'Pouco Urgente', color: '#198754' },
                        { val: 'AZUL', label: 'Não Urgente', color: '#0d6efd' }
                      ].map(p => (
                        <label key={p.val} className={`priority-card ${formData.prioridade === p.val ? 'selected' : ''}`} style={{ '--p-color': p.color }}>
                          <input 
                            type="radio" 
                            name="prioridade" 
                            value={p.val} 
                            checked={formData.prioridade === p.val}
                            onChange={(e) => setFormData({...formData, prioridade: e.target.value})}
                          />
                          <span className="priority-dot"></span>
                          <span className="priority-label">{p.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="form-group mb-4">
                    <label>Sintomas / Motivo da Urgência (Recolhidos na Triagem):</label>
                    <textarea 
                      className="form-control"
                      rows="4"
                      value={formData.sintomas} 
                      onChange={(e) => setFormData({...formData, sintomas: e.target.value})}
                      required
                      placeholder="Ex: Dor torácica intensa, dificuldade respiratória..."
                    />
                  </div>

                  <div className="form-group mb-4">
                    <label>Observações Clínicas e Sinais Vitais:</label>
                    <textarea 
                      className="form-control"
                      rows="4"
                      value={formData.observacoes} 
                      onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                      placeholder="Ex: TA: 140/90, FC: 85, Temp: 37.2ºC. Paciente consciente..."
                    />
                  </div>

                  <div className="form-actions mt-4">
                    <button type="button" className="btn btn-outline-secondary" onClick={() => setSelectedEpisode(null)}>Cancelar</button>
                    <button type="submit" className="btn btn-primary btn-lg">Finalizar Triagem</button>
                  </div>
                </form>
              </div>
            </div>
          ) : (
            <div className="select-prompt card">
              <AlertCircle size={48} className="text-muted mb-3" />
              <h3>Selecione um paciente da fila</h3>
              <p>Clique num paciente à esquerda para iniciar a triagem de Manchester.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .triage-page { padding: 2rem; max-width: 1200px; margin: 0 auto; }
        .triage-container { display: grid; grid-template-columns: 350px 1fr; gap: 2rem; margin-top: 1.5rem; }
        
        .queue-list { max-height: 70vh; overflow-y: auto; }
        .queue-item { 
          display: flex; justify-content: space-between; align-items: center;
          padding: 1rem; border-bottom: 1px solid #eee; cursor: pointer;
          transition: all 0.2s;
        }
        .queue-item:hover { background: #f8f9fa; }
        .queue-item.active { background: #e7f1ff; border-left: 4px solid #0d6efd; }
        
        .queue-info { display: flex; align-items: center; gap: 1rem; }
        .order-number { background: #eee; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.8rem; font-weight: bold; }
        .patient-meta { display: flex; flex-direction: column; }
        
        .priority-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
        .priority-card { 
          border: 2px solid #eee; border-radius: 8px; padding: 10px; 
          display: flex; align-items: center; gap: 10px; cursor: pointer;
          transition: all 0.2s;
        }
        .priority-card.selected { border-color: var(--p-color); background: rgba(var(--p-color-rgb), 0.1); }
        .priority-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--p-color); }
        .priority-card input { display: none; }
        
        .patient-context { display: flex; gap: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; }
        .context-item { display: flex; align-items: center; gap: 8px; color: #666; }
        
        .select-prompt { height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; }
        .empty-state { padding: 3rem; text-align: center; color: #666; }
      `}</style>
    </div>
  );
};

export default Triage;
