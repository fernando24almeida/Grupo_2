import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Mail, Phone, Lock, Save, ShieldCheck, Hash, CheckCircle, AlertCircle } from 'lucide-react';

const Profile = () => {
  const [userData, setUserData] = useState({
    id_utilizador: '',
    nome_utilizador: '',
    nome_completo: '',
    email: '',
    telemovel: '',
    id_role: '',
    num_func: '',
    ativo: false
  });
  
  const [papeis, setPapeis] = useState([]);
  const [novaPassword, setNovaPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [mensagem, setMensagem] = useState({ tipo: '', texto: '' });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      // Garantir que temos o token para o pedido, lendo diretamente do localStorage
      const token = localStorage.getItem('token');
      const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};

      // Carregar papéis para mostrar o nome do cargo
      const resPapeis = await axios.get('/auth/roles', config);
      setPapeis(resPapeis.data);

      // Carregar dados do perfil
      const res = await axios.get('/auth/users/me', config);
      console.log('Perfil carregado:', res.data);
      
      setUserData({
        id_utilizador: res.data.id_utilizador || '',
        nome_utilizador: res.data.nome_utilizador || '',
        nome_completo: res.data.nome_completo || '',
        email: res.data.email || '',
        telemovel: res.data.telemovel || '',
        id_role: res.data.id_role || '',
        num_func: res.data.num_func || '',
        ativo: res.data.ativo || false
      });
      setLoading(false);
    } catch (err) {
      console.error('Erro ao carregar perfil:', err);
      setMensagem({ tipo: 'error', texto: 'Sessão expirada ou erro ao carregar dados.' });
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMensagem({ tipo: '', texto: '' });

    const payload = {
      nome_completo: userData.nome_completo,
      email: userData.email,
      telemovel: userData.telemovel,
    };

    if (novaPassword) {
      payload.palavra_passe = novaPassword;
    }

    try {
      await axios.patch('/auth/users/me', payload);
      setMensagem({ tipo: 'success', texto: 'Perfil atualizado com sucesso!' });
      setNovaPassword('');
      fetchProfile();
    } catch (err) {
      setMensagem({ tipo: 'error', texto: err.response?.data?.detail || 'Erro ao atualizar perfil.' });
    }
  };

  if (loading) return <div className="loading">Carregando perfil...</div>;

  const roleName = papeis.find(p => p.id_role === userData.id_role)?.nome || 'Utilizador';

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
        {/* COLUNA DA ESQUERDA: INFORMAÇÃO FIXA (CHAVE) */}
        <div className="profile-sidebar">
          <div className="card user-card">
            <div className="user-avatar">
              {userData.nome_completo.charAt(0).toUpperCase()}
            </div>
            <h3>{userData.nome_completo}</h3>
            <span className="badge-role">{roleName}</span>
            
            <div className="user-info-list">
              <div className="info-item">
                <Hash size={16} />
                <span>ID: {userData.id_utilizador}</span>
              </div>
              <div className="info-item">
                <User size={16} />
                <span>Username: {userData.nome_utilizador}</span>
              </div>
              {userData.num_func && (
                <div className="info-item">
                  <ShieldCheck size={16} />
                  <span>Nº Funcionário: {userData.num_func}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* COLUNA DA DIREITA: FORMULÁRIO EDITÁVEL */}
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

              <hr className="divider" />

              <div className="section-header" style={{ marginTop: '1rem' }}>
                <Lock className="icon-purple" />
                <h3>Segurança</h3>
              </div>
              
              <div className="form-group">
                <label>Alterar Palavra-passe:</label>
                <div className="input-with-icon">
                  <Lock size={18} />
                  <input 
                    type="password" 
                    value={novaPassword} 
                    onChange={e => setNovaPassword(e.target.value)}
                    placeholder="Deixe em branco para manter a atual"
                  />
                </div>
                <p className="form-hint">Mínimo 12 caracteres, com maiúsculas, números e símbolos.</p>
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
