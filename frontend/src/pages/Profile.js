import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { usarAutenticacao } from '../services/AuthContext';
import { User, Mail, Phone, Lock, Save, ShieldCheck, Hash, CheckCircle, AlertCircle } from 'lucide-react';

const Profile = () => {
  const { utilizador: authUser } = usarAutenticacao();
  const [userData, setUserData] = useState({
    id_utilizador: '',
    nome_utilizador: '',
    nome_completo: '',
    email: '',
    telemovel: '',
    id_role: '',
    num_func: '',
    num_utente: '', // Adicionado para utentes
    morada: '',
    localidade: '',
    ativo: false,
    estagiario: null
  });
  
  const [papeis, setPapeis] = useState([]);
  const [novaPassword, setNovaPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [mensagem, setMensagem] = useState({ tipo: '', texto: '' });

  const isUtente = authUser?.role === 'UTENTE';

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};

      // Carregar papéis
      const resPapeis = await axios.get('/auth/roles', config);
      setPapeis(resPapeis.data);

      // Carregar dados conforme o papel
      const endpoint = isUtente ? '/clinical/utentes/me' : '/auth/users/me';
      const res = await axios.get(endpoint, config);
      
      if (isUtente) {
        setUserData({
          num_utente: res.data.num_utente,
          nome_completo: res.data.nome,
          email: res.data.email,
          telemovel: res.data.telemovel || '',
          morada: res.data.morada || '',
          localidade: res.data.localidade || '',
          id_role: res.data.id_role
        });
      } else {
        setUserData({
          id_utilizador: res.data.id_utilizador || '',
          nome_utilizador: res.data.nome_utilizador || '',
          nome_completo: res.data.nome_completo || '',
          email: res.data.email || '',
          telemovel: res.data.telemovel || '',
          id_role: res.data.id_role || '',
          num_func: res.data.num_func || '',
          ativo: res.data.ativo || false,
          estagiario: res.data.estagiario || null
        });
      }
      setLoading(false);
    } catch (err) {
      setMensagem({ tipo: 'error', texto: 'Erro ao carregar dados do perfil.' });
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMensagem({ tipo: '', texto: '' });

    let payload = {};
    let endpoint = '';

    if (isUtente) {
      endpoint = '/clinical/utentes/me';
      payload = {
        telemovel: userData.telemovel,
        morada: userData.morada,
        localidade: userData.localidade
      };
      // Nota: PIN alterado via endpoint específico ou patch se o backend permitir
    } else {
      endpoint = '/auth/users/me';
      payload = {
        nome_completo: userData.nome_completo,
        email: userData.email,
        telemovel: userData.telemovel,
        estagiario: userData.estagiario,
        especialidade: userData.especialidade
      };
    }

    if (novaPassword) {
      if (isUtente) {
        // Se for utente, o campo no modelo é password_hash mas o patch espera novo_pin se for endpoint dedicado
        // Para simplificar, assumimos que o backend no patch /utentes/me ignora password ou tratar separadamente
        payload.password = novaPassword; 
      } else {
        payload.palavra_passe = novaPassword;
      }
    }

    try {
      await axios.patch(endpoint, payload);
      setMensagem({ tipo: 'success', texto: 'Perfil atualizado com sucesso!' });
      setNovaPassword('');
      fetchProfile();
    } catch (err) {
      setMensagem({ tipo: 'error', texto: err.response?.data?.detail || 'Erro ao atualizar perfil.' });
    }
  };

  if (loading) return <div className="loading">Carregando perfil...</div>;

  const roleName = papeis.find(p => p.id_role === userData.id_role)?.nome || (isUtente ? 'UTENTE' : 'Utilizador');
  const iniciais = (userData.nome_completo || 'U').charAt(0).toUpperCase();

  return (
    <div className="profile-page">
      <header className="page-header">
        <h1 className="page-title">O Meu Perfil</h1>
        <p className="page-subtitle">Gira as tuas informações pessoais e de segurança</p>
      </header>

      {mensagem.texto && (
        <div className={`alert alert-${mensagem.tipo}`}>
          {mensagem.tipo === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span>{mensagem.texto}</span>
        </div>
      )}

      <div className="profile-grid">
        <div className="profile-sidebar">
          <div className="card user-card">
            <div className="user-avatar">
              {iniciais}
            </div>
            <h3>{userData.nome_completo || 'Utilizador'}</h3>
            <span className="badge-role">{roleName}</span>
            
            <div className="user-info-list">
              {isUtente ? (
                <div className="info-item">
                  <Hash size={16} />
                  <span>NIF: {userData.num_utente}</span>
                </div>
              ) : (
                <>
                  <div className="info-item">
                    <Hash size={16} />
                    <span>ID: {userData.id_utilizador}</span>
                  </div>
                  <div className="info-item">
                    <User size={16} />
                    <span>Username: {userData.nome_utilizador}</span>
                  </div>
                </>
              )}
              <div className="info-item">
                <Mail size={16} />
                <span>{userData.email}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="profile-main">
          <section className="card">
            <div className="section-header">
              <User className="icon-blue" />
              <h3>Dados Pessoais</h3>
            </div>
            <form onSubmit={handleUpdate} className="admin-form">
              <div className="form-group">
                <label>Nome Completo:</label>
                <div className="input-with-icon">
                  <User size={18} />
                  <input 
                    type="text" 
                    value={userData.nome_completo} 
                    onChange={e => setUserData({...userData, nome_completo: e.target.value})}
                    disabled={isUtente}
                    className={isUtente ? 'bg-disabled' : ''}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>E-mail:</label>
                  <div className="input-with-icon">
                    <Mail size={18} />
                    <input 
                      type="email" 
                      value={userData.email} 
                      onChange={e => setUserData({...userData, email: e.target.value})}
                      disabled={isUtente}
                      className={isUtente ? 'bg-disabled' : ''}
                      required
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Telemóvel:</label>
                  <div className="input-with-icon">
                    <Phone size={18} />
                    <input 
                      type="text" 
                      value={userData.telemovel || ''} 
                      onChange={e => setUserData({...userData, telemovel: e.target.value})}
                      placeholder="9xxxxxxxx"
                    />
                  </div>
                </div>
              </div>

              {isUtente && (
                <div className="form-group">
                  <label>Morada:</label>
                  <input 
                    type="text" 
                    value={userData.morada} 
                    onChange={e => setUserData({...userData, morada: e.target.value})}
                    placeholder="Sua morada completa"
                  />
                </div>
              )}

              {!isUtente && userData.id_role && papeis.find(p => p.id_role === userData.id_role)?.nome === 'MEDICO' && (
                <div className="form-row" style={{ background: '#f8fafc', padding: '15px', borderRadius: '8px', marginBottom: '15px', border: '1px solid var(--border)' }}>
                  <div className="form-group">
                    <label>Status Profissional:</label>
                    <select 
                      value={userData.estagiario || 'NÃO'} 
                      onChange={e => setUserData({...userData, estagiario: e.target.value})}
                    >
                      <option value="SIM">Médico Estagiário</option>
                      <option value="NÃO">Médico Especialista</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Especialidade Médica:</label>
                    <input 
                      type="text" 
                      value={userData.especialidade || ''} 
                      onChange={e => setUserData({...userData, especialidade: e.target.value})}
                      placeholder="Ex: Cardiologia, Pediatria..."
                    />
                  </div>
                </div>
              )}

              <hr className="divider" />

              <div className="section-header" style={{ marginTop: '1rem' }}>
                <Lock className="icon-purple" />
                <h3>Segurança</h3>
              </div>
              
              <div className="form-group">
                <label>{isUtente ? 'Alterar PIN:' : 'Alterar Palavra-passe:'}</label>
                <div className="input-with-icon">
                  <Lock size={18} />
                  <input 
                    type="password" 
                    value={novaPassword} 
                    onChange={e => setNovaPassword(e.target.value)}
                    placeholder={isUtente ? 'Novo PIN de 6 dígitos' : 'Deixe em branco para manter a atual'}
                  />
                </div>
                <p className="form-hint">
                  {isUtente ? 'O PIN deve ter 6 dígitos numéricos.' : 'Mínimo 12 caracteres, com maiúsculas, números e símbolos.'}
                </p>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  <Save size={18} /> Guardar Alterações
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>

      <style jsx>{`
        .profile-grid { display: grid; grid-template-columns: 300px 1fr; gap: 30px; margin-top: 2rem; }
        .user-card { text-align: center; padding: 2rem; }
        .user-avatar { width: 80px; height: 80px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold; margin: 0 auto 1rem; }
        .user-info-list { margin-top: 2rem; text-align: left; }
        .info-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); color: var(--text-muted); font-size: 0.9rem; }
        .section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem; }
        .input-with-icon { position: relative; }
        .input-with-icon svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-muted); }
        .input-with-icon input { padding-left: 40px !important; }
        .divider { border: 0; border-top: 1px solid var(--border); margin: 2rem 0; }
        .form-hint { font-size: 0.8rem; color: var(--text-muted); margin-top: 5px; }
        @media (max-width: 768px) { .profile-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

export default Profile;
