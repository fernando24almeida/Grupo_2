import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { 
  Clipboard, User, HeartPulse, Thermometer, 
  Clock, CheckCircle, AlertCircle, ArrowRight,
  FileText, Activity
} from 'lucide-react';

const ClinicalActs = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('treatment');
  const [queue, setQueue] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(utilizador?.hospital || '');
  const [selectedEpisode, setSelectedEpisode] = useState(null);
  const [history, setHistory] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [atoData, setAtoData] = useState({ tipo: 'CONSULTA', data_h_inicio: new Date().toISOString().slice(0, 16) });
  const [prescData, setPrescData] = useState({ medicamento: '', dosagem: '' });
  
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

  const fetchQueue = async () => {
    if (!selectedHospital) return;
    try {
      const res = await axios.get('/clinical/episodes/awaiting-doctor', { 
        params: { id_hospital: selectedHospital } 
      });
      setQueue(res.data);
    } catch (error) { console.error('Erro ao carregar fila', error); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchQueue(); }, [selectedHospital]);

  const handleSelectPatient = async (cod) => {
    try {
      const res = await axios.get(`/clinical/episodes/${cod}`);
      setSelectedEpisode(res.data);
      setAtoData({ tipo: 'CONSULTA', data_h_inicio: new Date().toISOString().slice(0, 16) });
      
      // Carregar histórico e prescrições do paciente selecionado
      const [histRes, prescRes] = await Promise.all([
        axios.get(`/clinical/utentes/${res.data.id_utente}/history`),
        axios.get(`/clinical/episodes/${cod}/prescriptions`)
      ]);
      setHistory(histRes.data);
      setPrescriptions(prescRes.data);
      setActiveTab('treatment');
    } catch (error) { console.error('Erro ao buscar detalhes', error); }
  };

  const handleSubmitAto = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/atos', {
        ...atoData,
        cod_epis: selectedEpisode.cod_epis,
        id_hosp: selectedEpisode.id_hospital,
        num_func: utilizador?.num_func || 1002
      });
      setMessage({ type: 'success', text: 'Ato clínico registado!' });
    } catch (error) { setMessage({ type: 'error', text: 'Erro ao registar ato.' }); }
  };

  const handleAddPrescription = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/prescricoes', {
        ...prescData,
        cod_epis: selectedEpisode.cod_epis,
        num_func_medico: utilizador?.num_func || 1002
      });
      setPrescData({ medicamento: '', dosagem: '' });
      const res = await axios.get(`/clinical/episodes/${selectedEpisode.cod_epis}/prescriptions`);
      setPrescriptions(res.data);
      setMessage({ type: 'success', text: 'Prescrição adicionada!' });
    } catch (error) { setMessage({ type: 'error', text: 'Erro ao prescrever.' }); }
  };

  const handleDischarge = async () => {
    if (!window.confirm('Dar alta ao paciente?')) return;
    try {
      await axios.post(`/clinical/episodes/${selectedEpisode.cod_epis}/discharge`);
      setSelectedEpisode(null);
      fetchQueue();
      setMessage({ type: 'success', text: 'Paciente teve alta.' });
    } catch (error) { setMessage({ type: 'error', text: 'Erro ao dar alta.' }); }
  };

  if (loading) return <div className="loading-container">Carregando prontuário...</div>;

  return (
    <div className="clinical-acts-page">
      <header className="page-header">
        <div className="header-title">
          <Clipboard size={28} className="icon-blue" />
          <h1>Atendimento Clínico</h1>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/dashboard')}>Sair</button>
      </header>

      <div className="hospital-selection-bar">
        <div className="selection-inner">
          <span className="selection-label">Unidade Hospitalar:</span>
          <select 
            className="form-select" 
            value={selectedHospital} 
            onChange={(e) => setSelectedHospital(e.target.value)}
          >
            <option value="">Selecione...</option>
            {hospitals.map(h => (
              <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="clinical-grid">
        {/* FILA MÉDICA */}
        <div className="medical-sidebar">
          <div className="card shadow-sm">
            <div className="card-header bg-light d-flex justify-content-between">
              <h3 className="h6 mb-0">Pacientes Triados</h3>
              <span className="badge bg-primary">{queue.length}</span>
            </div>
            <div className="queue-list">
              {queue.length === 0 ? <p className="p-3 text-center text-muted">Fila vazia</p> : 
                queue.map((ep) => (
                  <div key={ep.cod_epis} className={`queue-item priority-border-${ep.prioridade.toLowerCase()} ${selectedEpisode?.cod_epis === ep.cod_epis ? 'active' : ''}`} onClick={() => handleSelectPatient(ep.cod_epis)}>
                    <div className="patient-meta">
                      <strong>{ep.utente_nome}</strong>
                      <small className={`text-${ep.prioridade.toLowerCase()}`}>{ep.prioridade}</small>
                    </div>
                    <ArrowRight size={16} />
                  </div>
                ))
              }
            </div>
          </div>
        </div>

        {/* ÁREA DE TRABALHO */}
        <div className="medical-main">
          {message && <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} mb-3`}>{message.text}</div>}

          {selectedEpisode ? (
            <div className="workspace">
              {/* CABEÇALHO DO PACIENTE */}
              <div className="patient-banner card mb-4">
                <div className="d-flex justify-content-between align-items-center p-3">
                  <div className="d-flex align-items-center gap-3">
                    <div className="avatar-med">{selectedEpisode.utente?.nome?.charAt(0)}</div>
                    <div>
                      <h2 className="h4 mb-0">{selectedEpisode.utente?.nome}</h2>
                      <small className="text-muted">NIF/Utente: {selectedEpisode.id_utente} | Episódio: {selectedEpisode.cod_epis}</small>
                    </div>
                  </div>
                  <div className={`vitals-summary priority-bg-${selectedEpisode.triagem?.prioridade.toLowerCase()}`}>
                    <span>{selectedEpisode.triagem?.tensao_arterial} mmHg</span>
                    <span>{selectedEpisode.triagem?.temperatura} ºC</span>
                  </div>
                </div>
                
                {/* TABS NAVEGAÇÃO */}
                <div className="tab-nav">
                  <button className={activeTab === 'treatment' ? 'active' : ''} onClick={() => setActiveTab('treatment')}>Atendimento</button>
                  <button className={activeTab === 'prescriptions' ? 'active' : ''} onClick={() => setActiveTab('prescriptions')}>Prescrições ({prescriptions.length})</button>
                  <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>Histórico Clínico</button>
                </div>
              </div>

              {/* CONTEÚDO DAS TABS */}
              <div className="tab-content">
                {activeTab === 'treatment' && (
                  <section className="card shadow-sm p-4">
                    <div className="sintomas-box mb-4">
                      <h6>Sintomas na Admissão:</h6>
                      <p>{selectedEpisode.triagem?.sintomas || 'Não descritos.'}</p>
                    </div>
                    <form onSubmit={handleSubmitAto}>
                      <div className="row">
                        <div className="col-md-6 mb-3">
                          <label className="form-label">Tipo de Ato</label>
                          <select className="form-select" value={atoData.tipo} onChange={e => setAtoData({...atoData, tipo: e.target.value})}>
                            <option value="CONSULTA">Consulta Médica</option>
                            <option value="EXAME">Exame de Diagnóstico</option>
                            <option value="INTERVENCAO">Intervenção</option>
                          </select>
                        </div>
                        <div className="col-md-6 mb-3">
                          <label className="form-label">Data/Hora</label>
                          <input type="datetime-local" className="form-control" value={atoData.data_h_inicio} onChange={e => setAtoData({...atoData, data_h_inicio: e.target.value})} required />
                        </div>
                      </div>
                      <div className="d-flex gap-2 mt-3">
                        <button type="submit" className="btn btn-primary px-4">Gravar Ato Clínico</button>
                        <button type="button" className="btn btn-success px-4" onClick={handleDischarge}>Finalizar Urgência (Alta)</button>
                      </div>
                    </form>
                  </section>
                )}

                {activeTab === 'prescriptions' && (
                  <section className="card shadow-sm p-4">
                    <form onSubmit={handleAddPrescription} className="mb-4 d-flex gap-3 align-items-end">
                      <div className="flex-grow-1">
                        <label className="form-label">Medicamento</label>
                        <input type="text" className="form-control" value={prescData.medicamento} onChange={e => setPrescData({...prescData, medicamento: e.target.value})} required placeholder="Ex: Paracetamol" />
                      </div>
                      <div style={{ width: '200px' }}>
                        <label className="form-label">Dosagem</label>
                        <input type="text" className="form-control" value={prescData.dosagem} onChange={e => setPrescData({...prescData, dosagem: e.target.value})} required placeholder="Ex: 1g 8/8h" />
                      </div>
                      <button type="submit" className="btn btn-primary">Adicionar</button>
                    </form>
                    <table className="table">
                      <thead><tr><th>Medicamento</th><th>Dosagem</th><th>Data</th></tr></thead>
                      <tbody>
                        {prescriptions.map((p, i) => (
                          <tr key={i}><td>{p.medicamento}</td><td>{p.dosagem}</td><td>{new Date(p.data_h_presc).toLocaleDateString()}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  </section>
                )}

                {activeTab === 'history' && (
                  <div className="history-timeline">
                    {history.map((item, i) => (
                      <div key={i} className="timeline-item card mb-3">
                        <div className="card-header bg-light d-flex justify-content-between">
                          <strong>EpisódioUrgent: {item.episodio.cod_epis}</strong>
                          <span>{new Date(item.episodio.data_h_entrada).toLocaleDateString()}</span>
                        </div>
                        <div className="card-body py-2">
                          <p className="mb-1"><strong>Queixa:</strong> {item.triagem?.sintomas}</p>
                          <p className="mb-1"><strong>Prioridade:</strong> {item.triagem?.prioridade}</p>
                          <small className="text-muted">Atos: {item.atos.map(a => a.tipo).join(', ')}</small>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="select-prompt-container">
              <Activity size={64} className="text-muted mb-3 opacity-25" />
              <h3>Aguardando Paciente</h3>
              <p>Selecione um paciente da fila para abrir o prontuário.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .clinical-acts-page { padding: 1.5rem; background: #f8f9fa; min-height: 100vh; }
        .clinical-grid { display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; }
        .queue-item { padding: 1rem; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid transparent; }
        .queue-item.active { background: white; border-left-color: var(--primary); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .priority-border-vermelho { border-left-color: #dc3545; }
        .priority-border-laranja { border-left-color: #fd7e14; }
        .priority-border-amarelo { border-left-color: #ffc107; }
        
        .patient-banner { border-radius: 12px; overflow: hidden; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .avatar-med { width: 45px; height: 45px; background: #e2e8f0; color: #475569; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem; }
        .vitals-summary { display: flex; gap: 1rem; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
        .priority-bg-vermelho { background: #fee2e2; color: #991b1b; }
        .priority-bg-laranja { background: #ffedd5; color: #9a3412; }
        .priority-bg-amarelo { background: #fef9c3; color: #854d0e; }
        .priority-bg-verde { background: #dcfce7; color: #166534; }
        .priority-bg-azul { background: #dbeafe; color: #1e40af; }

        .tab-nav { display: flex; background: #f1f5f9; padding: 4px; gap: 4px; }
        .tab-nav button { flex: 1; padding: 10px; border: none; background: none; border-radius: 6px; cursor: pointer; font-weight: 600; color: #64748b; transition: all 0.2s; }
        .tab-nav button.active { background: white; color: var(--primary); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        
        .sintomas-box { background: #fdf6e3; padding: 1rem; border-radius: 8px; border: 1px solid #eee8d5; }
        .history-timeline { max-height: 400px; overflow-y: auto; }
        .select-prompt-container { height: 500px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: white; border-radius: 1rem; border: 2px dashed #ddd; }
      `}</style>
    </div>
  );
};

export default ClinicalActs;
