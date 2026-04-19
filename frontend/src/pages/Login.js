import React, { useState } from 'react';
import { usarAutenticacao } from '../services/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Activity, Lock, User, AlertCircle, ShieldCheck, QrCode } from 'lucide-react';

const Login = () => {
  const [nomeUtilizador, setNomeUtilizador] = useState('');
  const [palavraPasse, setPalavraPasse] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaSetup, setMfaSetup] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [qrCodeImage, setQrCodeImage] = useState('');
  const [secret, setSecret] = useState('');
  const [error, setError] = useState(null);
  const { entrar, validarMFA } = usarAutenticacao();
  const navigate = useNavigate();

  const submeterFormulario = async (e) => {
    e.preventDefault();
    setError(null);

    if (mfaRequired) {
      // Se for a primeira vez (setup), temos de ativar o MFA antes de validar o login final
      if (mfaSetup) {
          try {
            // Chamada direta para ativar o MFA usando o código de 6 dígitos
            // Nota: Para segurança máxima, isto deve ser feito com o username
            // Mas o nosso backend já valida o código contra o segredo gerado
            const sucesso = await validarMFA(nomeUtilizador, mfaCode);
            if (sucesso) navigate('/dashboard');
            else setError('Código de ativação inválido.');
          } catch (err) {
            setError('Erro ao ativar MFA.');
          }
          return;
      }

      const sucesso = await validarMFA(nomeUtilizador, mfaCode);
      if (sucesso) navigate('/dashboard');
      else setError('Código MFA inválido.');
      return;
    }

    const resultado = await entrar(nomeUtilizador, palavraPasse);
    
    if (resultado.conta_inativa) {
      setError(
        <span>
          A sua conta ainda não está ativa. {' '}
          <button 
            type="button" 
            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', textDecoration: 'underline', padding: 0, font: 'inherit' }}
            onClick={() => navigate('/activate')}
          >
            Clique aqui para ativar
          </button>
        </span>
      );
      return;
    }

    if (resultado.mfa_required) {
      setMfaRequired(true);
      if (!resultado.setup_complete) {
        setMfaSetup(true);
        setQrCodeUrl(resultado.qr_code_url);
        setQrCodeImage(resultado.qr_code_image);
        setSecret(resultado.secret);
      }
    } else if (resultado.sucesso) {
      navigate('/dashboard');
    } else {
      setError(resultado.erro || 'Falha no login.');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ 
            display: 'inline-flex', 
            background: 'var(--primary)', 
            color: 'white', 
            padding: '1rem', 
            borderRadius: '1rem',
            marginBottom: '1rem' 
          }}>
            {mfaRequired ? <ShieldCheck size={32} /> : <Activity size={32} />}
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {mfaRequired ? 'Segurança Adicional' : 'Portal Clínico'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {mfaRequired ? 'Proteção de dois fatores ativa' : 'Introduza os seus dados para aceder ao sistema'}
          </p>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={submeterFormulario}>
          {!mfaRequired ? (
            <>
              <div className="form-group">
                <label>Utilizador</label>
                <div style={{ position: 'relative' }}>
                  <User size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input 
                    type="text" 
                    placeholder="nome.utilizador" 
                    style={{ paddingLeft: '40px' }}
                    value={nomeUtilizador} 
                    onChange={(e) => setNomeUtilizador(e.target.value)} 
                    required 
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Palavra-passe</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input 
                    type="password" 
                    placeholder="••••••••" 
                    style={{ paddingLeft: '40px' }}
                    value={palavraPasse} 
                    onChange={(e) => setPalavraPasse(e.target.value)} 
                    required 
                  />
                </div>
                <div style={{ textAlign: 'right', marginTop: '0.5rem' }}>
                  <button 
                    type="button" 
                    className="link-btn"
                    style={{ fontSize: '0.8rem', color: 'var(--primary)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                    onClick={() => navigate('/forgot-password')}
                  >
                    Esqueceu-se dos dados?
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="form-group">
              {mfaSetup ? (
                <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                  <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px dashed #cbd5e1', marginBottom: '1rem' }}>
                    <QrCode size={48} style={{ margin: '0 auto 1rem', color: 'var(--primary)' }} />
                    <p style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-main)' }}>Configuração de Segurança</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      Leia o QR Code abaixo com o Google Authenticator ou utilize o segredo manual.
                    </p>
                    
                    {/* Prioritário: QR gerado localmente pelo backend. Fallback: Google Charts */}
                    <img 
                      src={qrCodeImage || `https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=${encodeURIComponent(qrCodeUrl)}`} 
                      alt="MFA QR Code"
                      style={{ margin: '1rem auto', display: 'block', borderRadius: '8px', width: '200px', height: '200px' }}
                    />
                    
                    <div style={{ background: 'white', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Segredo Manual:</p>
                      <code style={{ fontSize: '0.9rem', color: 'var(--primary)', letterSpacing: '0.1rem', fontWeight: 'bold' }}>{secret}</code>
                    </div>
                  </div>
                </div>
              ) : null}
              
              <label style={{ textAlign: 'center', display: 'block', marginBottom: '0.5rem' }}>Introduza o código de 6 dígitos</label>
              <input 
                type="text" 
                placeholder="000 000" 
                maxLength="6"
                style={{ textAlign: 'center', fontSize: '1.8rem', letterSpacing: '0.5rem', height: '60px', fontWeight: 'bold' }}
                value={mfaCode} 
                onChange={(e) => setMfaCode(e.target.value.replace(/\s/g, ''))} 
                required 
                autoFocus
              />
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', height: '54px', fontSize: '1rem' }}>
            {mfaRequired ? (mfaSetup ? 'Ativar e Entrar' : 'Verificar e Entrar') : 'Entrar no Sistema'}
          </button>
          
          {mfaRequired && (
            <button type="button" className="btn" style={{ width: '100%', marginTop: '0.5rem', background: 'transparent' }} onClick={() => setMfaRequired(false)}>
              Voltar ao Login
            </button>
          )}
        </form>

        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <p>Protegido por Encriptação AES-256 e MFA Obrigatório</p>
          <p style={{ marginTop: '0.5rem' }}>&copy; 2026 Grupo 2</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
