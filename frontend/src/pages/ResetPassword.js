import React, { useState } from 'react';
import { usarAutenticacao } from '../services/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, Key, AlertCircle, CheckCircle } from 'lucide-react';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [novaPassword, setNovaPassword] = useState('');
  const [confirmarPassword, setConfirmarPassword] = useState('');
  const [error, setError] = useState(null);
  const [mensagem, setMensagem] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const { redefinirPassword } = usarAutenticacao();
  const navigate = useNavigate();

  const handleReset = async (e) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError('Token de recuperação em falta.');
      return;
    }

    if (novaPassword !== confirmarPassword) {
      setError('As palavras-passe não coincidem.');
      return;
    }

    setCarregando(true);
    const res = await redefinirPassword(token, novaPassword);
    setCarregando(false);

    if (res.sucesso) {
      setMensagem(res.mensagem);
      setTimeout(() => navigate('/login'), 3000);
    } else {
      setError(res.erro);
    }
  };

  if (!token) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: 'center' }}>
          <AlertCircle size={64} color="var(--error)" style={{ margin: '0 auto 1.5rem' }} />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>Link Inválido</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>
            Este link de recuperação de palavra-passe é inválido ou já expirou.
          </p>
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '2rem' }} onClick={() => navigate('/forgot-password')}>
            Pedir Novo Link
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
            <Key size={32} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>Nova Palavra-passe</h1>
          <p style={{ color: 'var(--text-muted)' }}>Introduza a sua nova palavra-passe de segurança</p>
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
          <form onSubmit={handleReset}>
            <div className="form-group">
              <label>Nova Palavra-passe</label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="password" 
                  placeholder="••••••••••••" 
                  style={{ paddingLeft: '40px' }}
                  value={novaPassword} 
                  onChange={(e) => setNovaPassword(e.target.value)} 
                  required 
                />
              </div>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                Mínimo 12 caracteres, 1 maiúscula, 1 número e 1 símbolo.
              </p>
            </div>

            <div className="form-group">
              <label>Confirmar Palavra-passe</label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="password" 
                  placeholder="••••••••••••" 
                  style={{ paddingLeft: '40px' }}
                  value={confirmarPassword} 
                  onChange={(e) => setConfirmarPassword(e.target.value)} 
                  required 
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', height: '48px' }} disabled={carregando}>
              {carregando ? 'A processar...' : 'Redefinir Palavra-passe'}
            </button>
          </form>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            A redirecionar para o login...
          </p>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;
