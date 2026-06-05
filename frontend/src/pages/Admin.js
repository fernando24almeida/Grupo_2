import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  UserCog, Users, PlusCircle, Shield, Activity, Save, 
  Trash2, Edit2, Search, Hotel, Clipboard, X, Mail, User, ShieldCheck,
  History, Eye, FileText, Settings, Database, Briefcase, LogOut
} from 'lucide-react';

import { usarAutenticacao } from '../services/AuthContext';

const Admin = () => {
  const { utilizador, hospital: globalHospital } = usarAutenticacao();
  const [activeTab, setActiveTab] = useState('active_flow');
  const [papeis, setPapeis] = useState([]);
  const [hospitais, setHospitais] = useState([]);
  const [utilizadores, setUtilizadores] = useState([]);
  const [utentes, setUtentes] = useState([]);
  const [episodiosAtivos, setEpisodiosAtivos] = useState([]);
  const [episodiosArquivados, setEpisodiosArquivados] = useState([]);
  const [aguardandoTriagem, setAguardandoTriagem] = useState([]);
  const [triagens, setTriagens] = useState([]);
  const [atos, setAtos] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [internamentos, setInternamentos] = useState([]);
  
  // Estados para Criação
  const [nomeUtilizador, setNomeUtilizador] = useState('');
  const [nomeCompleto, setNomeCompleto] = useState('');
  const [email, setEmail] = useState('');
  const [telemovel, setTelemovel] = useState('');
  const [palavraPasse, setPalavraPasse] = useState('');
  const [idRole, setIdRole] = useState('');
  const [numFunc, setNumFunc] = useState('');
  const [isAutoRole, setIsAutoRole] = useState(false);
  
  const [nomeHosp, setNomeHosp] = useState('');
  const [localHosp, setLocalHosp] = useState('');

  const [profNumFunc, setProfNumFunc] = useState('');
  const [profSexo, setProfSexo] = useState('Masculino');
  const [profTipo, setProfTipo] = useState('MEDICO');
  const [profEstagiario, setProfEstagiario] = useState('NÃO');
  
  const [uNome, setUNome] = useState('');
  const [uEmail, setUEmail] = useState('');
  const [uNum, setUNum] = useState('');
  const [uTel, setUTel] = useState('');
  const [uMorada, setUMorada] = useState('');
  const [uLocalidade, setULocalidade] = useState('');
  const [uSexo, setUSexo] = useState('M');
  const [uDataNasc, setUDataNasc] = useState('');
  const [uParentesco, setUParentesco] = useState('');
  
  // Estados para Edição e Visualização
  const [editingItem, setEditingItem] = useState(null);
  const [journeyEpisode, setJourneyEpisode] = useState(null);
  const [historyUtente, setHistoryUtente] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [mensagem, setMensagem] = useState({ tipo: '', texto: '' });

  // Auto-close das mensagens após 30 segundos
  useEffect(() => {
    if (mensagem.texto) {
      const timer = setTimeout(() => {
        setMensagem({ tipo: '', texto: '' });
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [mensagem]);

  // Limpar mensagens ao mudar de aba
  useEffect(() => {
    setMensagem({ tipo: '', texto: '' });
    // Refresh data when switching back to main tabs that show live data
    if (activeTab === 'active_flow' || activeTab === 'utentes' || activeTab === 'users') {
      fetchData();
    }
  }, [activeTab]);

  // Filtros
  const [filtros, setFiltros] = useState({ 
    user: '', userType: '', utente: '', episode: '', 
    hospital: globalHospital || '', triagem: '', ato: '', audit: ''
  });

  useEffect(() => {
    setFiltros(prev => ({ ...prev, hospital: globalHospital || '' }));
  }, [globalHospital]);

  const menuItems = [
    { id: 'active_flow', label: 'Fluxo Ativo', icon: Activity },
    { id: 'archive', label: 'Arquivo Histórico', icon: Database },
    { id: 'utentes', label: 'Utentes', icon: Users },
    { id: 'users', label: 'Utilizadores', icon: Shield },
    { id: 'system', label: 'Configuração', icon: Settings },
    { id: 'audit', label: 'Auditoria', icon: History },
  ];

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = filtros.hospital ? { id_hospital: filtros.hospital } : {};
      
      const requests = [
        axios.get('/auth/roles'),
        axios.get('/clinical/hospitals'),
        axios.get('/auth/users'),
        axios.get('/clinical/utentes'),
        axios.get('/clinical/episodes', { params: { ...params, em_aberto: true } }),
        axios.get('/clinical/episodes', { params: { ...params, em_aberto: false } }),
        axios.get('/clinical/episodes/awaiting-triage', { params }),
        axios.get('/auth/audit'),
        axios.get('/clinical/internamentos', { params })
      ];

      const results = await Promise.allSettled(requests);

      if (results[0].status === 'fulfilled') setPapeis(results[0].value.data);
      if (results[1].status === 'fulfilled') setHospitais(results[1].value.data);
      if (results[2].status === 'fulfilled') setUtilizadores(results[2].value.data);
      if (results[3].status === 'fulfilled') setUtentes(results[3].value.data);
      if (results[4].status === 'fulfilled') setEpisodiosAtivos(results[4].value.data);
      if (results[5].status === 'fulfilled') setEpisodiosArquivados(results[5].value.data);
      if (results[6].status === 'fulfilled') setAguardandoTriagem(results[6].value.data);
      if (results[7].status === 'fulfilled') setAuditLogs(results[7].value.data);
      if (results[8].status === 'fulfilled') setInternamentos(results[8].value.data);

    } catch (erro) {
      console.error('Erro fatal ao carregar dados', erro);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filtros.hospital]);

  const detectRole = async (num) => {
    if (!num) {
      setIsAutoRole(false);
      return;
    }
    try {
      const response = await axios.get(`/auth/professionals/${num}`);
      if (response.data.id_role) {
        setIdRole(response.data.id_role.toString());
        setIsAutoRole(true);
      }
    } catch (erro) {
      setIsAutoRole(false);
    }
  };

  const criarUtilizador = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/auth/users', {
        nome_utilizador: nomeUtilizador,
        nome_completo: nomeCompleto,
        email: email,
        palavra_passe: palavraPasse,
        id_role: idRole ? parseInt(idRole) : null,
        num_func: numFunc ? parseInt(numFunc) : null
      });
      setMensagem({ tipo: 'success', texto: `Utilizador ${nomeUtilizador} criado!` });
      setNomeUtilizador(''); setNomeCompleto(''); setEmail(''); setPalavraPasse(''); setIdRole(''); setNumFunc(''); setIsAutoRole(false);
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao criar utilizador.' });
    }
  };

  const criarProfissional = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/auth/professionals', {
        num_func: parseInt(profNumFunc),
        sexo: profSexo,
        tipo_func: profTipo,
        estagiario: profTipo === 'MEDICO' ? profEstagiario : null
      });
      setMensagem({ tipo: 'success', texto: `Profissional ${profNumFunc} registado com sucesso!` });
      
      const confirmMsg = `Profissional registado. Deseja criar agora a conta de utilizador para este profissional?`;
      if (window.confirm(confirmMsg)) {
        setNumFunc(profNumFunc);
        detectRole(profNumFunc);
        setActiveTab('system');
        document.getElementById('form-utilizador')?.scrollIntoView({ behavior: 'smooth' });
      }
      setProfNumFunc('');
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao registar profissional.' });
    }
  };

  const criarHospital = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/hospitals', { nome_hosp: nomeHosp, local_hosp: localHosp });
      setMensagem({ tipo: 'success', texto: `Hospital ${nomeHosp} criado com sucesso!` });
      setNomeHosp(''); setLocalHosp('');
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: 'Erro ao criar hospital.' });
    }
  };

  const criarUtenteApp = async (e) => {
    e.preventDefault();

    // Validação básica
    if (!uNum || !uNome || !uEmail) {
      setMensagem({ tipo: 'error', texto: 'Nº Utente, Nome e E-mail são obrigatórios.' });
      return;
    }

    try {
      await axios.post('/clinical/utentes', {
        num_utente: parseInt(uNum),
        nome: uNome,
        email: uEmail,
        telemovel: uTel || null,
        morada: uMorada || null,
        localidade: uLocalidade || null,
        sexo: uSexo || "M",
        data_nascimento: uDataNasc || null,
        parentesco: uParentesco || null
      });
      setMensagem({ tipo: 'success', texto: `Utente ${uNome} registado!` });
      setUNome(''); setUEmail(''); setUNum(''); setUTel('');
      setUMorada(''); setULocalidade(''); setUSexo('M'); setUDataNasc(''); setUParentesco('');
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao registar utente.' });
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    const { type, data } = editingItem;
    let url = '';
    let payload = { ...data };

    try {
      if (type === 'user') {
        url = `/auth/users/${data.id_utilizador}`;
        delete payload.id_utilizador;
        if (!payload.palavra_passe) delete payload.palavra_passe;
      } else if (type === 'utente') {
        url = `/clinical/utentes/${data.num_utente}`;
        delete payload.num_utente;
      } else if (type === 'hospital') {
        url = `/clinical/hospitals/${data.nome_hosp}`;
        delete payload.nome_hosp;
      } else if (type === 'episode') {
        url = `/clinical/episodes/${data.cod_epis}`;
        delete payload.cod_epis;
      } else if (type === 'triagem') {
        url = `/clinical/triagens/${data.num_triagem}/audit`;
        if (!payload.justificativa || !payload.autorizacao) {
          alert("Justificativa e Autorização são obrigatórias.");
          return;
        }
      }

      await axios.patch(url, payload);
      setMensagem({ tipo: 'success', texto: 'Registo atualizado com sucesso!' });
      setEditingItem(null);
      fetchData();
    } catch (erro) {
      const errorMsg = erro.response?.data?.detail || 'Erro ao atualizar registo.';
      if (erro.response?.status === 400) {
        alert(`AVISO: ${errorMsg}`);
      }
      setMensagem({ tipo: 'error', texto: errorMsg });
    }
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm('Tem a certeza que deseja eliminar este registo?')) return;
    try {
      let url = '';
      if (type === 'user') url = `/auth/users/${id}`;
      else if (type === 'utente') url = `/clinical/utentes/${id}`;
      else if (type === 'hospital') url = `/clinical/hospitals/${id}`;
      else if (type === 'episode') url = `/clinical/episodes/${id}`;

      await axios.delete(url);
      setMensagem({ tipo: 'success', texto: 'Registo eliminado com sucesso!' });
      fetchData();
    } catch (erro) {
      const errorMsg = erro.response?.data?.detail || 'Erro ao eliminar registo.';
      if (erro.response?.status === 400) {
        alert(`NÃO É POSSÍVEL ELIMINAR:\n\n${errorMsg}`);
      }
      setMensagem({ tipo: 'error', texto: errorMsg });
    }
  };

  const verPercursoEpisodio = async (codEpis) => {
    try {
      const res = await axios.get(`/clinical/episodes/${codEpis}/journey`);
      setJourneyEpisode(res.data);
    } catch (erro) {
      const msg = erro.response?.data?.detail || 'Erro ao carregar percurso.';
      setMensagem({ tipo: 'error', texto: msg });
    }
  };

  const verHistoricoUtente = async (numUtente) => {
    try {
      const res = await axios.get(`/clinical/utentes/${numUtente}/history`);
      setHistoryUtente(res.data);
    } catch (erro) {
      const msg = erro.response?.data?.detail || 'Erro ao carregar histórico do utente.';
      setMensagem({ tipo: 'error', texto: msg });
    }
  };

  const darAltaInternamento = async (id) => {
    if (!window.confirm('Confirmar alta do internamento?')) return;
    try {
      await axios.post(`/clinical/internamentos/${id}/discharge`);
      setMensagem({ tipo: 'success', texto: 'Alta de internamento registada!' });
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: 'Erro ao registar alta.' });
    }
  };

  const toggleUserStatus = async (id, currentStatus) => {
    const action = currentStatus ? 'suspender' : 'ativar';
    if (!window.confirm(`Tem a certeza que deseja ${action} este utilizador?`)) return;
    try {
      await axios.post(`/auth/users/${id}/toggle-status`);
      setMensagem({ tipo: 'success', texto: `Utilizador ${action === 'ativar' ? 'ativado' : 'suspenso'} com sucesso!` });
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: `Erro ao ${action} utilizador.` });
    }
  };

  const toggleUtenteStatus = async (id, currentStatus) => {
    const action = currentStatus ? 'suspender' : 'ativar';
    if (!window.confirm(`Tem a certeza que deseja ${action} este utente?`)) return;
    try {
      await axios.post(`/clinical/utentes/${id}/toggle-status`);
      setMensagem({ tipo: 'success', texto: `Utente ${action === 'ativar' ? 'ativado' : 'suspenso'} com sucesso!` });
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: `Erro ao ${action} utente.` });
    }
  };

  const resendUserActivation = async (id) => {
    try {
      await axios.post(`/auth/users/${id}/resend-activation`);
      setMensagem({ tipo: 'success', texto: 'E-mail de ativação reenviado com sucesso!' });
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao reenviar ativação.' });
    }
  };

  const resendUtenteActivation = async (id) => {
    try {
      await axios.post(`/clinical/utentes/${id}/resend-activation`);
      setMensagem({ tipo: 'success', texto: 'Novo PIN e código de ativação enviados!' });
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao reenviar ativação.' });
    }
  };

  const simularEpisodios = async () => {
    const hospitalSelecionado = filtros.hospital;
    const confirmMsg = hospitalSelecionado 
      ? `Deseja simular 200 episódios para o hospital "${hospitalSelecionado}"?` 
      : 'Deseja simular 200 episódios distribuídos por todos os hospitais?';
      
    if (!window.confirm(confirmMsg)) return;
    
    setLoading(true);
    try {
      const res = await axios.post('/analytics/simulate-episodes', null, {
        params: { id_hospital: hospitalSelecionado }
      });
      setMensagem({ tipo: 'success', texto: `${res.data.message} (${res.data.total} episódios criados)` });
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao simular episódios.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-layout-container">
      <aside className="admin-side-nav">
        <div className="admin-nav-header">
          <UserCog size={24} />
          <h3>Administração</h3>
        </div>
        <nav className="admin-nav-list">
          {menuItems.map(item => (
            <button 
              key={item.id}
              className={`admin-nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="admin-main-content">
        <header className="admin-header">
          <div className="admin-header-left">
            <h2 className="admin-tab-title">{menuItems.find(i => i.id === activeTab)?.label}</h2>
          </div>
          <div className="admin-header-right">
            <div className="hospital-filter">
              <Hotel size={16} />
              <select 
                value={filtros.hospital}
                onChange={(e) => setFiltros({...filtros, hospital: e.target.value})}
              >
                <option value="">Todos os Hospitais</option>
                {hospitais.map(h => <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>)}
              </select>
            </div>
            <button className="btn-refresh" onClick={fetchData} title="Atualizar Dados">
              <History size={18} />
            </button>
            <button className="btn-simulate" onClick={simularEpisodios} title="Simular 200 Episódios">
              <PlusCircle size={18} />
              <span>Simular Episódios</span>
            </button>
          </div>
        </header>

        {mensagem.texto && (
          <div className={`alert alert-${mensagem.tipo}`}>
            <span>{mensagem.texto}</span>
            <X size={18} className="close-msg" onClick={() => setMensagem({ ...mensagem, texto: '' })} />
          </div>
        )}

        {/* MODAL DE EDIÇÃO */}
        {editingItem && (
          <div className="admin-modal-overlay">
            <div className="admin-modal-content">
              <div className="modal-header">
                <h3>Editar {editingItem.type === 'utente' ? 'Utente' : 'Utilizador'}</h3>
                <button className="close-btn" onClick={() => setEditingItem(null)}><X size={24}/></button>
              </div>
              <form onSubmit={handleUpdate} className="standard-form">
                {editingItem.type === 'utente' ? (
                  <>
                    <div className="form-group">
                      <label>NIF (Não editável)</label>
                      <input type="text" value={editingItem.data.num_utente} disabled className="bg-disabled" />
                    </div>
                    <div className="form-group">
                      <label>Nome Completo</label>
                      <input 
                        type="text" 
                        value={editingItem.data.nome} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, nome: e.target.value}})}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Email</label>
                      <input 
                        type="email" 
                        value={editingItem.data.email || ''} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, email: e.target.value}})}
                        placeholder="Insira o e-mail para envio de credenciais"
                      />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Telemóvel</label>
                        <input 
                          type="text" 
                          value={editingItem.data.telemovel || ''} 
                          onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, telemovel: e.target.value}})}
                        />
                      </div>
                      <div className="form-group">
                        <label>Sexo</label>
                        <select 
                          value={editingItem.data.sexo} 
                          onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, sexo: e.target.value}})}
                        >
                          <option value="M">Masculino</option>
                          <option value="F">Feminino</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Morada</label>
                      <input 
                        type="text" 
                        value={editingItem.data.morada || ''} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, morada: e.target.value}})}
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="form-group">
                      <label>Username (Não editável)</label>
                      <input type="text" value={editingItem.data.nome_utilizador} disabled className="bg-disabled" />
                    </div>
                    <div className="form-group">
                      <label>Nome Completo</label>
                      <input 
                        type="text" 
                        value={editingItem.data.nome_completo} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, nome_completo: e.target.value}})}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Email</label>
                      <input 
                        type="email" 
                        value={editingItem.data.email} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, email: e.target.value}})}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Nova Password (deixe vazio para manter)</label>
                      <input 
                        type="password" 
                        value={editingItem.data.palavra_passe || ''} 
                        onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, palavra_passe: e.target.value}})}
                      />
                    </div>
                  </>
                )}
                <div className="modal-footer">
                  <button type="button" className="btn-secondary" onClick={() => setEditingItem(null)}>Cancelar</button>
                  <button type="submit" className="btn-primary">Guardar Alterações</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL DE PERCURSO DO EPISÓDIO */}
        {journeyEpisode && (
          <div className="admin-modal-overlay">
            <div className="admin-modal-content large">
              <div className="modal-header">
                <h3>Percurso Completo: {journeyEpisode.episodio.cod_epis}</h3>
                <button className="close-btn" onClick={() => setJourneyEpisode(null)}><X size={24}/></button>
              </div>
              <div className="journey-body">
                <div className="journey-summary">
                  <div className="summary-card">
                    <h4><User size={18}/> Utente</h4>
                    <p><strong>Nome:</strong> {journeyEpisode.utente.nome}</p>
                    <p><strong>NIF:</strong> {journeyEpisode.utente.num_utente}</p>
                  </div>
                  <div className="summary-card">
                    <h4><Activity size={18}/> Estado</h4>
                    <p><strong>Entrada:</strong> {new Date(journeyEpisode.episodio.data_h_entrada).toLocaleString()}</p>
                    <p><strong>Status:</strong> {journeyEpisode.episodio.data_h_saida ? 'Alta' : 'Ativo'}</p>
                    <p><strong>Admissão:</strong> {journeyEpisode.episodio.profissional_info?.nome} ({journeyEpisode.episodio.profissional_info?.username} | ID: {journeyEpisode.episodio.profissional_info?.num_func})</p>
                  </div>
                </div>

                <div className="timeline">
                  <div className="timeline-item">
                    <div className="timeline-icon"><Clipboard size={16} /></div>
                    <div className="timeline-content">
                      <h5>Triagem</h5>
                      {journeyEpisode.triagem ? (
                        <>
                          <span className={`priority-tag ${journeyEpisode.triagem.prioridade?.toLowerCase() || 'gray'}`}>{journeyEpisode.triagem.prioridade}</span>
                          <p><strong>Sintomas:</strong> {journeyEpisode.triagem.sintomas}</p>
                          <p><strong>Profissional:</strong> {journeyEpisode.triagem.profissional_info?.nome} ({journeyEpisode.triagem.profissional_info?.username} | ID: {journeyEpisode.triagem.profissional_info?.num_func})</p>
                        </>
                      ) : <p>Não realizada.</p>}
                    </div>
                  </div>

                  {journeyEpisode.atos && journeyEpisode.atos.map((ato, i) => (
                    <div className="timeline-item" key={i}>
                      <div className="timeline-icon"><Briefcase size={16} /></div>
                      <div className="timeline-content">
                        <h5>Ato: {ato.tipo}</h5>
                        <p><strong>Diagnóstico:</strong> {ato.diagnostico || '---'}</p>
                        <p><strong>Decisão:</strong> {ato.decisao_clinica || '---'}</p>
                        <p><strong>Profissional:</strong> {ato.profissional_info?.nome} ({ato.profissional_info?.username} | ID: {ato.profissional_info?.num_func})</p>
                        <small>{ato.data_h_inicio ? new Date(ato.data_h_inicio).toLocaleString() : '---'}</small>
                      </div>
                    </div>
                  ))}

                  {journeyEpisode.prescricoes && journeyEpisode.prescricoes.map((p, i) => (
                    <div className="timeline-item" key={i}>
                      <div className="timeline-icon"><FileText size={16} /></div>
                      <div className="timeline-content">
                        <h5>Prescrição Médica</h5>
                        <p><strong>Medicação:</strong> {p.medicamento} ({p.dosagem})</p>
                        <p><strong>Médico:</strong> {p.profissional_info?.nome} ({p.profissional_info?.username} | ID: {p.profissional_info?.num_func})</p>
                        <small>{p.data_h_presc ? new Date(p.data_h_presc).toLocaleString() : '---'}</small>
                      </div>
                    </div>
                  ))}

                  {journeyEpisode.internamento && (
                    <div className="timeline-item special">
                      <div className="timeline-icon"><Hotel size={16} /></div>
                      <div className="timeline-content">
                        <h5>Internamento</h5>
                        <p><strong>Entrada:</strong> {journeyEpisode.internamento.data_h_entrada ? new Date(journeyEpisode.internamento.data_h_entrada).toLocaleString() : '---'}</p>
                        <p><strong>Cama:</strong> {journeyEpisode.internamento.num_cama || 'N/A'}</p>
                        <p><strong>Médico Responsável:</strong> {journeyEpisode.internamento.profissional_info?.nome} ({journeyEpisode.internamento.profissional_info?.username} | ID: {journeyEpisode.internamento.profissional_info?.num_func})</p>
                        {journeyEpisode.internamento.data_h_saida && (
                          <p className="text-success"><strong>Alta:</strong> {new Date(journeyEpisode.internamento.data_h_saida).toLocaleString()}</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MODAL DE HISTÓRICO COMPLETO DO UTENTE */}
        {historyUtente && (
          <div className="admin-modal-overlay">
            <div className="admin-modal-content large">
              <div className="modal-header">
                <h3>Histórico Clínico: {historyUtente[0]?.utente?.nome || 'Utente'}</h3>
                <button className="close-btn" onClick={() => setHistoryUtente(null)}><X size={24}/></button>
              </div>
              <div className="journey-body">
                <div className="admin-history-list">
                  {historyUtente.map((item, i) => {
                    const events = [
                      { type: 'triagem', date: new Date(item.triagem?.data_h_triagem), data: item.triagem },
                      ...(item.atos || []).map(a => ({ type: 'ato', date: new Date(a.data_h_inicio), data: a })),
                      ...(item.prescricoes || []).map(p => ({ type: 'presc', date: new Date(p.data_h_presc), data: p }))
                    ]
                    .filter(e => e.date && !isNaN(e.date.getTime()))
                    .sort((a, b) => a.date - b.date);

                    return (
                      <div key={i} className="history-episode-card mb-4">
                        <div className="history-episode-header">
                          <div className="d-flex align-items-center gap-3">
                            <span className="badge-episodio">EPISÓDIO: {item.episodio.cod_epis}</span>
                            <span className="date-episodio">{new Date(item.episodio.data_h_entrada).toLocaleDateString()}</span>
                          </div>
                          <span className={`status-tag ${item.episodio.data_h_saida ? 'closed' : 'open'}`}>
                            {item.episodio.data_h_saida ? 'ARQUIVADO' : 'EM CURSO'}
                          </span>
                        </div>
                        
                        <div className="timeline-unified">
                          {events.map((ev, idx) => (
                            <div key={idx} className="timeline-step">
                              <div className="timeline-marker"></div>
                              <div className="timeline-info">
                                <div className="d-flex align-items-center gap-2 mb-1">
                                  <span className={`badge-type ${ev.type}`}>{ev.type.toUpperCase()}</span>
                                  <span className="time-marker">{ev.date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                                {ev.type === 'triagem' && (
                                  <div className="step-details">
                                    <p><strong>Prioridade:</strong> <span className={`priority-mini ${ev.data.prioridade?.toLowerCase()}`}>{ev.data.prioridade}</span></p>
                                    <p><strong>Sintomas:</strong> {ev.data.sintomas}</p>
                                    <p><strong>Enfermeiro/a:</strong> {ev.data.profissional_info?.nome}</p>
                                  </div>
                                )}
                                {ev.type === 'ato' && (
                                  <div className="step-details">
                                    <p><strong>Tipo:</strong> {ev.data.tipo}</p>
                                    <p><strong>Diagnóstico:</strong> {ev.data.diagnostico || '---'}</p>
                                    <p><strong>Profissional:</strong> {ev.data.profissional_info?.nome}</p>
                                  </div>
                                )}
                                {ev.type === 'presc' && (
                                  <div className="step-details">
                                    <p><strong>Medicação:</strong> {ev.data.medicamento} ({ev.data.dosagem})</p>
                                    <p><strong>Médico:</strong> {ev.data.profissional_info?.nome}</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                          {item.internamento && (
                            <div className="timeline-step special-step">
                              <div className="timeline-marker red"></div>
                              <div className="timeline-info">
                                <div className="d-flex align-items-center gap-2 mb-1">
                                  <span className="badge-type intern">INTERNAMENTO</span>
                                  <span className="time-marker">{new Date(item.internamento.data_h_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                                <div className="step-details">
                                  <p><strong>Cama:</strong> {item.internamento.num_cama || 'N/A'}</p>
                                  <p><strong>Médico Resp:</strong> {item.internamento.profissional_info?.nome}</p>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {historyUtente.length === 0 && <p className="text-center p-5 text-muted">Este utente ainda não possui histórico de episódios.</p>}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="admin-tab-panels">
          {activeTab === 'active_flow' && (
            <div className="flow-container">
              {/* 1. AGUARDANDO TRIAGEM */}
              <section className="admin-card">
                <div className="card-header bg-warning-light">
                  <Clipboard size={18} /> 
                  <h3>Aguardando Triagem ({aguardandoTriagem.length})</h3>
                </div>
                <div className="card-body p-0">
                  <table className="admin-table">
                    <thead><tr><th>Código</th><th>Entrada</th><th>Rececionista</th><th>Ações</th></tr></thead>
                    <tbody>
                      {aguardandoTriagem.map(ep => (
                        <tr key={ep.cod_epis}>
                          <td><strong>{ep.cod_epis}</strong></td>
                          <td>{new Date(ep.data_h_entrada).toLocaleString()}</td>
                          <td>{ep.profissional_info?.nome || ep.rececionista_nome}</td>
                          <td className="actions">
                            <button className="btn-icon primary" onClick={() => verPercursoEpisodio(ep.cod_epis)} title="Ver Percurso"><Eye size={16}/></button>
                            <button className="btn-icon danger" onClick={() => handleDelete('episode', ep.cod_epis)}><Trash2 size={16}/></button>
                          </td>
                        </tr>
                      ))}
                      {aguardandoTriagem.length === 0 && <tr><td colSpan="4" className="text-center p-4 text-muted">Nenhum utente aguardando triagem.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* 2. EPISÓDIOS EM ATENDIMENTO */}
              <section className="admin-card">
                <div className="card-header bg-primary-light">
                  <Activity size={18} /> 
                  <h3>Urgências em Curso ({episodiosAtivos.length})</h3>
                </div>
                <div className="table-controls">
                  <Search size={18} />
                  <input type="text" placeholder="Filtrar episódios ativos..." value={filtros.episode} onChange={e => setFiltros({...filtros, episode: e.target.value})} />
                </div>
                <div className="card-body p-0">
                  <table className="admin-table">
                    <thead><tr><th>Código</th><th>Utente</th><th>Entrada</th><th>Ações</th></tr></thead>
                    <tbody>
                      {episodiosAtivos.filter(e => 
                        e.cod_epis.toLowerCase().includes(filtros.episode.toLowerCase()) || 
                        e.id_utente.toString().includes(filtros.episode)
                      ).map(e => (
                        <tr key={e.cod_epis}>
                          <td><strong>{e.cod_epis}</strong></td>
                          <td>ID: {e.id_utente}</td>
                          <td>{new Date(e.data_h_entrada).toLocaleString()}</td>
                          <td className="actions">
                            <button className="btn-icon primary" onClick={() => verPercursoEpisodio(e.cod_epis)} title="Ver Detalhes"><Eye size={16}/></button>
                            <button className="btn-icon danger" onClick={() => handleDelete('episode', e.cod_epis)}><Trash2 size={16}/></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* 3. INTERNAMENTOS ATIVOS */}
              <section className="admin-card">
                <div className="card-header bg-danger-light">
                  <Hotel size={18} /> 
                  <h3>Internamentos Ativos ({internamentos.length})</h3>
                </div>
                <div className="card-body p-0">
                  <table className="admin-table">
                    <thead><tr><th>Cama</th><th>Cód. Episódio</th><th>Utente</th><th>Entrada</th><th>Ações</th></tr></thead>
                    <tbody>
                      {internamentos.map(i => (
                        <tr key={i.num_internamento}>
                          <td><span className="badge-cama">{i.num_cama || '---'}</span></td>
                          <td>{i.cod_epis}</td>
                          <td>{i.utente_nome}</td>
                          <td>{i.medico_responsavel}</td>
                          <td>{new Date(i.data_h_entrada).toLocaleString()}</td>
                          <td className="actions">
                            <button className="btn-icon primary" onClick={() => verPercursoEpisodio(i.cod_epis)} title="Ver Percurso"><Eye size={16}/></button>
                            <button className="btn-icon success" onClick={() => darAltaInternamento(i.num_internamento)} title="Dar Alta"><LogOut size={16}/></button>
                          </td>
                        </tr>
                      ))}
                      {internamentos.length === 0 && <tr><td colSpan="5" className="text-center p-4 text-muted">Nenhum internamento ativo.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'archive' && (
            <div className="admin-card">
              <div className="card-header">
                <Database size={20} />
                <h3>Arquivo Global de Episódios</h3>
              </div>
              <div className="table-controls">
                <Search size={18} />
                <input 
                  type="text" 
                  placeholder="Pesquisar por Código, Nome ou NIF..." 
                  value={filtros.episode} 
                  onChange={e => setFiltros({...filtros, episode: e.target.value})} 
                />
              </div>
                <div className="card-body p-0">
                <table className="admin-table">
                  <thead><tr><th>Código</th><th>Utente (Nome/NIF)</th><th>Entrada</th><th>Saída (Alta)</th><th>Ações</th></tr></thead>
                  <tbody>
                    {episodiosArquivados.filter(e => {
                      const termo = filtros.episode.toLowerCase();
                      const utenteInfo = utentes.find(u => u.num_utente === e.id_utente);
                      const nomeUtente = utenteInfo?.nome?.toLowerCase() || "";
                      
                      return e.cod_epis.toLowerCase().includes(termo) ||
                             e.id_utente.toString().includes(termo) ||
                             nomeUtente.includes(termo);
                    }).map(e => {
                      const utenteInfo = utentes.find(u => u.num_utente === e.id_utente);
                      return (
                        <tr key={e.cod_epis}>
                          <td><strong>{e.cod_epis}</strong></td>
                          <td>
                            <div className="d-flex flex-column">
                              <span>{utenteInfo?.nome || 'Utente s/ Nome'}</span>
                              <small className="text-muted">NIF: {e.id_utente}</small>
                            </div>
                          </td>
                          <td>{new Date(e.data_h_entrada).toLocaleString()}</td>
                          <td>{e.data_h_saida ? new Date(e.data_h_saida).toLocaleString() : '---'}</td>
                          <td className="actions">
                            <button className="btn-icon primary" onClick={() => verPercursoEpisodio(e.cod_epis)} title="Ver Histórico Completo"><FileText size={16}/></button>
                            <button className="btn-icon danger" onClick={() => handleDelete('episode', e.cod_epis)}><Trash2 size={16}/></button>
                          </td>
                        </tr>
                      );
                    })}
                    {episodiosArquivados.length === 0 && <tr><td colSpan="5" className="text-center p-5 text-muted">O arquivo está vazio.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'utentes' && (
            <div className="admin-card">
              <div className="table-controls">
                <Search size={18} />
                <input type="text" placeholder="Filtrar utentes..." value={filtros.utente} onChange={e => setFiltros({...filtros, utente: e.target.value})} />
              </div>
              <table className="admin-table">
                <thead><tr><th>NIF</th><th>Nome</th><th>Email</th><th>Estado</th><th>Ações</th></tr></thead>
                <tbody>
                  {utentes.filter(u => u.nome.toLowerCase().includes(filtros.utente.toLowerCase()) || u.num_utente.toString().includes(filtros.utente)).map(u => (
                    <tr key={u.num_utente}>
                      <td>{u.num_utente}</td>
                      <td>{u.nome}</td>
                      <td>{u.email || <span className="text-danger">Sem E-mail</span>}</td>
                      <td><span className={`status-pill ${u.ativo ? 'active' : 'pending'}`}>{u.ativo ? 'Ativo' : 'Pendente'}</span></td>
                      <td className="actions">
                        <button 
                          className="btn-icon primary" 
                          onClick={() => verHistoricoUtente(u.num_utente)}
                          title="Ver Histórico Clínico"
                        >
                          <History size={16}/>
                        </button>
                        <button 
                          className="btn-icon primary" 
                          onClick={() => setEditingItem({ type: 'utente', data: { ...u } })}
                          title="Editar Utente"
                        >
                          <Edit2 size={16}/>
                        </button>
                        <button 
                          className={`btn-icon ${u.ativo ? 'warning' : 'success'}`} 
                          onClick={() => toggleUtenteStatus(u.num_utente, u.ativo)}
                          title={u.ativo ? 'Suspender Utente' : 'Ativar Utente'}
                        >
                          <ShieldCheck size={16}/>
                        </button>
                        <button 
                          className="btn-icon primary" 
                          onClick={() => {
                            if (!u.email) {
                              setMensagem({ tipo: 'warning', texto: 'Utente sem e-mail. Por favor, atualize os dados primeiro.' });
                              setEditingItem({ type: 'utente', data: { ...u } });
                            } else {
                              resendUtenteActivation(u.num_utente);
                            }
                          }}
                          title="Reenviar PIN e Ativação"
                        >
                          <Mail size={16}/>
                        </button>
                        <button className="btn-icon danger" onClick={() => handleDelete('utente', u.num_utente)}><Trash2 size={16}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="admin-card">
              <div className="table-controls">
                <Search size={18} />
                <input type="text" placeholder="Filtrar utilizadores..." value={filtros.user} onChange={e => setFiltros({...filtros, user: e.target.value})} />
              </div>
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Nome</th><th>Papel</th><th>Estado</th><th>Ações</th></tr></thead>
                <tbody>
                  {utilizadores.filter(u => u.nome_completo.toLowerCase().includes(filtros.user.toLowerCase())).map(u => (
                    <tr key={u.id_utilizador}>
                      <td>{u.id_utilizador}</td>
                      <td>{u.nome_completo}</td>
                      <td>{papeis.find(p => p.id_role === u.id_role)?.nome}</td>
                      <td><span className={`status-pill ${u.ativo ? 'active' : 'pending'}`}>{u.ativo ? 'Ativo' : 'Pendente'}</span></td>
                      <td className="actions">
                        <button 
                          className="btn-icon primary" 
                          onClick={() => setEditingItem({ type: 'user', data: { ...u } })}
                          title="Editar Utilizador"
                        >
                          <Edit2 size={16}/>
                        </button>
                        <button 
                          className={`btn-icon ${u.ativo ? 'warning' : 'success'}`} 
                          onClick={() => toggleUserStatus(u.id_utilizador, u.ativo)}
                          title={u.ativo ? 'Suspender Utilizador' : 'Ativar Utilizador'}
                        >
                          <ShieldCheck size={16}/>
                        </button>
                        <button 
                          className="btn-icon primary" 
                          onClick={() => resendUserActivation(u.id_utilizador)}
                          title="Reenviar E-mail de Ativação"
                        >
                          <Mail size={16}/>
                        </button>
                        <button className="btn-icon danger" onClick={() => handleDelete('user', u.id_utilizador)}><Trash2 size={16}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="system-grid">
              <section className="admin-card">
                <div className="card-header"><Database size={20} /><h3>Configurações Globais</h3></div>
                <div className="card-body">
                  <div className="config-group">
                    <h4>Registar Novo Hospital</h4>
                    <form onSubmit={criarHospital} className="compact-form">
                      <input type="text" value={nomeHosp} onChange={e => setNomeHosp(e.target.value)} placeholder="Nome Hospital" required />
                      <input type="text" value={localHosp} onChange={e => setLocalHosp(e.target.value)} placeholder="Localidade" required />
                      <button type="submit" className="btn-primary">Adicionar</button>
                    </form>
                  </div>
                  <hr />
                  <div className="config-group">
                    <h4>Registar Profissional</h4>
                    <form onSubmit={criarProfissional} className="compact-form-grid">
                      <input type="number" value={profNumFunc} onChange={e => setProfNumFunc(e.target.value)} placeholder="Nº Func" required />
                      <select value={profTipo} onChange={e => setProfTipo(e.target.value)}>
                        <option value="MEDICO">Médico</option>
                        <option value="ENFERMEIRO">Enfermeiro</option>
                        <option value="RECECIONISTA">Rececionista</option>
                      </select>
                      <button type="submit" className="btn-primary wide">Registar</button>
                    </form>
                  </div>
                </div>
              </section>

              <section className="admin-card">
                <div className="card-header"><Shield size={20} /><h3>Criar Conta Utilizador</h3></div>
                <div className="card-body">
                  <form onSubmit={criarUtilizador} className="standard-form">
                    <input type="text" value={nomeCompleto} onChange={e => setNomeCompleto(e.target.value)} placeholder="Nome Completo" required />
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
                    <input type="text" value={nomeUtilizador} onChange={e => setNomeUtilizador(e.target.value)} placeholder="Username" required />
                    <input type="password" value={palavraPasse} onChange={e => setPalavraPasse(e.target.value)} placeholder="Password Inicial" required />
                    <div className="form-row">
                      <input type="number" value={numFunc} onChange={e => {setNumFunc(e.target.value); detectRole(e.target.value);}} placeholder="Vincular Nº Func" />
                      <select value={idRole} onChange={e => setIdRole(e.target.value)} required>
                        <option value="">Papel...</option>
                        {papeis.map(p => <option key={p.id_role} value={p.id_role}>{p.nome}</option>)}
                      </select>
                    </div>
                    <button type="submit" className="btn-primary">Criar Conta</button>
                  </form>
                </div>
              </section>

              <section className="admin-card">
                <div className="card-header"><Users size={20} /><h3>Registar Utente</h3></div>
                <div className="card-body">
                  <form onSubmit={criarUtenteApp} className="standard-form">
                    <input type="text" value={uNome} onChange={e => setUNome(e.target.value)} placeholder="Nome Completo" required />
                    <div className="form-row">
                      <input type="email" value={uEmail} onChange={e => setUEmail(e.target.value)} placeholder="Email (Pode ser partilhado)" required />
                      <input type="number" value={uNum} onChange={e => setUNum(e.target.value)} placeholder="Nº Utente (NIF)" required />
                    </div>
                    <div className="form-row">
                      <input type="text" value={uParentesco} onChange={e => setUParentesco(e.target.value)} placeholder="Grau Parentesco (se email partilhado)" />
                      <select value={uSexo} onChange={e => setUSexo(e.target.value)}>
                        <option value="M">Masculino</option>
                        <option value="F">Feminino</option>
                      </select>
                    </div>
                    <button type="submit" className="btn-primary">Registar Utente</button>
                  </form>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="admin-card">
              <div className="table-controls">
                <Search size={18} />
                <input type="text" placeholder="Filtrar auditoria..." value={filtros.audit} onChange={e => setFiltros({...filtros, audit: e.target.value})} />
              </div>
              <table className="admin-table">
                <thead><tr><th>Data</th><th>Ação</th><th>Alvo / Recurso</th><th>Executado por</th><th>IP</th></tr></thead>
                <tbody>
                  {auditLogs.filter(l => l.acao.includes(filtros.audit.toUpperCase())).map((l, idx) => (
                    <tr key={idx}>
                      <td>{new Date(l.data_hora).toLocaleString()}</td>
                      <td><span className="badge">{l.acao}</span></td>
                      <td>
                        {l.recurso === 'utente' && l.nome_recurso ? (
                          <strong>{l.nome_recurso}</strong>
                        ) : (
                          <span>{l.recurso} {l.id_recurso && `(${l.id_recurso})`}</span>
                        )}
                      </td>
                      <td>{l.nome_utilizador || `ID: ${l.id_utilizador}`}</td>
                      <td>{l.ip_origem}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      <style jsx>{`
        .admin-layout-container { display: flex; min-height: 100vh; background: #f8fafc; }
        .admin-side-nav { width: 260px; background: white; border-right: 1px solid #e2e8f0; padding: 20px 0; }
        .admin-nav-header { padding: 0 20px 20px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f1f5f9; }
        .admin-nav-list { display: flex; flex-direction: column; gap: 4px; padding: 10px; }
        .admin-nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; border: none; background: none; border-radius: 8px; color: #64748b; cursor: pointer; text-align: left; transition: 0.2s; font-weight: 500; }
        .admin-nav-item:hover { background: #f1f5f9; color: #2563eb; }
        .admin-nav-item.active { background: #eff6ff; color: #2563eb; font-weight: 600; }
        .admin-main-content { flex: 1; padding: 30px; overflow-y: auto; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .admin-header-right { display: flex; gap: 15px; }
        .hospital-filter { display: flex; align-items: center; gap: 8px; background: white; padding: 8px 12px; border-radius: 8px; border: 1px solid #e2e8f0; }
        .admin-card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .card-header { padding: 15px 20px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; gap: 10px; }
        .bg-warning-light { background: #fffbeb; color: #92400e; }
        .bg-primary-light { background: #eff6ff; color: #1e40af; }
        .bg-danger-light { background: #fef2f2; color: #991b1b; }
        .card-body { padding: 20px; }
        .flow-container { display: flex; flex-direction: column; gap: 20px; }
        .system-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .table-controls { padding: 15px 20px; display: flex; align-items: center; gap: 15px; border-bottom: 1px solid #f1f5f9; }
        .admin-table { width: 100%; border-collapse: collapse; }
        .admin-table th { background: #f8fafc; padding: 12px 20px; text-align: left; font-size: 0.75rem; color: #64748b; border-bottom: 1px solid #e2e8f0; }
        .admin-table td { padding: 15px 20px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
        .actions { display: flex; gap: 8px; }
        
        .status-pill { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-pill.active { background: #dcfce7; color: #166534; }
        .badge-cama { background: #f1f5f9; padding: 2px 8px; border-radius: 6px; font-weight: bold; color: #475569; }
        .admin-modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
        .admin-modal-content { background: white; border-radius: 16px; width: 550px; max-height: 90vh; overflow-y: auto; padding: 30px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); animation: modalEnter 0.3s ease-out; }
        .admin-modal-content.large { width: 1000px; }
        @keyframes modalEnter { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid #f1f5f9; }
        .modal-header h3 { margin: 0; font-size: 1.25rem; color: #1e293b; }
        .close-btn { width: 36px; height: 36px; border-radius: 50%; border: none; background: #f8fafc; color: #64748b; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
        .close-btn:hover { background: #fee2e2; color: #ef4444; transform: rotate(90deg); }
        
        .journey-body { padding-top: 10px; }
        .journey-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
        .timeline { padding-left: 20px; border-left: 2px solid #e2e8f0; margin-left: 10px; }
        .timeline-item { margin-bottom: 25px; position: relative; padding-left: 20px; }
        .timeline-icon { position: absolute; left: -29px; width: 16px; height: 16px; background: white; border: 2px solid #2563eb; border-radius: 50%; }
        .priority-tag { font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
        .priority-tag.vermelho { background: #dc3545; color: white; }
        .priority-tag.laranja { background: #fd7e14; color: white; }

        /* Estilos Histórico Completo Utente */
        .admin-history-list { display: flex; flex-direction: column; gap: 20px; }
        .history-episode-card { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: white; }
        .history-episode-header { background: #f8fafc; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; }
        .badge-episodio { background: #2563eb; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
        .date-episodio { color: #64748b; font-size: 0.85rem; font-weight: 500; }
        .status-tag { padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
        .status-tag.open { background: #dcfce7; color: #166534; }
        .status-tag.closed { background: #f1f5f9; color: #475569; }

        .timeline-unified { padding: 20px; position: relative; }
        .timeline-step { display: flex; gap: 20px; margin-bottom: 20px; position: relative; }
        .timeline-step:last-child { margin-bottom: 0; }
        .timeline-step::before { content: ""; position: absolute; left: 7px; top: 20px; bottom: -20px; width: 2px; background: #f1f5f9; }
        .timeline-step:last-child::before { display: none; }
        
        .timeline-marker { width: 16px; height: 16px; border-radius: 50%; background: white; border: 3px solid #cbd5e1; z-index: 1; flex-shrink: 0; margin-top: 4px; }
        .timeline-marker.red { border-color: #ef4444; }
        
        .timeline-info { flex: 1; }
        .badge-type { font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        .badge-type.triagem { background: #e0f2fe; color: #0369a1; }
        .badge-type.ato { background: #f1f5f9; color: #475569; }
        .badge-type.presc { background: #fef3c7; color: #92400e; }
        .badge-type.intern { background: #fee2e2; color: #991b1b; }
        
        .time-marker { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }
        .step-details { background: #fcfcfd; border-radius: 8px; padding: 10px; margin-top: 5px; border: 1px solid #f1f5f9; }
        .step-details p { margin: 2px 0; font-size: 0.85rem; color: #1e293b; }
        .priority-mini { font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
        .priority-mini.vermelho { color: #dc3545; }
        .priority-mini.laranja { color: #fd7e14; }
        .priority-mini.amarelo { color: #d97706; }
        .priority-mini.verde { color: #16a34a; }
        .priority-mini.azul { color: #2563eb; }

        .btn-simulate {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #2563eb;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .btn-simulate:hover {
          background: #1d4ed8;
          transform: translateY(-1px);
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .btn-simulate:active {
          transform: translateY(0);
        }
      `}</style>
    </div>
  );
};

export default Admin;