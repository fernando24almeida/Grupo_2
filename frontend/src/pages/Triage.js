import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';

const Triage = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  
  const [formData, setFormData] = useState({
    cod_epis: '',
    prioridade: 'VERDE',
    sintomas: '',
    observacoes: '',
    num_func_enfermeiro: utilizador?.num_func || 1001 // Use logged user's staff number if available
  });

  useEffect(() => {
    const fetchEpisodes = async () => {
      try {
        const params = {};
        if (utilizador?.hospital) {
          params.id_hospital = utilizador.hospital;
        }
        const res = await axios.get('/clinical/episodes', { params });
        setEpisodes(res.data);
        if (res.data.length > 0) {
          setFormData(prev => ({ ...prev, cod_epis: res.data[0].cod_epis }));
        }
      } catch (error) {
        console.error('Erro ao carregar episódios', error);
      } finally {
        setLoading(false);
      }
    };
    fetchEpisodes();
  }, [utilizador]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/triagens', formData);
      setMessage({ type: 'success', text: 'Triagem registada com sucesso!' });
      setFormData({
        ...formData,
        sintomas: '',
        observacoes: ''
      });
    } catch (error) {
      console.error('Erro ao registar triagem', error);
      setMessage({ type: 'error', text: 'Erro ao registar triagem.' });
    }
  };

  if (loading) return <div className="page-container">Carregando...</div>;

  return (
    <div className="page-container">
      <header className="page-header">
        <h2>Triagem de Paciente</h2>
        <button className="secondary-button" onClick={() => navigate('/dashboard')}>Voltar</button>
      </header>

      {message && <div className={`alert ${message.type}`}>{message.text}</div>}

      <form className="clinical-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Episódio de Urgência:</label>
          <select 
            value={formData.cod_epis} 
            onChange={(e) => setFormData({...formData, cod_epis: e.target.value})}
            required
          >
            {episodes.map(ep => (
              <option key={ep.cod_epis} value={ep.cod_epis}>
                {ep.cod_epis} - (Entrada: {new Date(ep.data_h_entrada).toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Prioridade (Manchester):</label>
          <select 
            value={formData.prioridade} 
            onChange={(e) => setFormData({...formData, prioridade: e.target.value})}
            className={`priority-select ${formData.prioridade.toLowerCase()}`}
          >
            <option value="VERMELHO">Vermelho (Emergência)</option>
            <option value="LARANJA">Laranja (Muito Urgente)</option>
            <option value="AMARELO">Amarelo (Urgente)</option>
            <option value="VERDE">Verde (Pouco Urgente)</option>
            <option value="AZUL">Azul (Não Urgente)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Sintomas:</label>
          <textarea 
            value={formData.sintomas} 
            onChange={(e) => setFormData({...formData, sintomas: e.target.value})}
            required
            placeholder="Descreva os sintomas principais..."
          />
        </div>

        <div className="form-group">
          <label>Observações:</label>
          <textarea 
            value={formData.observacoes} 
            onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
            placeholder="Notas adicionais de enfermagem..."
          />
        </div>

        <button type="submit" className="primary-button">Guardar Triagem</button>
      </form>
    </div>
  );
};

export default Triage;
