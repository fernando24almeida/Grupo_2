import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const ContextoAutenticacao = createContext(null);

export const ProvedorAutenticacao = ({ children }) => {
  const [utilizador, setUtilizador] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [hospital, setHospital] = useState(localStorage.getItem('hospital_selecionado'));

  // Configuração imediata do axios para evitar race conditions no primeiro render
  if (token && !axios.defaults.headers.common['Authorization']) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const papel = localStorage.getItem('role');
      const hosp = localStorage.getItem('hospital_selecionado');
      setUtilizador({ token, role: papel, hospital: hosp });
    } else {
      delete axios.defaults.headers.common['Authorization'];
      setUtilizador(null);
    }
  }, [token]);

  const entrar = async (nomeUtilizador, palavraPasse) => {
    try {
      const parametros = new URLSearchParams();
      parametros.append('username', nomeUtilizador);
      parametros.append('password', palavraPasse);
      
      const resposta = await axios.post('/auth/login', parametros, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      // Se o MFA for necessário, devolvemos a informação para o componente de Login tratar
      if (resposta.data.mfa_required) {
        return { 
          mfa_required: true, 
          setup_complete: resposta.data.mfa_setup_complete,
          qr_code_url: resposta.data.qr_code_url,
          qr_code_image: resposta.data.qr_code_image,
          secret: resposta.data.secret
        };
      }

      const { access_token, role } = resposta.data;
      guardarSessao(access_token, role);
      return { sucesso: true };
    } catch (erro) {
      if (erro.response?.status === 403) {
        return { sucesso: false, mfa_required: false, conta_inativa: true, erro: erro.response.data.detail };
      }
      return { sucesso: false, erro: 'Credenciais inválidas. Verifique o utilizador e a palavra-passe.' };
    }
  };

  const validarMFA = async (nomeUtilizador, codigo) => {
    try {
      const resposta = await axios.post('/auth/login/mfa', {
        username: nomeUtilizador,
        mfa_code: codigo
      });
      const { access_token, role } = resposta.data;
      guardarSessao(access_token, role);
      return true;
    } catch (erro) {
      console.error('Falha no MFA', erro);
      return false;
    }
  };

  const configurarMFA = async (tokenTemporario, codigo) => {
    try {
      // Usamos o token que temos no momento (se houver) ou passamos o código
      const resposta = await axios.post('/auth/mfa/ativar?mfa_code=' + codigo);
      return true;
    } catch (erro) {
      return false;
    }
  };

  const ativarConta = async (email, codigo) => {
    try {
      await axios.post('/auth/activate', { email, codigo });
      return { sucesso: true };
    } catch (erro) {
      return { 
        sucesso: false, 
        erro: erro.response?.data?.detail || 'Código inválido ou expirado.' 
      };
    }
  };

  const recuperarDados = async (email, tipo = 'password') => {
    try {
      const endpoint = tipo === 'username' ? '/auth/forgot-username' : '/auth/forgot-password';
      const resposta = await axios.post(endpoint, { email });
      return { sucesso: true, mensagem: resposta.data.message };
    } catch (erro) {
      return { sucesso: false, erro: erro.response?.data?.detail || 'Erro ao processar pedido.' };
    }
  };

  const redefinirPassword = async (token, nova_password) => {
    try {
      const resposta = await axios.post('/auth/reset-password', { token, nova_password });
      return { sucesso: true, mensagem: resposta.data.message };
    } catch (erro) {
      return { sucesso: false, erro: erro.response?.data?.detail || 'Erro ao redefinir palavra-passe.' };
    }
  };

  const guardarSessao = (access_token, role) => {
    localStorage.setItem('token', access_token);
    localStorage.setItem('role', role);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setToken(access_token);
    setUtilizador({ token: access_token, role });
  };

  const definirHospital = (nomeHosp) => {
    localStorage.setItem('hospital_selecionado', nomeHosp);
    setHospital(nomeHosp);
    setUtilizador(prev => ({ ...prev, hospital: nomeHosp }));
  };

  const sair = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('hospital_selecionado');
    setToken(null);
    setUtilizador(null);
    setHospital(null);
  };

  return (
    <ContextoAutenticacao.Provider value={{ 
      utilizador, 
      hospital, 
      entrar, 
      sair, 
      definirHospital, 
      ativarConta, 
      validarMFA, 
      configurarMFA,
      recuperarDados,
      redefinirPassword
    }}>
      {children}
    </ContextoAutenticacao.Provider>
  );
};

export const usarAutenticacao = () => useContext(ContextoAutenticacao);
