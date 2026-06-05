import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { 
  Clipboard, HeartPulse, Thermometer, 
  Clock, CheckCircle, ArrowRight,
  Activity, Hotel, Search, X
} from 'lucide-react';

const ClinicalActs = () => {
  // --- ESTADO DO COMPONENTE (Memória local para guardar dados e controlar o que aparece no ecrã) ---
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [activeMode, setActiveMode] = useState('urgencia'); // Alterna entre modo Urgência e Internamento
  const [activeTab, setActiveTab] = useState('treatment'); // Controla qual aba está ativa (Tratamento, Histórico, etc)
  const [queue, setQueue] = useState([]); // Guarda a lista de pacientes à espera na urgência
  const [internments, setInternments] = useState([]); // Guarda a lista de pacientes atualmente internados
  const [selectedEpisode, setSelectedEpisode] = useState(null); // Guarda o episódio do paciente que estamos a atender
  const [searchQuery, setSearchQuery] = useState(''); // Guarda o texto escrito na barra de pesquisa
  const [isHospitalizedPatient, setIsHospitalizedPatient] = useState(false); // Indica se o paciente atual é de internamento
  const [history, setHistory] = useState([]); // Guarda o histórico clínico do utente
  const [prescriptions, setPrescriptions] = useState([]); // Guarda as receitas/prescrições do episódio atual
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  // --- EFEITOS AUTOMÁTICOS (Código que corre sozinho quando algo muda) ---
  // Fecha as mensagens de aviso automaticamente após 30 segundos
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // Limpa mensagens do ecrã ao mudar de aba, de paciente ou de modo de atendimento
  useEffect(() => {
    setMessage(null);
  }, [activeTab, selectedEpisode, activeMode]);

  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(utilizador?.hospital || '');
  
  // Dados do formulário para registar um Ato Médico (Consulta ou Exame)
  const [atoData, setAtoData] = useState({ 
    tipo: 'CONSULTA', 
    data_h_inicio: new Date().toISOString().slice(0, 16),
    diagnostico: '',
    exame_fisico: '',
    notas_clinicas: '',
    decisao_clinica: 'CONTINUAR'
  });
  
  // Dados para criar novas prescrições e gerir o internamento
  const [prescData, setPrescData] = useState({ medicamento: '', dosagem: '' });
  const [services, setServices] = useState([]);
  const [internData, setInternData] = useState({ id_servico: '', num_cama: '' });
  const [availableBeds, setAvailableBeds] = useState([]);
  const [loadingBeds, setLoadingBeds] = useState(false);

  // Procura camas livres sempre que o médico escolhe um serviço para internar o paciente
  useEffect(() => {
    if (internData.id_servico) {
      setLoadingBeds(true);
      axios.get(`/clinical/services/${internData.id_servico}/available-beds`)
        .then(res => {
          setAvailableBeds(res.data.camas_disponiveis);
          setLoadingBeds(false);
        })
        .catch(err => {
          console.error('Erro ao buscar camas:', err);
          setLoadingBeds(false);
        });
    } else {
      setAvailableBeds([]);
    }
  }, [internData.id_servico]);

  // --- FUNÇÕES DE AÇÃO (Chamadas por botões ou cliques no ecrã) ---
  // Muda entre o modo de Urgência (azul) e o modo de Internamento (vermelho)
  const handleModeChange = (mode) => {
    setActiveMode(mode);
    setSelectedEpisode(null); // Limpa o paciente selecionado ao mudar de modo
    setIsHospitalizedPatient(mode === 'internamento');
    setInternData({ id_servico: '', num_cama: '' });
    setAvailableBeds([]);
    setSearchQuery(''); // Limpa a pesquisa ao trocar de modo
    setMessage(null);
    
    // Opcional: Limpar as listas locais para mostrar que está a carregar dados novos
    setQueue([]);
    setInternments([]);
    setLoading(true);
    
    fetchQueue(); // Refresh data when switching modes
  };

  useEffect(() => {
    if (utilizador?.hospital) {
      setSelectedHospital(utilizador.hospital);
    }
  }, [utilizador?.hospital]);

  // Vai buscar a lista de hospitais ao servidor quando a página carrega
  useEffect(() => {
    const fetchData = async () => {
      try {
        const resHosp = await axios.get('/clinical/hospitals');
        setHospitals(resHosp.data);
        if (resHosp.data.length > 0 && !selectedHospital) {
          const exists = resHosp.data.find(h => h.nome_hosp === utilizador?.hospital);
          setSelectedHospital(exists ? utilizador.hospital : resHosp.data[0].nome_hosp);
        }
      } catch (e) { console.error(e); }
    };
    fetchData();
  }, []);

  // Atualiza as listas de pacientes (fila de espera e internados) vindas do servidor
  const fetchQueue = async () => {
    if (!selectedHospital) return;
    try {
      const [resQueue, resIntern] = await Promise.all([
        axios.get('/clinical/episodes/awaiting-doctor', { params: { id_hospital: selectedHospital } }),
        axios.get('/clinical/internamentos', { params: { id_hospital: selectedHospital } })
      ]);
      setQueue(resQueue.data);
      setInternments(resIntern.data);
    } catch (error) { console.error('Erro ao carregar dados', error); }
    finally { setLoading(false); }
  };

  useEffect(() => { 
    fetchQueue();
    if (selectedHospital) {
      axios.get(`/clinical/hospitals/${selectedHospital}/services`)
        .then(res => setServices(res.data))
        .catch(err => console.error('Erro ao buscar serviços', err));
    }
  }, [selectedHospital]);

  // Função disparada ao clicar num paciente da lista lateral para ver os seus detalhes
  const handleSelectPatient = async (cod, isIntern = false) => {
    try {
      // 1. Vai buscar os dados básicos do episódio
      const res = await axios.get(`/clinical/episodes/${cod}`);
      setSelectedEpisode(res.data);
      setIsHospitalizedPatient(isIntern);
      
      // 2. Limpa o formulário para começar um novo atendimento
      setAtoData({ 
        tipo: 'CONSULTA', 
        data_h_inicio: new Date().toISOString().slice(0, 16),
        diagnostico: '',
        exame_fisico: '',
        notas_clinicas: '',
        decisao_clinica: 'CONTINUAR'
      });
      setInternData({ id_servico: '', num_cama: '' });
      setAvailableBeds([]);
      
      // 3. Carrega o histórico completo e as receitas que o paciente já tem
      const [histRes, prescRes] = await Promise.all([
        axios.get(`/clinical/utentes/${res.data.id_utente}/history`),
        axios.get(`/clinical/episodes/${cod}/prescriptions`)
      ]);
      setHistory(histRes.data);
      setPrescriptions(prescRes.data);
      setActiveTab('treatment'); // Abre automaticamente a aba de tratamento
    } catch (error) { console.error('Erro ao buscar detalhes', error); }
  };

  const handleSubmitAto = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/atos', {
        ...atoData,
        cod_epis: selectedEpisode.cod_epis,
        id_hosp: selectedEpisode.id_hospital,
        num_func: utilizador?.num_func
      });

      if (atoData.decisao_clinica === 'INTERNAMENTO' && !isHospitalizedPatient) {
        if (!internData.id_servico) {
          alert('Por favor, selecione o serviço para internamento.');
          return;
        }
        await axios.post('/clinical/internamentos', {
          cod_epis: selectedEpisode.cod_epis,
          id_servico: parseInt(internData.id_servico),
          num_cama: internData.num_cama ? parseInt(internData.num_cama) : null,
          data_h_entrada: new Date().toISOString(),
          num_func_medico: utilizador?.num_func
        });
        setMessage({ type: 'success', text: 'Paciente internado com sucesso!' });
      } else if (atoData.decisao_clinica === 'ALTA') {
        if (isHospitalizedPatient) {
          const currentIntern = internments.find(i => i.cod_epis === selectedEpisode.cod_epis);
          if (currentIntern) {
            await axios.post(`/clinical/internamentos/${currentIntern.num_internamento}/discharge`);
          }
        }
        setMessage({ type: 'success', text: 'Alta concedida e episódio finalizado!' });
      } else {
        setMessage({ type: 'success', text: 'Registro clínico guardado!' });
      }
      
      setSelectedEpisode(null);
      setInternData({ id_servico: '', num_cama: '' });
      setAvailableBeds([]);
      fetchQueue();
    } catch (error) { setMessage({ type: 'error', text: 'Erro ao processar decisão clínica.' }); }
  };

  const handleAddPrescription = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/prescricoes', {
        ...prescData,
        cod_epis: selectedEpisode.cod_epis,
        num_func_medico: utilizador?.num_func
      });
      setPrescData({ medicamento: '', dosagem: '' });
      const res = await axios.get(`/clinical/episodes/${selectedEpisode.cod_epis}/prescriptions`);
      setPrescriptions(res.data);
      setMessage({ type: 'success', text: 'Prescrição adicionada!' });
    } catch (error) { setMessage({ type: 'error', text: 'Erro ao prescrever.' }); }
  };

  if (loading) return <div className="loading-container">Carregando prontuário...</div>;

  return (
    <div className="clinical-acts-page">
      <header className="page-header">
        <div className="header-title">
          <Clipboard size={28} className="icon-blue" />
          <h1>Atendimento Clínico</h1>
        </div>
        
        <div className="mode-toggle-group">
          <button 
            className={`mode-btn ${activeMode === 'urgencia' ? 'active urgencia' : ''}`} 
            onClick={() => handleModeChange('urgencia')}
          >
            <Activity size={18} /> Urgências
          </button>
          <button 
            className={`mode-btn ${activeMode === 'internamento' ? 'active internamento' : ''}`} 
            onClick={() => handleModeChange('internamento')}
          >
            <Hotel size={18} /> Internamentos
          </button>
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
            disabled={utilizador?.role === 'MEDICO'}
          >
            <option value="">Selecione...</option>
            {hospitals.map(h => (
              <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="clinical-grid">
        <div className="medical-sidebar">
          {activeMode === 'urgencia' ? (
            <div className="sidebar-section urgencia animate-fade-in">
              <div className="section-header">
                <h3>Fila de Urgência</h3>
                <span className="count">{queue.length}</span>
              </div>
              <div className="search-box-sidebar">
                <Search size={16} />
                <input 
                  type="text" 
                  placeholder="Pesquisar paciente..." 
                  value={searchQuery} 
                  onChange={(e) => setSearchQuery(e.target.value)} 
                />
              </div>
              <div className="queue-list">
                {queue.length === 0 ? <p className="empty-msg">Fila vazia</p> : 
                  queue.filter(ep => 
                    ep.utente_nome.toLowerCase().includes(searchQuery.toLowerCase()) || 
                    ep.cod_epis.toLowerCase().includes(searchQuery.toLowerCase())
                  ).map((ep) => (
                    <div key={ep.cod_epis} className={`queue-item priority-${ep.prioridade.toLowerCase()} ${selectedEpisode?.cod_epis === ep.cod_epis ? 'active' : ''}`} onClick={() => handleSelectPatient(ep.cod_epis, false)}>
                      <div className="patient-meta">
                        <strong>{ep.utente_nome}</strong>
                        <small>{ep.prioridade}</small>
                      </div>
                      <ArrowRight size={16} />
                    </div>
                  ))
                }
              </div>
            </div>
          ) : (
            <div className="sidebar-section internamento animate-fade-in">
              <div className="section-header">
                <h3>Pacientes Internados</h3>
                <span className="count">{internments.length}</span>
              </div>
              <div className="search-box-sidebar">
                <Search size={16} />
                <input 
                  type="text" 
                  placeholder="Pesquisar internado..." 
                  value={searchQuery} 
                  onChange={(e) => setSearchQuery(e.target.value)} 
                />
              </div>
              <div className="queue-list">
                {internments.length === 0 ? <p className="empty-msg">Nenhum internado</p> : 
                  internments.filter(int => 
                    int.utente_nome.toLowerCase().includes(searchQuery.toLowerCase()) || 
                    int.cod_epis.toLowerCase().includes(searchQuery.toLowerCase())
                  ).map((int) => (
                    <div key={int.cod_epis} className={`queue-item intern ${selectedEpisode?.cod_epis === int.cod_epis ? 'active' : ''}`} onClick={() => handleSelectPatient(int.cod_epis, true)}>
                      <div className="patient-meta">
                        <strong>{int.utente_nome}</strong>
                        <small>{int.servico_nome} - Cama {int.num_cama || 'N/A'}</small>
                      </div>
                      <Hotel size={16} />
                    </div>
                  ))
                }
              </div>
            </div>
          )}
        </div>

        <div className="medical-main">
          {message && (
            <div className={`alert alert-${message.type === 'success' ? 'success' : 'danger'} mb-3`} style={{ position: 'relative' }}>
              {message.text}
              <X 
                size={18} 
                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', cursor: 'pointer', opacity: 0.7 }} 
                onClick={() => setMessage(null)} 
              />
            </div>
          )}

          {selectedEpisode ? (
            <div className="workspace">
              <div className={`patient-banner ${activeMode === 'internamento' ? 'intern-theme' : 'urg-theme'}`}>
                <div className="banner-info">
                  <div className="avatar">{selectedEpisode.utente?.nome?.charAt(0)}</div>
                  <div className="details">
                    <h2>{selectedEpisode.utente?.nome} {isHospitalizedPatient && <span className="intern-badge">INTERNADO</span>}</h2>
                    <p>Utente: {selectedEpisode.id_utente} | Episódio: {selectedEpisode.cod_epis}</p>
                  </div>
                </div>
                <div className="vitals">
                  {isHospitalizedPatient ? (
                    <div className="intern-info">
                      <Hotel size={16} /> <span>{internments.find(i => i.cod_epis === selectedEpisode.cod_epis)?.servico_nome}</span>
                    </div>
                  ) : (
                    <>
                      <div className="vital-item"><HeartPulse size={16} /> {selectedEpisode.triagem?.tensao_arterial}</div>
                      <div className="vital-item"><Thermometer size={16} /> {selectedEpisode.triagem?.temperatura}ºC</div>
                    </>
                  )}
                </div>
              </div>
                
              <div className="tab-nav">
                <button className={activeTab === 'treatment' ? 'active' : ''} onClick={() => setActiveTab('treatment')}>Evolução / Atendimento</button>
                <button className={activeTab === 'prescriptions' ? 'active' : ''} onClick={() => setActiveTab('prescriptions')}>Prescrições ({prescriptions.length})</button>
                <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>Histórico Clínico</button>
              </div>

              <div className="tab-content">
                {activeTab === 'treatment' && (
                  <section className="card-form shadow-sm">
                    <div className={`sintomas-box ${activeMode === 'internamento' ? 'intern' : ''}`}>
                      <h6>{activeMode === 'urgencia' ? 'Sintomas na Admissão:' : 'Motivo do Internamento:'}</h6>
                      <p>{selectedEpisode.triagem?.sintomas || 'Não descritos.'}</p>
                    </div>
                    
                    <form onSubmit={handleSubmitAto} className="p-4">
                      <div className="row mb-3">
                        <div className="col-md-6">
                          <label className="form-label">Tipo de Ato</label>
                          <select className="form-select" value={atoData.tipo} onChange={e => setAtoData({...atoData, tipo: e.target.value})}>
                            <option value="CONSULTA">{activeMode === 'internamento' ? 'Consulta de Evolução' : 'Consulta Médica'}</option>
                            <option value="EXAME">Exame de Diagnóstico</option>
                            <option value="INTERVENCAO">Intervenção</option>
                            <option value="TRATAMENTO">Tratamento / Medicação</option>
                          </select>
                        </div>
                        <div className="col-md-6">
                          <label className="form-label">Data/Hora</label>
                          <input type="datetime-local" className="form-control" value={atoData.data_h_inicio} onChange={e => setAtoData({...atoData, data_h_inicio: e.target.value})} required />
                        </div>
                      </div>

                      <div className="mb-3">
                        <label className="form-label">Exame Físico / Sinais Atuais</label>
                        <textarea className="form-control" rows="2" value={atoData.exame_fisico} onChange={e => setAtoData({...atoData, exame_fisico: e.target.value})} />
                      </div>

                      <div className="mb-3">
                        <label className="form-label">Notas Clínicas / Evolução</label>
                        <textarea className="form-control" rows="3" value={atoData.notas_clinicas} onChange={e => setAtoData({...atoData, notas_clinicas: e.target.value})} />
                      </div>

                      <div className="mb-4">
                        <label className="form-label">Diagnóstico</label>
                        <input type="text" className="form-control" value={atoData.diagnostico} onChange={e => setAtoData({...atoData, diagnostico: e.target.value})} />
                      </div>

                      <div className={`decision-box ${activeMode === 'internamento' ? 'intern' : 'urg'}`}>
                        <label className="fw-bold d-block mb-2">Decisão Clínica:</label>
                        <select 
                          className="form-select"
                          value={atoData.decisao_clinica} 
                          onChange={e => setAtoData({...atoData, decisao_clinica: e.target.value})}
                        >
                          <option value="CONTINUAR">Manter {isHospitalizedPatient ? 'Internamento' : 'em Observação'} / Continuar</option>
                          <option value="ALTA">{isHospitalizedPatient ? 'Alta do Internamento (Finalizar Episódio)' : 'Alta Médica (Finalizar Episódio)'}</option>
                          {!isHospitalizedPatient && <option value="INTERNAMENTO">Mover para Internamento</option>}
                        </select>
                      </div>

                      {atoData.decisao_clinica === 'INTERNAMENTO' && !isHospitalizedPatient && (
                        <div className="intern-subform animate-fade-in">
                          <div className="row g-3">
                            <div className="col-md-8">
                              <label className="form-label">Serviço de Destino</label>
                              <select className="form-select" value={internData.id_servico} onChange={e => setInternData({...internData, id_servico: e.target.value})} required>
                                <option value="">Selecione o Serviço...</option>
                                {services.map(s => <option key={s.id_servico} value={s.id_servico}>{s.nome}</option>)}
                              </select>
                            </div>
                            <div className="col-md-4">
                              <label className="form-label">Cama Disponível</label>
                              <select 
                                className="form-select" 
                                value={internData.num_cama} 
                                onChange={e => setInternData({...internData, num_cama: e.target.value})}
                                disabled={!internData.id_servico || loadingBeds}
                                required
                              >
                                <option value="">{loadingBeds ? 'A carregar...' : 'Escolher...'}</option>
                                {availableBeds.map(cama => (
                                  <option key={cama} value={cama}>Cama {cama}</option>
                                ))}
                                {!loadingBeds && internData.id_servico && availableBeds.length === 0 && (
                                  <option value="" disabled>Sem camas livres</option>
                                )}
                              </select>
                            </div>
                          </div>
                          {internData.id_servico && (
                            <p className="mt-2 small text-muted">
                              Cada especialidade dispõe de 15 camas no total. 
                              {availableBeds.length > 0 ? ` Estão livres ${availableBeds.length} camas.` : ' Atenção: Lotação esgotada.'}
                            </p>
                          )}
                        </div>
                      )}

                      <button type="submit" className={`btn ${activeMode === 'internamento' ? 'btn-danger' : 'btn-primary'} w-100 mt-4 py-3`}>
                        {atoData.decisao_clinica === 'ALTA' ? 'Confirmar Alta e Fechar Episódio' : 
                         atoData.decisao_clinica === 'INTERNAMENTO' ? 'Processar Internamento' : 
                         'Gravar Registro Clínico'}
                      </button>
                    </form>
                  </section>
                )}

                {activeTab === 'prescriptions' && (
                  <section className="card-form shadow-sm p-4">
                    <form onSubmit={handleAddPrescription} className="mb-4 d-flex gap-3 align-items-end">
                      <div className="flex-grow-1">
                        <label className="form-label">Medicamento</label>
                        <input type="text" className="form-control" value={prescData.medicamento} onChange={e => setPrescData({...prescData, medicamento: e.target.value})} required />
                      </div>
                      <div style={{ width: '200px' }}>
                        <label className="form-label">Dosagem</label>
                        <input type="text" className="form-control" value={prescData.dosagem} onChange={e => setPrescData({...prescData, dosagem: e.target.value})} required />
                      </div>
                      <button type="submit" className={`btn ${activeMode === 'internamento' ? 'btn-danger' : 'btn-primary'}`}>Adicionar</button>
                    </form>
                    <table className="table table-hover">
                      <thead className="table-light"><tr><th>Medicamento</th><th>Dosagem</th><th>Médico</th><th>Data</th></tr></thead>
                      <tbody>
                        {prescriptions.map((p, i) => (
                          <tr key={i}>
                            <td>{p.medicamento}</td>
                            <td>{p.dosagem}</td>
                            <td>{p.medico_nome} ({p.medico_username})</td>
                            <td>{new Date(p.data_h_presc).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </section>
                )}

                {activeTab === 'history' && (
                  <div className="history-timeline">
                    {history.map((item, i) => {
                      // Criar uma lista única de eventos para este episódio e ordenar cronologicamente
                      const events = [
                        { type: 'triagem', date: new Date(item.triagem?.data_h_triagem), data: item.triagem },
                        ...(item.atos || []).map(a => ({ type: 'ato', date: new Date(a.data_h_inicio), data: a })),
                        ...(item.prescricoes || []).map(p => ({ type: 'presc', date: new Date(p.data_h_presc), data: p }))
                      ]
                      .filter(e => e.date && !isNaN(e.date.getTime()))
                      .sort((a, b) => a.date - b.date);

                      return (
                        <div key={i} className="history-card">
                          <div className="history-header">
                            <strong>Episódio: {item.episodio.cod_epis}</strong>
                            <span className="date">{new Date(item.episodio.data_h_entrada).toLocaleDateString()}</span>
                          </div>
                          <div className="history-body">
                            {events.map((ev, idx) => (
                              <div key={idx} className="history-step">
                                <span className={`tag ${ev.type}`}>{ev.type === 'presc' ? 'Prescrição' : ev.type === 'ato' ? `Ato (${ev.data.tipo})` : 'Triagem'}</span>
                                <span className="event-time">{ev.date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                
                                {ev.type === 'triagem' && (
                                  <p><strong>Queixa:</strong> {ev.data.sintomas} | <strong>Enfermeiro/a:</strong> {ev.data.profissional_info?.nome}</p>
                                )}
                                {ev.type === 'ato' && (
                                  <p><strong>Diag:</strong> {ev.data.diagnostico || '---'} | <strong>Prof:</strong> {ev.data.profissional_nome}</p>
                                )}
                                {ev.type === 'presc' && (
                                  <p><strong>Med:</strong> {ev.data.medicamento} ({ev.data.dosagem}) | <strong>Prof:</strong> {ev.data.medico_nome}</p>
                                )}
                              </div>
                            ))}
                            {item.internamento && (
                              <div className="history-step">
                                <span className="tag intern">Internamento</span>
                                <span className="event-time">{new Date(item.internamento.data_h_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                <p><strong>Médico Resp:</strong> {item.internamento.medico_nome} ({item.internamento.medico_username})</p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="empty-workspace">
              {activeMode === 'urgencia' ? <Activity size={80} /> : <Hotel size={80} />}
              <h3>{activeMode === 'urgencia' ? 'Pronto para Atendimento de Urgência' : 'Pronto para Evolução em Internamento'}</h3>
              <p>Selecione um paciente na lista lateral para iniciar.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .clinical-acts-page { padding: 1.5rem; background: #f0f2f5; min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .page-header { display: flex; justify-content: space-between; align-items: center; background: white; padding: 1rem 2rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .header-title { display: flex; align-items: center; gap: 12px; }
        .header-title h1 { font-size: 1.5rem; margin: 0; color: #1e293b; }

        .mode-toggle-group { display: flex; background: #f1f5f9; padding: 4px; border-radius: 10px; gap: 4px; }
        .mode-btn { border: none; padding: 8px 1.5rem; border-radius: 8px; font-weight: 600; color: #64748b; background: none; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all 0.2s; }
        .mode-btn.active.urgencia { background: #2563eb; color: white; box-shadow: 0 4px 6px rgba(37,99,235,0.2); }
        .mode-btn.active.internamento { background: #dc2626; color: white; box-shadow: 0 4px 6px rgba(220,38,38,0.2); }

        .clinical-grid { display: grid; grid-template-columns: 300px 1fr; gap: 1.5rem; }
        
        .sidebar-section { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: calc(100vh - 200px); display: flex; flex-direction: column; }
        .section-header { padding: 1rem; color: white; display: flex; justify-content: space-between; align-items: center; }
        .urgencia .section-header { background: #2563eb; }
        .internamento .section-header { background: #dc2626; }
        .count { background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: bold; }
        
        .search-box-sidebar { padding: 10px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; gap: 8px; }
        .search-box-sidebar input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; color: #475569; }
        .search-box-sidebar svg { color: #94a3b8; }

        .queue-list { overflow-y: auto; flex: 1; }
        .queue-item { padding: 1.25rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; border-left: 4px solid transparent; }
        .queue-item:hover { background: #f8fafc; }
        .queue-item.active { background: #f1f5f9; border-left-width: 6px; }
        
        .priority-vermelho { border-left-color: #ef4444; }
        .priority-laranja { border-left-color: #f97316; }
        .priority-amarelo { border-left-color: #eab308; }
        .priority-verde { border-left-color: #22c55e; }
        .priority-azul { border-left-color: #3b82f6; }
        .queue-item.intern.active { border-left-color: #dc2626; }

        .patient-banner { border-radius: 12px; padding: 1.5rem; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .urg-theme { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); }
        .intern-theme { background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); }
        
        .banner-info { display: flex; align-items: center; gap: 1.5rem; }
        .avatar { width: 50px; height: 50px; background: rgba(255,255,255,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: bold; }
        .details h2 { margin: 0; font-size: 1.4rem; }
        .details p { margin: 0; opacity: 0.8; font-size: 0.9rem; }
        .intern-badge { background: white; color: #dc2626; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; vertical-align: middle; margin-left: 10px; font-weight: bold; }

        .vitals { display: flex; gap: 1.5rem; font-weight: bold; }
        .vital-item { display: flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.1); padding: 5px 12px; border-radius: 20px; }

        .tab-nav { display: flex; gap: 10px; margin-bottom: 1.5rem; border-bottom: 2px solid #e2e8f0; }
        .tab-nav button { background: none; border: none; padding: 0.75rem 1rem; font-weight: 600; color: #64748b; cursor: pointer; position: relative; }
        .tab-nav button.active { color: #1e293b; }
        .tab-nav button.active::after { content: ''; position: absolute; bottom: -2px; left: 0; right: 0; height: 3px; background: #2563eb; border-radius: 3px; }

        .card-form { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .sintomas-box { padding: 1rem 1.5rem; background: #fff7ed; border-left: 5px solid #f97316; }
        .sintomas-box.intern { background: #fef2f2; border-left-color: #ef4444; }
        .sintomas-box h6 { margin-bottom: 4px; color: #9a3412; }
        .sintomas-box.intern h6 { color: #991b1b; }
        
        .decision-box { padding: 1.5rem; border-radius: 10px; margin-top: 1rem; }
        .decision-box.urg { background: #eff6ff; border: 1px solid #bfdbfe; }
        .decision-box.intern { background: #fef2f2; border: 1px solid #fecaca; }
        
        .empty-workspace { height: 500px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; }
        
        .history-card { background: white; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #e2e8f0; overflow: hidden; }
        .history-header { background: #f8fafc; padding: 0.75rem 1rem; display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; }
        .history-body { padding: 1rem; }
        .history-step { margin-bottom: 1rem; padding-left: 1rem; border-left: 2px solid #e2e8f0; position: relative; }
        .tag { font-size: 0.7rem; font-weight: bold; text-transform: uppercase; padding: 2px 6px; border-radius: 4px; margin-bottom: 4px; display: inline-block; }
        .tag.triagem { background: #fef3c7; color: #92400e; }
        .tag.ato { background: #dbeafe; color: #1e40af; }
        .tag.intern { background: #fee2e2; color: #991b1b; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fadeIn 0.3s ease-out; }
      `}</style>
    </div>
  );
};

export default ClinicalActs;