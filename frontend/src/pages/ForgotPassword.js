import React, { useState } from 'react';
import { usarAutenticacao } from '../services/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Mail, HelpCircle, AlertCircle, ArrowLeft, CheckCircle } from 'lucide-react';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [tipo, setTipo] = useState('password'); // 'password' ou 'username'
  const [error, setError] = useState(null);
  const [mensagem, setMensagem] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const { recuperarDados } = usarAutenticacao();
  const navigate = useNavigate();

  const handleRecuperar = async (e) => {
    e.preventDefault();
    setError(null);
    setMensagem(null);
    setCarregando(true);
    
    const res = await recuperarDados(email, tipo);
    setCarregando(false);
    
    if (res.sucesso) {
      setMensagem(res.mensagem);
    } else {
      setError(res.erro);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ 
            display: 'inline-flex', 
            background: 'var(--primary)', 
            color: 'white', 
            padding: '1rem', 
            borderRadius: '1rem',
            marginBottom: '1rem' 
          }}>
            <HelpCircle size={32} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>Recuperar Acesso</h1>
          <p style={{ color: 'var(--text-muted)' }}>Introduza o seu e-mail para recuperar os seus dados</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {mensagem && (
          <div className="alert alert-success">
            <CheckCircle size={18} />
            <span>{mensagem}</span>
          </div>
        )}

        {!mensagem ? (
          <form onSubmit={handleRecuperar}>
            <div className="form-group">
              <label>O que deseja recuperar?</label>
              <div style={{ display: 'flex', gap: '10px', marginBottom: '1rem' }}>
                <button 
                  type="button" 
                  className={`btn ${tipo === 'password' ? 'btn-primary' : ''}`}
                  style={{ flex: 1, height: '40px', fontSize: '0.85rem', background: tipo === 'password' ? '' : '#f1f5f9', color: tipo === 'password' ? '' : '#64748b' }}
                  onClick={() => setTipo('password')}
                >
                  Palavra-passe
                </button>
                <button 
                  type="button" 
                  className={`btn ${tipo === 'username' ? 'btn-primary' : ''}`}
                  style={{ flex: 1, height: '40px', fontSize: '0.85rem', background: tipo === 'username' ? '' : '#f1f5f9', color: tipo === 'username' ? '' : '#64748b' }}
                  onClick={() => setTipo('username')}
                >
                  Utilizador
                </button>
              </div>
            </div>

            <div className="form-group">
              <label>E-mail da Conta</label>
              <div style={{ position: 'relative' }}>
                <Mail size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="email" 
                  placeholder="exemplo@hospital.com" 
                  style={{ paddingLeft: '40px' }}
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  required 
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', height: '48px' }} disabled={carregando}>
              {carregando ? 'A processar...' : 'Enviar Pedido'}
            </button>
          </form>
        ) : (
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} onClick={() => navigate('/login')}>
            Voltar ao Login
          </button>
        )}
        
        {!mensagem && (
          <button type="button" className="btn" style={{ width: '100%', marginTop: '0.5rem', background: 'transparent' }} onClick={() => navigate('/login')}>
            <ArrowLeft size={16} style={{ marginRight: '8px' }} /> Voltar ao Login
          </button>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
