import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  UserCog, Users, PlusCircle, Shield, Activity, Save, 
  Trash2, Edit2, Search, Hotel, Clipboard, X, Mail, User
} from 'lucide-react';

const Admin = () => {
  const [activeTab, setActiveTab] = useState('system');
  const [papeis, setPapeis] = useState([]);
  const [hospitais, setHospitais] = useState([]);
  const [utilizadores, setUtilizadores] = useState([]);
  const [utentes, setUtentes] = useState([]);
  const [episodios, setEpisodios] = useState([]);
  
  // Estados para Criação de Utilizador
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
  const [profSexo, setProfSexo] = useState('M');
  const [profTipo, setProfTipo] = useState('MEDICO');
  const [profEstagiario, setProfEstagiario] = useState('NÃO');
  
  // Estados para Registro de Utente (App Mobile)
  const [uNome, setUNome] = useState('');
  const [uEmail, setUEmail] = useState('');
  const [uNum, setUNum] = useState('');
  const [uTel, setUTel] = useState('');
  const [uMorada, setUMorada] = useState('');
  const [uLocalidade, setULocalidade] = useState('');
  const [uSexo, setUSexo] = useState('M');
  const [uDataNasc, setUDataNasc] = useState('');
  
  // Estados para Edição
  const [editingItem, setEditingItem] = useState(null);
  
  const [mensagem, setMensagem] = useState({ tipo: '', texto: '' });

  // Filtros
  const [filtros, setFiltros] = useState({ user: '', userType: '', utente: '', episode: '', hospital: '' });

  const fetchData = async () => {
    // Carregar papéis e hospitais primeiro pois são usados para lookup
    try {
      const resPapeis = await axios.get('/auth/roles');
      setPapeis(resPapeis.data);
    } catch (err) { console.error('Erro ao carregar papéis', err); }

    try {
      const resHospitais = await axios.get('/clinical/hospitals');
      setHospitais(resHospitais.data);
    } catch (err) { console.error('Erro ao carregar hospitais', err); }

    // Carregar utilizadores
    try {
      const resUsers = await axios.get('/auth/users');
      setUtilizadores(resUsers.data || []);
      console.log('Utilizadores carregados:', resUsers.data?.length);
    } catch (err) { 
      console.error('Erro ao carregar utilizadores:', err.response?.status, err.response?.data);
      setUtilizadores([]); // Garantir que fica vazio em caso de erro
    }

    // Carregar utentes
    try {
      const resUtentes = await axios.get('/clinical/utentes');
      setUtentes(resUtentes.data || []);
      console.log('Utentes carregados:', resUtentes.data?.length);
    } catch (err) { 
      console.error('Erro ao carregar utentes:', err); 
      setUtentes([]);
    }

    // Carregar episódios
    try {
      const resEpisodios = await axios.get('/clinical/episodes');
      setEpisodios(resEpisodios.data || []);
    } catch (err) { console.error('Erro ao carregar episódios', err); }
  };

  useEffect(() => {
    fetchData();
  }, []);

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
      setMensagem({ tipo: 'success', texto: `Utilizador ${nomeUtilizador} criado! Verifique o log do backend pelo código de ativação.` });
      setNomeUtilizador(''); setNomeCompleto(''); setEmail(''); setPalavraPasse(''); setIdRole(''); setNumFunc(''); setIsAutoRole(false);
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao criar utilizador. Verifique se o e-mail ou username já existem.' });
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
    try {
      await axios.post('/clinical/utentes', {
        num_utente: parseInt(uNum),
        nome: uNome,
        email: uEmail,
        telemovel: uTel,
        morada: uMorada,
        localidade: uLocalidade,
        sexo: uSexo,
        data_nascimento: uDataNasc
      });
      setMensagem({ tipo: 'success', texto: `Utente ${uNome} registado! PIN e código enviados para ${uEmail}.` });
      setUNome(''); setUEmail(''); setUNum(''); setUTel('');
      setUMorada(''); setULocalidade(''); setUSexo('M'); setUDataNasc('');
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: erro.response?.data?.detail || 'Erro ao registar utente para a App.' });
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
      }

      await axios.patch(url, payload);
      setMensagem({ tipo: 'success', texto: 'Registo atualizado com sucesso!' });
      setEditingItem(null);
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: 'Erro ao atualizar registo.' });
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
      setMensagem({ tipo: 'error', texto: 'Erro ao eliminar registo. Verifique dependências.' });
    }
  };

  const toggleUserStatus = async (userId) => {
    try {
      await axios.post(`/auth/users/${userId}/toggle-status`);
      fetchData();
    } catch (erro) {
      setMensagem({ tipo: 'error', texto: 'Erro ao alterar estado.' });
    }
  };

  return (
    <div className="admin-page">
      <header className="page-header">
        <h1 className="page-title">Gestão Avançada do Sistema</h1>
        <div className="admin-tabs">
          <button className={`tab-btn ${activeTab === 'system' ? 'active' : ''}`} onClick={() => setActiveTab('system')}>Configuração</button>
          <button className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>Utilizadores</button>
          <button className={`tab-btn ${activeTab === 'utentes' ? 'active' : ''}`} onClick={() => setActiveTab('utentes')}>Utentes</button>
          <button className={`tab-btn ${activeTab === 'episodes' ? 'active' : ''}`} onClick={() => setActiveTab('episodes')}>Episódios</button>
          <button className={`tab-btn ${activeTab === 'hospitals' ? 'active' : ''}`} onClick={() => setActiveTab('hospitals')}>Hospitais</button>
        </div>
      </header>

      <div className="hospital-selection-bar">
        <div className="selection-inner">
          <span className="selection-label">Gestão Hospitalar:</span>
          <select 
            className="form-select" 
            value={filtros.hospital}
            onChange={(e) => setFiltros({...filtros, hospital: e.target.value})}
          >
            <option value="">Visão Global (Todos os Hospitais)</option>
            {hospitais.map(h => <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>)}
          </select>
        </div>
      </div>
      
      {mensagem.texto && (
        <div className={`alert alert-${mensagem.tipo}`}>
          <span>{mensagem.texto}</span>
          <X size={18} className="close-msg" onClick={() => setMensagem({ ...mensagem, texto: '' })} />
        </div>
      )}

      {/* MODAL DE EDIÇÃO */}
      {editingItem && (
        <div className="edit-overlay">
          <div className="card edit-card">
            <div className="edit-header">
              <h3>Editar {editingItem.type.charAt(0).toUpperCase() + editingItem.type.slice(1)}</h3>
              <button className="btn-close" onClick={() => setEditingItem(null)}><X size={20}/></button>
            </div>
            <form onSubmit={handleUpdate} className="admin-form">
              {editingItem.type === 'user' && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label>ID (Chave):</label>
                      <input type="text" value={editingItem.data.id_utilizador} readOnly style={{ background: '#f5f5f5' }} />
                    </div>
                    <div className="form-group">
                      <label>Login (Username):</label>
                      <input type="text" value={editingItem.data.nome_utilizador} readOnly style={{ background: '#f5f5f5' }} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Nome Completo:</label>
                    <input type="text" value={editingItem.data.nome_completo} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, nome_completo: e.target.value}})} />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>E-mail:</label>
                      <input type="email" value={editingItem.data.email} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, email: e.target.value}})} />
                    </div>
                    <div className="form-group">
                      <label>Telemóvel:</label>
                      <input type="text" value={editingItem.data.telemovel || ''} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, telemovel: e.target.value}})} placeholder="Opcional" />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Papel (Cargo):</label>
                      <select value={editingItem.data.id_role} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, id_role: parseInt(e.target.value)}})}>
                        {papeis.map(p => <option key={p.id_role} value={p.id_role}>{p.nome}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Nova Password:</label>
                      <input type="password" placeholder="Deixe vazio para manter" onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, palavra_passe: e.target.value}})} />
                    </div>
                  </div>
                  <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
                    <input type="checkbox" checked={editingItem.data.ativo} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, ativo: e.target.checked}})} />
                    <label style={{ margin: 0 }}>Conta Ativa / Validada</label>
                  </div>
                </>
              )}
              {editingItem.type === 'utente' && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Nº Utente:</label>
                      <input type="text" value={editingItem.data.num_utente} readOnly style={{ background: '#f5f5f5' }} />
                    </div>
                    <div className="form-group">
                      <label>Nome Completo:</label>
                      <input type="text" value={editingItem.data.nome} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, nome: e.target.value}})} />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>E-mail (App Mobile):</label>
                      <input type="email" value={editingItem.data.email || ''} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, email: e.target.value}})} />
                    </div>
                    <div className="form-group">
                      <label>Telemóvel:</label>
                      <input type="text" value={editingItem.data.telemovel || ''} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, telemovel: e.target.value}})} />
                    </div>
                  </div>
                  <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
                    <input type="checkbox" checked={editingItem.data.ativo} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, ativo: e.target.checked}})} />
                    <label style={{ margin: 0 }}>Conta Ativa</label>
                  </div>
                </>
              )}
              {editingItem.type === 'hospital' && (
                <>
                  <div className="form-group">
                    <label>Nome do Hospital:</label>
                    <input type="text" value={editingItem.data.nome_hosp} readOnly style={{ background: '#f5f5f5' }} />
                  </div>
                  <div className="form-group">
                    <label>Localidade:</label>
                    <input type="text" value={editingItem.data.local_hosp} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, local_hosp: e.target.value}})} />
                  </div>
                </>
              )}
              {editingItem.type === 'episode' && (
                <>
                  <div className="form-group">
                    <label>Código Episódio:</label>
                    <input type="text" value={editingItem.data.cod_epis} readOnly style={{ background: '#f5f5f5' }} />
                  </div>
                  <div className="form-group">
                    <label>Sintomas/Observações:</label>
                    <textarea value={editingItem.data.sintomas || ''} onChange={e => setEditingItem({...editingItem, data: {...editingItem.data, sintomas: e.target.value}})} />
                  </div>
                </>
              )}

              <div className="form-actions" style={{ marginTop: '2rem', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setEditingItem(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary"><Save size={18}/> Salvar Alterações</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="tab-content">
        {activeTab === 'system' && (
          <div className="admin-grid-layout">
            <div className="admin-column">
              {/* REGISTAR PROFISSIONAL */}
              <section className="card admin-section">
                <div className="section-header-icon">
                  <Activity className="icon-blue" />
                  <h3>Registar Profissional</h3>
                </div>
                <form onSubmit={criarProfissional} className="admin-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label>Nº Funcionário:</label>
                      <input type="number" value={profNumFunc} onChange={(e) => setProfNumFunc(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Sexo:</label>
                      <select value={profSexo} onChange={(e) => setProfSexo(e.target.value)}>
                        <option value="Masculino">Masculino</option>
                        <option value="Feminino">Feminino</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Tipo:</label>
                      <select value={profTipo} onChange={(e) => setProfTipo(e.target.value)}>
                        <option value="MEDICO">Médico</option>
                        <option value="ENFERMEIRO">Enfermeiro</option>
                        <option value="RECECIONISTA">Rececionista</option>
                        <option value="ADMIN">Administrador</option>
                      </select>
                    </div>
                    {profTipo === 'MEDICO' && (
                      <div className="form-group">
                        <label>Estagiário?</label>
                        <select value={profEstagiario} onChange={(e) => setProfEstagiario(e.target.value)}>
                          <option value="SIM">Sim</option>
                          <option value="NÃO">Não</option>
                        </select>
                      </div>
                    )}
                  </div>
                  <button type="submit" className="btn btn-primary"><PlusCircle size={18}/> Registar Profissional</button>
                </form>
              </section>

              {/* CRIAR CONTA DE UTILIZADOR */}
              <section className="card admin-section" id="form-utilizador">
                <div className="section-header-icon">
                  <Shield className="icon-purple" />
                  <h3>Criar Conta de Utilizador</h3>
                </div>
                <form onSubmit={criarUtilizador} className="admin-form">
                  <div className="form-group">
                    <label>Nome Completo:</label>
                    <div style={{ position: 'relative' }}>
                      <User size={16} className="input-icon" />
                      <input type="text" className="with-icon" value={nomeCompleto} onChange={(e) => setNomeCompleto(e.target.value)} required placeholder="Ex: José Carlos Santos" />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>E-mail:</label>
                      <div style={{ position: 'relative' }}>
                        <Mail size={16} className="input-icon" />
                        <input type="email" className="with-icon" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="exemplo@hospital.com" />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Telemóvel:</label>
                      <input type="text" value={telemovel} onChange={(e) => setTelemovel(e.target.value)} placeholder="912345678 (Opcional)" />
                    </div>
                    <div className="form-group">
                      <label>Username:</label>
                      <input type="text" value={nomeUtilizador} onChange={(e) => setNomeUtilizador(e.target.value)} required placeholder="jose.santos" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Palavra-passe Inicial:</label>
                    <input type="password" value={palavraPasse} onChange={(e) => setPalavraPasse(e.target.value)} required placeholder="Mínimo 12 caracteres..." />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Papel (Cargo):</label>
                      <select value={idRole} onChange={(e) => {setIdRole(e.target.value); setIsAutoRole(false);}} required className={isAutoRole ? 'auto-detected' : ''}>
                        <option value="">Selecione...</option>
                        {papeis.map(p => <option key={p.id_role} value={p.id_role}>{p.nome}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Nº Funcionário:</label>
                      <input type="number" value={numFunc} onChange={(e) => {setNumFunc(e.target.value); detectRole(e.target.value);}} placeholder="Para vincular..." />
                    </div>
                  </div>
                  <button type="submit" className="btn btn-primary"><PlusCircle size={18}/> Criar Conta e Enviar Código</button>
                </form>
              </section>
            </div>

            <div className="admin-column">
              {/* REGISTAR UTENTE (APP MOBILE) */}
              <section className="card admin-section">
                <div className="section-header-icon">
                  <Users className="icon-blue" />
                  <h3>Registar Utente (App Mobile)</h3>
                </div>
                <form onSubmit={criarUtenteApp} className="admin-form">
                  <div className="form-group">
                    <label>Nome Completo:</label>
                    <input type="text" value={uNome} onChange={(e) => setUNome(e.target.value)} required placeholder="Ex: Maria Silva" />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>E-mail:</label>
                      <input type="email" value={uEmail} onChange={(e) => setUEmail(e.target.value)} required placeholder="maria@email.com" />
                    </div>
                    <div className="form-group">
                      <label>Nº Utente:</label>
                      <input type="number" value={uNum} onChange={(e) => setUNum(e.target.value)} required placeholder="123456789" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Telemóvel:</label>
                    <input type="text" value={uTel} onChange={(e) => setUTel(e.target.value)} placeholder="912345678" />
                  </div>
                  <div className="form-group">
                    <label>Morada Completa:</label>
                    <input type="text" value={uMorada} onChange={(e) => setUMorada(e.target.value)} placeholder="Rua, Nº, Andar..." />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Localidade:</label>
                      <input type="text" value={uLocalidade} onChange={(e) => setULocalidade(e.target.value)} placeholder="Cidade/Vila" />
                    </div>
                    <div className="form-group">
                      <label>Sexo:</label>
                      <select value={uSexo} onChange={(e) => setUSexo(e.target.value)}>
                        <option value="M">Masculino</option>
                        <option value="F">Feminino</option>
                        <option value="O">Outro</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Data Nascimento:</label>
                      <input type="date" value={uDataNasc} onChange={(e) => setUDataNasc(e.target.value)} />
                    </div>
                  </div>
                  <button type="submit" className="btn btn-primary"><PlusCircle size={18}/> Registar e Enviar PIN</button>
                </form>
              </section>

              {/* REGISTAR HOSPITAL */}
              <section className="card admin-section">
                <div className="section-header-icon">
                  <Hotel className="icon-green" />
                  <h3>Registar Hospital</h3>
                </div>
                <form onSubmit={criarHospital} className="admin-form">
                  <div className="form-group">
                    <label>Nome do Hospital:</label>
                    <input type="text" value={nomeHosp} onChange={(e) => setNomeHosp(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Localidade:</label>
                    <input type="text" value={localHosp} onChange={(e) => setLocalHosp(e.target.value)} required />
                  </div>
                  <button type="submit" className="btn btn-primary"><Save size={18}/> Registar Hospital</button>
                </form>
              </section>
            </div>
          </div>
        )}

        {/* LISTAGEM DE UTILIZADORES */}
        {activeTab === 'users' && (
          <section className="card">
            <div className="table-controls">
              <div className="search-box">
                <Search size={18} />
                <input 
                  type="text" 
                  placeholder="Pesquisar por ID, Nome ou Login..." 
                  value={filtros.user} 
                  onChange={e => setFiltros({...filtros, user: e.target.value})} 
                />
              </div>
              <div className="filter-box">
                <select 
                  value={filtros.userType} 
                  onChange={e => setFiltros({...filtros, userType: e.target.value})}
                  className="tab-btn"
                  style={{ height: 'auto', padding: '8px 15px' }}
                >
                  <option value="">Todos os Tipos</option>
                  {papeis.map(p => (
                    <option key={p.id_role} value={p.id_role}>{p.nome}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Nome Completo</th>
                    <th>Login</th>
                    <th>Papel</th>
                    <th>Estado</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {utilizadores.filter(u => {
                    const searchStr = (filtros.user || '').toLowerCase();
                    const nomeComp = (u.nome_completo || '').toLowerCase();
                    const nomeUtil = (u.nome_utilizador || '').toLowerCase();
                    const idUtil = String(u.id_utilizador || '');

                    const matchSearch = 
                      idUtil.includes(searchStr) ||
                      nomeUtil.includes(searchStr) || 
                      nomeComp.includes(searchStr);
                    
                    const matchType = filtros.userType === '' || u.id_role === parseInt(filtros.userType);
                    
                    return matchSearch && matchType;
                  }).length > 0 ? (
                    utilizadores.filter(u => {
                      const searchStr = (filtros.user || '').toLowerCase();
                      const matchSearch = 
                        String(u.id_utilizador || '').includes(searchStr) ||
                        (u.nome_utilizador || '').toLowerCase().includes(searchStr) || 
                        (u.nome_completo || '').toLowerCase().includes(searchStr);
                      const matchType = filtros.userType === '' || u.id_role === parseInt(filtros.userType);
                      return matchSearch && matchType;
                    }).map(u => (
                      <tr key={u.id_utilizador}>
                        <td>{u.id_utilizador}</td>
                        <td>{u.nome_completo}</td>
                        <td>{u.nome_utilizador}</td>
                        <td>
                          <span className="badge-role">
                            {papeis.find(p => p.id_role === u.id_role)?.nome || 'N/A'}
                          </span>
                        </td>
                        <td><span className={`status-pill ${u.ativo ? 'active' : 'inactive'}`}>{u.ativo ? 'Ativo' : 'Pendente'}</span></td>
                        <td className="actions-cell">
                          <button className="btn-icon" title="Editar" onClick={() => setEditingItem({type: 'user', data: {...u}})}><Edit2 size={16}/></button>
                          <button 
                            className={`btn-icon ${u.ativo ? 'btn-warn' : 'btn-ok'}`} 
                            title={u.ativo ? "Desativar" : "Ativar"}
                            onClick={() => toggleUserStatus(u.id_utilizador)}
                          >
                            <Activity size={16}/>
                          </button>
                          <button className="btn-icon btn-del" title="Eliminar" onClick={() => handleDelete('user', u.id_utilizador)}><Trash2 size={16}/></button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        Nenhum utilizador encontrado.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* LISTAGEM DE UTENTES */}
        {activeTab === 'utentes' && (
          <section className="card">
            <div className="table-controls">
              <div className="search-box">
                <Search size={18} />
                <input 
                  type="text" 
                  placeholder="Pesquisar por nome, Nº utente ou telemóvel..." 
                  value={filtros.utente} 
                  onChange={e => setFiltros({...filtros, utente: e.target.value})} 
                />
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Nº Utente</th>
                    <th>Nome</th>
                    <th>Telemóvel</th>
                    <th>Localidade</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {utentes.filter(u => {
                    const searchStr = filtros.utente.toLowerCase();
                    const numUtenteStr = String(u.num_utente);
                    return u.nome.toLowerCase().includes(searchStr) || 
                           numUtenteStr.includes(searchStr) ||
                           (u.telemovel && u.telemovel.includes(searchStr));
                  }).map(u => (
                    <tr key={u.num_utente}>
                      <td>{u.num_utente}</td>
                      <td>{u.nome}</td>
                      <td>{u.telemovel || 'N/A'}</td>
                      <td>{u.localidade || 'N/A'}</td>
                      <td className="actions-cell">
                        <button className="btn-icon" onClick={() => setEditingItem({type: 'utente', data: {...u}})}><Edit2 size={16}/></button>
                        <button className="btn-icon btn-del" onClick={() => handleDelete('utente', u.num_utente)}><Trash2 size={16}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* LISTAGEM DE EPISÓDIOS */}
        {activeTab === 'episodes' && (
          <section className="card">
            <div className="table-controls">
              <div className="search-box">
                <Search size={18} />
                <input 
                  type="text" 
                  placeholder="Pesquisar por Código, ID Utente ou Sintomas..." 
                  value={filtros.episode} 
                  onChange={e => setFiltros({...filtros, episode: e.target.value})} 
                />
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>ID Utente</th>
                    <th>Entrada</th>
                    <th>Estado</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {episodios.filter(e => 
                    e.cod_epis.toLowerCase().includes(filtros.episode.toLowerCase()) || 
                    e.id_utente.toString().includes(filtros.episode) ||
                    (e.sintomas && e.sintomas.toLowerCase().includes(filtros.episode.toLowerCase()))
                  ).map(e => (
                    <tr key={e.cod_epis}>
                      <td>{e.cod_epis}</td>
                      <td>{e.id_utente}</td>
                      <td>{new Date(e.data_h_entrada).toLocaleString()}</td>
                      <td>
                        <span className={`status-pill ${e.data_h_saida ? 'inactive' : 'active'}`}>
                          {e.data_h_saida ? 'Encerrado' : 'Em Aberto'}
                        </span>
                      </td>
                      <td className="actions-cell">
                        <button className="btn-icon" onClick={() => setEditingItem({type: 'episode', data: {...e}})}><Edit2 size={16}/></button>
                        <button className="btn-icon btn-del" onClick={() => handleDelete('episode', e.cod_epis)}><Trash2 size={16}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* LISTAGEM DE HOSPITAIS */}
        {activeTab === 'hospitals' && (
          <section className="card">
            <div className="table-controls">
              <div className="search-box">
                <Search size={18} />
                <input 
                  type="text" 
                  placeholder="Pesquisar hospital..." 
                  value={filtros.hospital} 
                  onChange={e => setFiltros({...filtros, hospital: e.target.value})} 
                />
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Localidade</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {hospitais.filter(h => 
                    h.nome_hosp.toLowerCase().includes(filtros.hospital.toLowerCase()) || 
                    h.local_hosp.toLowerCase().includes(filtros.hospital.toLowerCase())
                  ).map(h => (
                    <tr key={h.nome_hosp}>
                      <td>{h.nome_hosp}</td>
                      <td>{h.local_hosp}</td>
                      <td className="actions-cell">
                        <button className="btn-icon" onClick={() => setEditingItem({type: 'hospital', data: {...h}})}><Edit2 size={16}/></button>
                        <button className="btn-icon btn-del" onClick={() => handleDelete('hospital', h.nome_hosp)}><Trash2 size={16}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>

      <style jsx>{`
        .admin-tabs { display: flex; gap: 10px; margin-top: 1rem; }
        .tab-btn { padding: 10px 20px; border-radius: 8px; border: 1px solid var(--border); background: white; cursor: pointer; font-weight: 600; color: var(--text-muted); transition: all 0.2s; }
        .tab-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
        .admin-grid-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .section-header-icon { display: flex; align-items: center; gap: 12px; margin-bottom: 15px; }
        .auto-detected { border-color: var(--primary) !important; background-color: #f0f9ff !important; font-weight: bold; }
        .input-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
        .with-icon { padding-left: 40px !important; }
        .actions-cell { display: flex; gap: 8px; }
        .btn-icon { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; border: 1px solid var(--border); background: white; cursor: pointer; color: var(--text-muted); }
        .status-pill { padding: 4px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }
        .status-pill.active { background: #dcfce7; color: #166534; }
        .status-pill.inactive { background: #fef9c3; color: #854d0e; }
      `}</style>
    </div>
  );
};

export default Admin;
