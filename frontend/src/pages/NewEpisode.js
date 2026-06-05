import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { Search, UserPlus, AlertCircle, CheckCircle, X } from 'lucide-react';

const NewEpisode = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  
  // Estados para o Episódio
  const [formData, setFormData] = useState({
    data_h_entrada: new Date().toISOString().slice(0, 16),
    id_utente: '',
    id_hospital: utilizador?.hospital || '',
    sintomas: '',
    observacoes: ''
  });

  // Estados para Pesquisa
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedUtente, setSelectedUtente] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);

  // Efeito para Pesquisa Dinâmica (Live Search)
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.trim().length >= 3 && !selectedUtente) {
        performSearch();
      } else if (searchQuery.trim().length < 3) {
        setSearchResults([]);
        setShowDropdown(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, selectedUtente]);

  const performSearch = async () => {
    setIsSearching(true);
    try {
      const isNumeric = /^\d+$/.test(searchQuery);
      let params = {};
      if (isNumeric) {
        params = searchQuery.length > 5 ? { num_utente: searchQuery } : { telemovel: searchQuery };
      } else {
        params = { nome: searchQuery };
      }
      
      const res = await axios.get('/clinical/utentes/search', { params });
      setSearchResults(res.data);
      setShowDropdown(true);
    } catch (error) {
      console.error('Erro na pesquisa', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Estados para Novo Utente
  const [showUtenteForm, setShowUtenteForm] = useState(false);
  const [emailInUse, setEmailInUse] = useState(false);
  const [newUtente, setNewUtente] = useState({
    num_utente: '',
    nome: '',
    email: '',
    telemovel: '',
    morada: '',
    data_nascimento: '',
    sexo: 'M',
    localidade: '',
    parentesco: ''
  });

  const parentescoOptions = ["Próprio/Titular", "Pai/Mãe", "Filho/a", "Cônjuge", "Irmão/ã", "Outro"];
  const [customParentesco, setCustomParentesco] = useState('');

  // Verificar se email existe ao digitar
  useEffect(() => {
    const checkEmail = async () => {
      if (newUtente.email.includes('@') && newUtente.email.length > 5) {
        try {
          const res = await axios.get('/clinical/utentes');
          const exists = res.data.some(u => u.email === newUtente.email.toLowerCase().trim());
          setEmailInUse(exists);
        } catch (e) { console.error(e); }
      }
    };
    const timer = setTimeout(checkEmail, 1000);
    return () => clearTimeout(timer);
  }, [newUtente.email]);

  const [message, setMessage] = useState(null);

  // Auto-close das mensagens após 30 segundos
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // Limpar mensagens ao mudar de contexto no formulário (exceto se for sucesso)
  useEffect(() => {
    if (message && message.type !== 'success') {
      setMessage(null);
    }
  }, [showUtenteForm, selectedUtente]);

  // Sincronizar hospital com a sessão
  useEffect(() => {
    if (utilizador?.hospital) {
      setFormData(prev => ({ ...prev, id_hospital: utilizador.hospital }));
    }
  }, [utilizador?.hospital]);

  // Carregar Hospitais
  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const res = await axios.get('/clinical/hospitals');
        setHospitals(res.data);
        // Pré-selecionar o primeiro hospital se disponível e nenhum selecionado
        if (res.data.length > 0 && !formData.id_hospital) {
          setFormData(prev => ({ ...prev, id_hospital: res.data[0].nome_hosp }));
        }
      } catch (error) {
        console.error('Erro ao carregar hospitais', error);
      }
    };
    fetchHospitals();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery) return;

    setIsSearching(true);
    setMessage(null);
    setSearchResults([]);
    setSelectedUtente(null);
    setShowUtenteForm(false);

    try {
      // Tentar pesquisar por número ou telefone
      // O backend aceita num_utente ou telemovel como query params
      const isNumeric = /^\d+$/.test(searchQuery);
      const params = isNumeric ? { num_utente: searchQuery } : { telemovel: searchQuery };
      
      const res = await axios.get('/clinical/utentes/search', { params });
      setSearchResults(res.data);
      
      if (res.data.length === 0) {
        setMessage({ type: 'info', text: 'Utente não encontrado. Deseja registar um novo?' });
      }
    } catch (error) {
      console.error('Erro na pesquisa', error);
      setMessage({ type: 'error', text: 'Erro ao pesquisar utente.' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectUtente = (utente) => {
    setSelectedUtente(utente);
    setFormData(prev => ({ ...prev, id_utente: utente.num_utente }));
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleCreateUtente = async (e) => {
    e.preventDefault();
    setMessage(null);

    // Validação local antes do envio
    if (!newUtente.num_utente || !newUtente.nome || !newUtente.email) {
      setMessage({ type: 'error', text: 'Nº Utente (SNS), Nome Completo e E-mail são obrigatórios.' });
      return;
    }

    // Validar parentesco se o email estiver em uso
    const parentescoFinal = newUtente.parentesco === 'Outro' ? customParentesco : newUtente.parentesco;
    if (emailInUse && !parentescoFinal) {
      setMessage({ type: 'error', text: 'O e-mail indicado já pertence a outro utente. Por favor, indique o grau de parentesco.' });
      return;
    }

    try {
      const payload = {
        num_utente: parseInt(newUtente.num_utente),
        nome: newUtente.nome,
        email: newUtente.email.toLowerCase().trim(),
        telemovel: newUtente.telemovel || null,
        morada: newUtente.morada || null,
        localidade: newUtente.localidade || null,
        sexo: newUtente.sexo || "M",
        data_nascimento: newUtente.data_nascimento || null,
        parentesco: parentescoFinal || null
      };

      const res = await axios.post('/clinical/utentes', payload);
      setMessage({ type: 'success', text: `Utente ${newUtente.nome} registado! PIN enviado para o e-mail.` });
      
      // O backend devolve { success: true, data: { ...utente... } }
      const utenteCriado = res.data.data;
      setSelectedUtente(utenteCriado);
      setFormData(prev => ({ ...prev, id_utente: utenteCriado.num_utente }));
      
      setShowUtenteForm(false);
      setEmailInUse(false);
    } catch (error) {
      console.error('Erro detalhado:', error.response?.data);
      const detail = error.response?.data?.detail;
      let msg = 'Erro ao registar utente.';
      if (typeof detail === 'string') msg = detail;
      else if (Array.isArray(detail)) msg = `Campo obrigatório em falta: ${detail[0]?.loc[1]}`;
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleSubmitEpisode = async (e) => {
    e.preventDefault();
    setMessage(null);
    if (!selectedUtente) {
      setMessage({ type: 'error', text: 'Por favor, selecione ou registe um utente primeiro.' });
      return;
    }

    try {
      const res = await axios.post('/clinical/episodes', {
        ...formData,
        id_utente: parseInt(formData.id_utente)
      });
      setMessage({ type: 'success', text: `Episódio ${res.data.cod_epis} registado com sucesso!` });
      // Reset form
      setFormData({
        data_h_entrada: new Date().toISOString().slice(0, 16),
        id_utente: '',
        id_hospital: utilizador?.hospital || '',
        sintomas: '',
        observacoes: ''
      });
      setSelectedUtente(null);
    } catch (error) {
      const detail = error.response?.data?.detail;
      const msgText = typeof detail === 'string' ? detail : 'Erro ao registar episódio.';
      setMessage({ type: 'error', text: msgText });
    }
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div className="header-title">
          <AlertCircle size={24} className="icon-warning" />
          <h2>Admissão de Urgência</h2>
        </div>
        <button className="secondary-button" onClick={() => navigate('/dashboard')}>Voltar</button>
      </header>

      {message && (
        <div className={`alert alert-${message.type}`} style={{ position: 'relative' }}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span style={{ marginRight: '25px' }}>{message.text}</span>
          {message.type === 'info' && !showUtenteForm && (
            <button className="text-button" onClick={() => {
              setShowUtenteForm(true);
              setNewUtente({...newUtente, num_utente: /^\d+$/.test(searchQuery) ? searchQuery : ''});
            }}>
              Registar Novo Utente
            </button>
          )}
          <X 
            size={18} 
            style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', cursor: 'pointer', opacity: 0.7 }} 
            onClick={() => setMessage(null)} 
          />
        </div>
      )}

      <div className="admission-grid">
        {/* COLUNA 1: IDENTIFICAÇÃO */}
        <div className="column">
          <section className="form-section">
            <div className="section-header">
              <h3>1. Identificação do Utente</h3>
            </div>

            {!selectedUtente && !showUtenteForm && (
              <div className="search-container" style={{ position: 'relative' }}>
                <form onSubmit={handleSearch} className="search-box">
                  <div className="search-input-wrapper" style={{ flex: 1, position: 'relative' }}>
                    <Search size={18} className="search-icon-inner" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#a0aec0' }} />
                    <input 
                      type="text" 
                      placeholder="Pesquisar por NIF, Telemóvel ou Nome..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="search-input"
                      style={{ paddingLeft: '40px', width: '100%' }}
                    />
                  </div>
                  <button type="submit" className="search-button" disabled={isSearching}>
                    {isSearching ? '...' : 'Pesquisar'}
                  </button>
                </form>

                {/* Dropdown de Resultados Dinâmicos */}
                {showDropdown && searchResults.length > 0 && (
                  <div className="search-dropdown" style={{
                    position: 'absolute', top: '100%', left: 0, right: 0, 
                    background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', zIndex: 100,
                    marginTop: '5px', maxHeight: '300px', overflowY: 'auto'
                  }}>
                    {searchResults.map(u => (
                      <div 
                        key={u.num_utente} 
                        className="dropdown-item" 
                        onClick={() => { handleSelectUtente(u); setShowDropdown(false); }}
                        style={{
                          padding: '12px 15px', borderBottom: '1px solid #f1f5f9', cursor: 'pointer',
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: '600', color: '#2d3748' }}>{u.nome}</div>
                          <div style={{ fontSize: '0.8rem', color: '#718096' }}>NIF: {u.num_utente} | Tel: {u.telemovel}</div>
                        </div>
                        <CheckCircle size={16} color="#48bb78" />
                      </div>
                    ))}
                  </div>
                )}
                
                <div style={{ textAlign: 'center', margin: '20px 0' }}>
                  <div style={{ position: 'relative' }}>
                    <hr style={{ border: '0', borderTop: '1px solid #e2e8f0' }} />
                    <span style={{ 
                      position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                      background: 'white', padding: '0 15px', color: '#718096', fontSize: '0.85rem'
                    }}>OU</span>
                  </div>
                </div>
                
                <button 
                  className="btn-new-utente" 
                  style={{ 
                    width: '100%', display: 'flex', alignItems: 'center', justifyCenter: 'center', 
                    gap: '10px', padding: '12px', borderRadius: '8px', border: '2px dashed #4299e1',
                    background: '#ebf8ff', color: '#2b6cb0', fontWeight: '600', cursor: 'pointer'
                  }}
                  onClick={() => setShowUtenteForm(true)}
                >
                  <UserPlus size={20} />
                  Registar Novo Utente no Sistema
                </button>
              </div>
            )}

            {searchResults.length === 0 && searchQuery && !isSearching && !showUtenteForm && (
               <div className="no-results" style={{ marginTop: '20px', textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
                  <p style={{ color: '#64748b', marginBottom: '10px' }}>Nenhum utente encontrado com "{searchQuery}"</p>
                  <button className="btn btn-primary" onClick={() => {
                    setShowUtenteForm(true);
                    setNewUtente({...newUtente, num_utente: /^\d+$/.test(searchQuery) ? searchQuery : ''});
                  }}>
                    Criar Novo Registo
                  </button>
               </div>
            )}

            {searchResults.length > 0 && showDropdown && (
              <div className="results-list dynamic-dropdown">
                <div className="dropdown-header">Resultados da Pesquisa:</div>
                {searchResults.map(u => (
                  <div key={u.num_utente} className="result-item" onClick={() => { handleSelectUtente(u); setShowDropdown(false); }}>
                    <div className="result-info">
                      <span className="result-name">{u.nome}</span>
                      <span className="result-details">NIF: {u.num_utente} | Tel: {u.telemovel || 'N/A'}</span>
                    </div>
                    <CheckCircle size={20} color="#48bb78" className="select-icon" />
                  </div>
                ))}
              </div>
            )}

            {selectedUtente && (
              <div className="selected-card">
                <div className="card-header">
                  <span className="status-badge">Selecionado</span>
                  <button className="text-button" onClick={() => setSelectedUtente(null)}>Alterar</button>
                </div>
                <div className="card-body">
                  <p><strong>Nome:</strong> {selectedUtente.nome}</p>
                  <p><strong>Nº Utente:</strong> {selectedUtente.num_utente}</p>
                  <p><strong>Morada:</strong> {selectedUtente.morada || 'N/A'}</p>
                  <p><strong>Localidade:</strong> {selectedUtente.localidade}</p>
                </div>
              </div>
            )}

            {showUtenteForm && (
              <div className="new-utente-form">
                <div className="form-header">
                  <h4>Novo Registo de Utente</h4>
                  <button className="text-button" onClick={() => setShowUtenteForm(false)}>Cancelar</button>
                </div>
                <form onSubmit={handleCreateUtente}>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Nº Utente (SNS):</label>
                      <input 
                        type="number" required 
                        value={newUtente.num_utente}
                        onChange={(e) => setNewUtente({...newUtente, num_utente: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Telemóvel:</label>
                      <input 
                        type="text" required 
                        value={newUtente.telemovel}
                        onChange={(e) => setNewUtente({...newUtente, telemovel: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Nome Completo:</label>
                    <input 
                      type="text" required 
                      value={newUtente.nome}
                      onChange={(e) => setNewUtente({...newUtente, nome: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>E-mail (Para App Mobile):</label>
                    <input 
                      type="email" required 
                      value={newUtente.email}
                      onChange={(e) => setNewUtente({...newUtente, email: e.target.value})}
                      placeholder="utente@email.com"
                    />
                  </div>

                  {emailInUse && (
                    <div className="parentesco-box animate-fade-in">
                      <div className="alert-inline info">
                        <AlertCircle size={16} />
                        <span>Este e-mail já está em uso. Por favor, indique o parentesco.</span>
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Grau de Parentesco:</label>
                          <select 
                            className="form-select"
                            value={newUtente.parentesco}
                            onChange={(e) => setNewUtente({...newUtente, parentesco: e.target.value})}
                            required={emailInUse}
                          >
                            <option value="">Selecione...</option>
                            {parentescoOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                          </select>
                        </div>
                        {newUtente.parentesco === 'Outro' && (
                          <div className="form-group">
                            <label>Especifique:</label>
                            <input 
                              type="text" 
                              placeholder="Ex: Primo/a, Tutor..."
                              value={customParentesco}
                              onChange={(e) => setCustomParentesco(e.target.value)}
                              required
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="form-group">
                    <label>Morada:</label>
                    <input 
                      type="text" required 
                      value={newUtente.morada}
                      onChange={(e) => setNewUtente({...newUtente, morada: e.target.value})}
                    />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Data Nascimento:</label>
                      <input 
                        type="date" required 
                        value={newUtente.data_nascimento}
                        onChange={(e) => setNewUtente({...newUtente, data_nascimento: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Sexo:</label>
                      <select 
                        value={newUtente.sexo}
                        onChange={(e) => setNewUtente({...newUtente, sexo: e.target.value})}
                      >
                        <option value="M">Masculino</option>
                        <option value="F">Feminino</option>
                        <option value="O">Outro</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Localidade:</label>
                    <input 
                      type="text" required 
                      value={newUtente.localidade}
                      onChange={(e) => setNewUtente({...newUtente, localidade: e.target.value})}
                    />
                  </div>
                  <button type="submit" className="success-button">
                    <UserPlus size={18} /> Registar Utente
                  </button>
                </form>
              </div>
            )}
          </section>
        </div>

        {/* COLUNA 2: DETALHES DO EPISÓDIO */}
        <div className="column">
          <section className="form-section">
            <h3>2. Detalhes do Episódio</h3>
            <form className="clinical-form" onSubmit={handleSubmitEpisode}>
              <div className="form-group">
                <label>Código do Episódio:</label>
                <input 
                  type="text" 
                  value="Gerado Automaticamente" 
                  readOnly 
                  className="read-only-input"
                  style={{ fontStyle: 'italic', color: '#718096' }}
                />
              </div>

              <div className="form-group">
                <label>Data/Hora Entrada:</label>
                <input 
                  type="datetime-local" value={formData.data_h_entrada} 
                  onChange={(e) => setFormData({...formData, data_h_entrada: e.target.value})}
                  required 
                />
              </div>

              <div className="form-group">
                <label>Hospital de Registo:</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <select 
                    className="form-input"
                    value={formData.id_hospital} 
                    onChange={(e) => setFormData({...formData, id_hospital: e.target.value})}
                    required
                    disabled={utilizador?.role === 'RECECIONISTA'}
                  >
                    <option value="">Selecione um Hospital...</option>
                    {hospitals.map(h => (
                      <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
                    ))}
                  </select>
                  {utilizador?.role === 'RECECIONISTA' && (
                    <span style={{ fontSize: '0.8rem', color: '#718096', whiteSpace: 'nowrap' }}>
                      (Fixo à sessão)
                    </span>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label>Sintomas:</label>
                <textarea 
                  value={formData.sintomas} 
                  onChange={(e) => setFormData({...formData, sintomas: e.target.value})}
                  placeholder="Descreva os sintomas principais..."
                  rows={3}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Observações:</label>
                <textarea 
                  value={formData.observacoes} 
                  onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                  placeholder="Notas adicionais de admissão..."
                  rows={2}
                  className="form-input"
                />
              </div>

              <button 
                type="submit" 
                className="primary-button" 
                disabled={!selectedUtente}
                style={{ marginTop: '20px', width: '100%', padding: '15px' }}
              >
                Registar Admissão Final
              </button>
              {!selectedUtente && <p className="hint">Selecione um utente para ativar o registo.</p>}
            </form>
          </section>
        </div>
      </div>

      <style jsx>{`
        .admission-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }
        .form-section { background: white; padding: 18px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }
        .section-header { margin-bottom: 15px; }
        .form-section h3 { margin-top: 0; color: #2d3748; border-bottom: 3px solid #4299e1; padding-bottom: 8px; font-size: 1.1rem; }
        
        .search-box { display: flex; gap: 8px; margin-bottom: 15px; }
        .search-input { flex: 1; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem; }
        .search-button { display: flex; align-items: center; gap: 6px; background: #4299e1; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.9rem; }
        
        .new-utente-form { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; }
        
        .parentesco-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin: 10px 0; border-left: 4px solid #3b82f6; }
        .alert-inline { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; margin-bottom: 8px; }
        .alert-inline.info { color: #1e40af; }
        
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .success-button { width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; background: #48bb78; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 700; margin-top: 12px; }
        
        .text-button { background: none; border: none; color: #4299e1; text-decoration: underline; cursor: pointer; font-weight: 600; font-size: 0.9rem; }
        .hint { font-size: 0.8rem; color: #a0aec0; text-align: center; margin-top: 8px; }
        .read-only-input { background: #edf2f7; color: #4a5568; }
        .form-input { width: 100%; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem; font-family: inherit; }
        .form-input:focus { outline: none; border-color: #4299e1; }
        .icon-warning { color: #f6ad55; margin-right: 8px; }

        /* Estilos de Pesquisa Dinâmica Compactos */
        .dynamic-dropdown { background: white; border: 1px solid #e2e8f0; border-radius: 10px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); overflow: hidden; margin-top: 4px; position: absolute; width: 100%; max-width: 450px; z-index: 1000; }
        .dropdown-header { background: #f8fafc; padding: 6px 12px; font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
        .result-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; cursor: pointer; transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
        .result-item:last-child { border-bottom: none; }
        .result-item:hover { background: #eff6ff; }
        .result-name { font-weight: 600; color: #1e293b; display: block; font-size: 0.9rem; }
        .result-details { font-size: 0.75rem; color: #64748b; }
        .select-icon { opacity: 0; transition: opacity 0.2s; }
        .result-item:hover .select-icon { opacity: 1; }

        .selected-card { background: #f0fdf4; border: 2px solid #22c55e; border-radius: 10px; padding: 12px; position: relative; animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .status-badge { background: #48bb78; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; display: inline-block; }
        .card-header { display: flex; justify-content: space-between; align-items: flex-start; }
        .selected-card p { margin: 3px 0; font-size: 0.85rem; color: #1e293b; }
        .selected-card strong { color: #166534; }
      `}</style>
    </div>
  );
};

export default NewEpisode;
