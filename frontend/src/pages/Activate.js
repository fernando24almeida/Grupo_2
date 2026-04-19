import React, { useState } from 'react';
import { usarAutenticacao } from '../services/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Mail, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';

const Activate = () => {
  const [email, setEmail] = useState('');
  const [codigo, setCodigo] = useState('');
  const [error, setError] = useState(null);
  const [sucesso, setSucesso] = useState(false);
  const { ativarConta } = usarAutenticacao();
  const navigate = useNavigate();

  const handleAtivar = async (e) => {
    e.preventDefault();
    setError(null);
    const res = await ativarConta(email, codigo);
    if (res.sucesso) {
      setSucesso(true);
      setTimeout(() => navigate('/login'), 3000);
    } else {
      setError(res.erro);
    }
  };

  if (sucesso) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: 'center' }}>
          <CheckCircle size={64} color="var(--success)" style={{ margin: '0 auto 1.5rem' }} />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>Conta Ativada!</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>
            A sua conta foi validada com sucesso. Redirecionando para o login...
          </p>
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '2rem' }} onClick={() => navigate('/login')}>
            Ir para Login Agora
          </button>
        </div>
      </div>
    );
  }

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
            <Mail size={32} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>Ativação de Conta</h1>
          <p style={{ color: 'var(--text-muted)' }}>Introduza o código de 6 dígitos enviado para o seu e-mail</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleAtivar}>
          <div className="form-group">
            <label>E-mail de Registo</label>
            <input 
              type="email" 
              placeholder="exemplo@hospital.com" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
            />
          </div>

          <div className="form-group">
            <label>Código de Ativação</label>
            <input 
              type="text" 
              placeholder="000000" 
              maxLength="6"
              style={{ textAlign: 'center', fontSize: '1.5rem', letterSpacing: '0.5rem', fontWeight: 'bold' }}
              value={codigo} 
              onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ''))} 
              required 
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', height: '48px' }}>
            Ativar Conta
          </button>
          
          <button type="button" className="btn" style={{ width: '100%', marginTop: '0.5rem', background: 'transparent' }} onClick={() => navigate('/login')}>
            <ArrowLeft size={16} style={{ marginRight: '8px' }} /> Voltar ao Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default Activate;
