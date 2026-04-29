import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { ClipboardList, User, Clock, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

const Triage = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [episodes, setEpisodes] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(utilizador?.hospital || '');
  const [selectedEpisode, setSelectedEpisode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [formData, setFormData] = useState({
    cod_epis: '',
    prioridade: 'AZUL',
    tensao_arterial: '120/80',
    temperatura: 36.5,
    sintomas: '',
    observacoes: '',
    num_func_enfermeiro: utilizador?.num_func || 1001
  });

  // Carregar Hospitais e Fila
  useEffect(() => {
    const fetchData = async () => {
      try {
        const resHosp = await axios.get('/clinical/hospitals');
        setHospitals(resHosp.data);
        if (resHosp.data.length > 0 && !selectedHospital) {
          setSelectedHospital(resHosp.data[0].nome_hosp);
        }
      } catch (e) { console.error(e); }
    };
    fetchData();
  }, []);

  const fetchAwaitingEpisodes = async () => {
    if (!selectedHospital) return;
    try {
      const res = await axios.get('/clinical/episodes/awaiting-triage', { 
        params: { id_hospital: selectedHospital } 
      });
      setEpisodes(res.data);
    } catch (error) {
      console.error('Erro ao carregar episódios', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAwaitingEpisodes();
  }, [selectedHospital]);

  // Simulação Manchester Automática
  useEffect(() => {
    if (formData.temperatura || formData.tensao_arterial) {
      const sistolica = parseInt(formData.tensao_arterial.split('/')[0]) || 120;
      const temp = parseFloat(formData.temperatura);
      
      let suggested = 'AZUL';
      if (temp >= 40 || sistolica < 70) suggested = 'VERMELHO';
      else if (temp >= 39 || sistolica > 190 || sistolica < 90) suggested = 'LARANJA';
      else if (temp >= 38 || sistolica > 160) suggested = 'AMARELO';
      else if (temp >= 37.5) suggested = 'VERDE';
      
      setFormData(prev => ({ ...prev, prioridade: suggested }));
    }
  }, [formData.temperatura, formData.tensao_arterial]);

  const handleCallPatient = async (episode) => {
    try {
      // Obter detalhes completos do episódio (incluindo nome do utente)
      const res = await axios.get(`/clinical/episodes/${episode.cod_epis}`);
      setSelectedEpisode(res.data);
      setFormData(prev => ({ 
        ...prev, 
        cod_epis: episode.cod_epis,
        sintomas: res.data.sintomas || '',
        observacoes: res.data.observacoes || ''
      }));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      console.error('Erro ao buscar detalhes', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/triagens/manchester', {
        ...formData,
        num_func_enfermeiro: utilizador?.num_func || 1001
      });
      setMessage({ type: 'success', text: `Triagem do episódio ${formData.cod_epis} concluída com prioridade ${formData.prioridade}!` });
      setSelectedEpisode(null);
      setFormData({
        cod_epis: '',
        prioridade: 'AZUL',
        tensao_arterial: '120/80',
        temperatura: 36.5,
        sintomas: '',
        observacoes: '',
        num_func_enfermeiro: utilizador?.num_func || 1001
      });
      fetchAwaitingEpisodes();
    } catch (error) {
      console.error('Erro ao registar triagem', error);
      setMessage({ type: 'error', text: 'Erro ao registar triagem.' });
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

      <div className="hospital-selection-bar">
        <div className="selection-inner">
          <span className="selection-label">Hospital a Monitorizar:</span>
          <select 
            className="form-select" 
            value={selectedHospital} 
            onChange={(e) => setSelectedHospital(e.target.value)}
          >
            <option value="">Selecione um Hospital...</option>
            {hospitals.map(h => (
              <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="triage-container">
        {/* FILA DE ESPERA */}
        <div className="triage-sidebar">
          <div className="card shadow-sm">
            <div className="card-header bg-light d-flex justify-content-between align-items-center">
              <h3 className="h5 mb-0"><Clock size={18} /> Fila de Espera</h3>
              <span className="badge bg-primary rounded-pill">{episodes.length}</span>
            </div>
            <div className="queue-list">
              {episodes.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle size={40} className="text-success mb-2" />
                  <p>Fila vazia</p>
                </div>
              ) : (
                episodes.map((ep, index) => (
                  <div 
                    key={ep.cod_epis} 
                    className={`queue-item ${selectedEpisode?.cod_epis === ep.cod_epis ? 'active' : ''}`}
                    onClick={() => handleCallPatient(ep)}
                  >
                    <div className="queue-info">
                      <span className="order-number">{index + 1}</span>
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

        {/* FORMULÁRIO */}
        <div className="triage-main">
          {message && (
            <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`}>
              {message.text}
              <button type="button" className="btn-close" onClick={() => setMessage(null)}></button>
            </div>
          )}

          {selectedEpisode ? (
            <div className="card shadow-lg">
              <div className={`card-header priority-header ${formData.prioridade.toLowerCase()}`}>
                <h3 className="h5 mb-0">Avaliação: {selectedEpisode.utente?.nome || selectedEpisode.cod_epis}</h3>
                <span className="badge bg-white text-dark">Nº Utente: {selectedEpisode.id_utente}</span>
              </div>
              <div className="card-body">
                <form onSubmit={handleSubmit} className="triage-form">
                  <div className="row mb-4">
                    <div className="col-md-6">
                      <label className="form-label">Tensão Arterial (Sistólica/Diastólica)</label>
                      <div className="input-group">
                        <input 
                          type="text" 
                          className="form-control form-control-lg" 
                          value={formData.tensao_arterial} 
                          onChange={(e) => setFormData({...formData, tensao_arterial: e.target.value})}
                          placeholder="Ex: 120/80"
                          required
                        />
                        <span className="input-group-text">mmHg</span>
                      </div>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Temperatura Corporal</label>
                      <div className="input-group">
                        <input 
                          type="number" 
                          step="0.1"
                          className="form-control form-control-lg" 
                          value={formData.temperatura} 
                          onChange={(e) => setFormData({...formData, temperatura: e.target.value})}
                          required
                        />
                        <span className="input-group-text">ºC</span>
                      </div>
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="form-label">Prioridade Manchester (Sugerida pelo Sistema)</label>
                    <div className="priority-selector">
                      {[
                        { val: 'VERMELHO', label: 'Emergência', color: '#dc3545' },
                        { val: 'LARANJA', label: 'Muito Urgente', color: '#fd7e14' },
                        { val: 'AMARELO', label: 'Urgente', color: '#ffc107' },
                        { val: 'VERDE', label: 'Pouco Urgente', color: '#198754' },
                        { val: 'AZUL', label: 'Não Urgente', color: '#0d6efd' }
                      ].map(p => (
                        <div 
                          key={p.val} 
                          className={`priority-option ${formData.prioridade === p.val ? 'selected active-' + p.val.toLowerCase() : ''}`}
                          onClick={() => setFormData({...formData, prioridade: p.val})}
                        >
                          <div className="priority-color-box" style={{ background: p.color }}></div>
                          <span>{p.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="form-label">Sintomas Transmitidos pelo Paciente</label>
                    <textarea 
                      className="form-control"
                      rows="3"
                      value={formData.sintomas} 
                      onChange={(e) => setFormData({...formData, sintomas: e.target.value})}
                      required
                      placeholder="Descreva as queixas do paciente..."
                    />
                  </div>

                  <div className="mb-4">
                    <label className="form-label">Observações de Enfermagem</label>
                    <textarea 
                      className="form-control"
                      rows="3"
                      value={formData.observacoes} 
                      onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                      placeholder="Observações adicionais, estado de consciência, etc."
                    />
                  </div>

                  <div className="d-flex gap-3 justify-content-end">
                    <button type="button" className="btn btn-light btn-lg" onClick={() => setSelectedEpisode(null)}>Cancelar</button>
                    <button type="submit" className="btn btn-primary btn-lg px-5">Registar Triagem</button>
                  </div>
                </form>
              </div>
            </div>
          ) : (
            <div className="select-prompt-container">
              <ClipboardList size={64} className="text-muted mb-4 opacity-25" />
              <h3>Pronto para Triagem</h3>
              <p className="text-muted">Selecione um paciente da fila de espera à esquerda para iniciar a avaliação Manchester.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .triage-page { padding: 2rem; background: #f0f2f5; min-height: 100vh; }
        .triage-container { display: grid; grid-template-columns: 320px 1fr; gap: 2rem; }
        
        .queue-list { max-height: calc(100vh - 250px); overflow-y: auto; }
        .queue-item { 
          display: flex; justify-content: space-between; align-items: center;
          padding: 1rem; border-bottom: 1px solid #f0f0f0; cursor: pointer;
          transition: all 0.2s;
        }
        .queue-item:hover { background: #f8f9fa; }
        .queue-item.active { background: #e7f1ff; border-left: 4px solid #0d6efd; }
        
        .priority-header { color: white; display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; }
        .priority-header.vermelho { background: #dc3545; }
        .priority-header.laranja { background: #fd7e14; }
        .priority-header.amarelo { background: #ffc107; color: #000; }
        .priority-header.verde { background: #198754; }
        .priority-header.azul { background: #0d6efd; }

        .priority-selector { display: flex; gap: 10px; flex-wrap: wrap; }
        .priority-option { 
          flex: 1; min-width: 140px; padding: 12px; border: 1px solid #ddd; 
          border-radius: 10px; display: flex; align-items: center; gap: 10px;
          cursor: pointer; transition: all 0.2s;
        }
        .priority-color-box { width: 20px; height: 20px; border-radius: 4px; }
        .priority-option.selected { border-width: 2px; font-weight: bold; }
        .priority-option.active-vermelho { border-color: #dc3545; background: #fff5f5; }
        .priority-option.active-laranja { border-color: #fd7e14; background: #fffaf0; }
        .priority-option.active-amarelo { border-color: #ffc107; background: #fffdf0; }
        .priority-option.active-verde { border-color: #198754; background: #f0fff4; }
        .priority-option.active-azul { border-color: #0d6efd; background: #f0f7ff; }

        .select-prompt-container { 
          height: 500px; display: flex; flex-direction: column; 
          align-items: center; justify-content: center; 
          background: white; border-radius: 1rem; border: 2px dashed #ddd;
        }
      `}</style>
    </div>
  );
};

export default Triage;
