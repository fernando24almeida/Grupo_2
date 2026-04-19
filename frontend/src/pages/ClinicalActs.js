import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';

const ClinicalActs = () => {
  const { utilizador } = usarAutenticacao();
  const navigate = useNavigate();
  const [episodes, setEpisodes] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  
  const [formData, setFormData] = useState({
    tipo: 'CONSULTA',
    data_h_inicio: new Date().toISOString().slice(0, 16),
    data_h_fim: null,
    cod_epis: '',
    id_hosp: utilizador?.hospital || '',
    num_func: utilizador?.num_func || 1002 // Default test doctor if not available
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = {};
        if (utilizador?.hospital) {
          params.id_hospital = utilizador.hospital;
        }
        const [epRes, hospRes] = await Promise.all([
          axios.get('/clinical/episodes', { params }),
          axios.get('/clinical/hospitals')
        ]);
        setEpisodes(epRes.data);
        setHospitals(hospRes.data);
        
        if (epRes.data.length > 0) {
          setFormData(prev => ({ 
            ...prev, 
            cod_epis: epRes.data[0].cod_epis,
            id_hosp: epRes.data[0].id_hospital // Use episode's hospital by default
          }));
        }
      } catch (error) {
        console.error('Erro ao carregar dados', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [utilizador]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/clinical/atos', formData);
      setMessage({ type: 'success', text: 'Ato clínico registado com sucesso!' });
    } catch (error) {
      console.error('Erro ao registar ato clínico', error);
      setMessage({ type: 'error', text: 'Erro ao registar ato clínico. Verifique se a data já existe (PK).' });
    }
  };

  if (loading) return <div className="page-container">Carregando...</div>;

  return (
    <div className="page-container">
      <header className="page-header">
        <h2>Atos Clínicos (Consultas e Exames)</h2>
        <button className="secondary-button" onClick={() => navigate('/dashboard')}>Voltar</button>
      </header>

      {message && <div className={`alert ${message.type}`}>{message.text}</div>}

      <form className="clinical-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Episódio:</label>
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
          <label>Tipo de Ato:</label>
          <select 
            value={formData.tipo} 
            onChange={(e) => setFormData({...formData, tipo: e.target.value})}
          >
            <option value="CONSULTA">Consulta Médica</option>
            <option value="EXAME">Exame de Diagnóstico</option>
            <option value="ANALISE">Análise Clínica</option>
            <option value="INTERVENCAO">Intervenção</option>
          </select>
        </div>

        <div className="form-group">
          <label>Data/Hora Início:</label>
          <input 
            type="datetime-local" 
            value={formData.data_h_inicio} 
            onChange={(e) => setFormData({...formData, data_h_inicio: e.target.value})}
            required 
          />
        </div>

        <div className="form-group">
          <label>Hospital:</label>
          <select 
            value={formData.id_hosp} 
            onChange={(e) => setFormData({...formData, id_hosp: e.target.value})}
            required
          >
            {hospitals.map(h => (
              <option key={h.nome_hosp} value={h.nome_hosp}>
                {h.nome_hosp}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" className="primary-button">Registar Ato</button>
      </form>
    </div>
  );
};

export default ClinicalActs;
