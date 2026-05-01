import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';
import { Search, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';

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

  // Estados para Novo Utente
  const [showUtenteForm, setShowUtenteForm] = useState(false);
  const [newUtente, setNewUtente] = useState({
    num_utente: '',
    nome: '',
    email: '',
    telemovel: '',
    morada: '',
    data_nascimento: '',
    sexo: 'M',
    localidade: ''
  });

  const [message, setMessage] = useState(null);

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

    try {
      const payload = {
        num_utente: parseInt(newUtente.num_utente),
        nome: newUtente.nome,
        email: newUtente.email.toLowerCase().trim(),
        telemovel: newUtente.telemovel || null,
        morada: newUtente.morada || null,
        localidade: newUtente.localidade || null,
        sexo: newUtente.sexo || "M",
        data_nascimento: newUtente.data_nascimento || null
      };

      const res = await axios.post('/clinical/utentes', payload);
      setMessage({ type: 'success', text: `Utente ${newUtente.nome} registado! PIN enviado para o e-mail.` });
      setSelectedUtente(res.data);
      setFormData(prev => ({ ...prev, id_utente: res.data.num_utente }));
      setShowUtenteForm(false);
    } catch (error) {
      console.error('Erro detalhado:', error.response?.data);
      const detail = error.response?.data?.detail;
      // Tratar diferentes formatos de erro do FastAPI
      let msg = 'Erro ao registar utente.';
      if (typeof detail === 'string') msg = detail;
      else if (Array.isArray(detail)) msg = `Campo obrigatório em falta: ${detail[0]?.loc[1]}`;
      
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleSubmitEpisode = async (e) => {
    e.preventDefault();
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
        <div className={`alert ${message.type}`}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{message.text}</span>
          {message.type === 'info' && !showUtenteForm && (
            <button className="text-button" onClick={() => {
              setShowUtenteForm(true);
              setNewUtente({...newUtente, num_utente: /^\d+$/.test(searchQuery) ? searchQuery : ''});
            }}>
              Registar Novo Utente
            </button>
          )}
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
              <>
                <form onSubmit={handleSearch} className="search-box">
                  <input 
                    type="text" 
                    placeholder="Nº Utente ou Telefone..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                  />
                  <button type="submit" className="search-button" disabled={isSearching}>
                    <Search size={18} />
                    {isSearching ? '...' : 'Pesquisar'}
                  </button>
                </form>
                
                <div style={{ textAlign: 'center', marginBottom: '15px' }}>
                  <span style={{ color: '#718096', fontSize: '0.9rem' }}>ou</span>
                </div>
                
                <button 
                  className="btn btn-secondary" 
                  style={{ width: '100%', display: 'flex', gap: '8px', color: 'var(--primary)', borderColor: 'var(--primary)' }}
                  onClick={() => setShowUtenteForm(true)}
                >
                  <UserPlus size={18} />
                  Registar Novo Utente
                </button>
              </>
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

            {searchResults.length > 0 && (
              <div className="results-list">
                <h4>Resultados Encontrados:</h4>
                {searchResults.map(u => (
                  <div key={u.num_utente} className="result-item" onClick={() => handleSelectUtente(u)}>
                    <div className="result-info">
                      <span className="result-name">{u.nome}</span>
                      <span className="result-details">SNS: {u.num_utente} | Tel: {u.telemovel}</span>
                    </div>
                    <button className="select-mini-button">Selecionar</button>
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
                <select 
                  className="form-input"
                  value={formData.id_hospital} 
                  onChange={(e) => setFormData({...formData, id_hospital: e.target.value})}
                  required
                >
                  <option value="">Selecione um Hospital...</option>
                  {hospitals.map(h => (
                    <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
                  ))}
                </select>
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
        .admission-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 20px; }
        .form-section { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }
        .section-header { margin-bottom: 20px; }
        .form-section h3 { margin-top: 0; color: #2d3748; border-bottom: 3px solid #4299e1; padding-bottom: 10px; font-size: 1.25rem; }
        
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-input { flex: 1; padding: 10px 15px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 1rem; }
        .search-button { display: flex; align-items: center; gap: 8px; background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; }
        
        .results-list { margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px; }
        .result-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f7fafc; border-radius: 8px; margin-bottom: 8px; cursor: pointer; border: 1px solid transparent; transition: all 0.2s; }
        .result-item:hover { border-color: #4299e1; background: #ebf8ff; }
        .result-name { display: block; font-weight: 700; color: #2d3748; }
        .result-details { font-size: 0.85rem; color: #718096; }
        .select-mini-button { background: white; border: 1px solid #4299e1; color: #4299e1; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        
        .selected-card { background: #f0fff4; border: 2px solid #68d391; border-radius: 12px; padding: 20px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .status-badge { background: #48bb78; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
        
        .new-utente-form { background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .success-button { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; background: #48bb78; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: 700; margin-top: 15px; }
        
        .text-button { background: none; border: none; color: #4299e1; text-decoration: underline; cursor: pointer; font-weight: 600; }
        .hint { font-size: 0.85rem; color: #a0aec0; text-align: center; margin-top: 10px; }
        .read-only-input { background: #edf2f7; color: #4a5568; }
        .form-input { width: 100%; padding: 10px 15px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 1rem; font-family: inherit; }
        .form-input:focus { outline: none; border-color: #4299e1; }
        .icon-warning { color: #f6ad55; margin-right: 10px; }
      `}</style>
    </div>
  );
};

export default NewEpisode;
