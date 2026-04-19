import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usarAutenticacao } from '../services/AuthContext';

const SelectHospital = () => {
  const [hospitais, setHospitais] = useState([]);
  const [selecionado, setSelecionado] = useState('');
  const { definirHospital } = usarAutenticacao();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHospitais = async () => {
      try {
        const res = await axios.get('/clinical/hospitals');
        setHospitais(res.data);
        if (res.data.length > 0) {
          setSelecionado(res.data[0].nome_hosp);
        }
      } catch (error) {
        console.error('Erro ao carregar hospitais', error);
      }
    };
    fetchHospitais();
  }, []);

  const confirmar = () => {
    if (selecionado) {
      definirHospital(selecionado);
      navigate('/dashboard');
    }
  };

  return (
    <div className="login-container">
      <div className="select-hospital-card">
        <h2>Selecionar Hospital</h2>
        <p>Por favor, selecione o hospital onde está a operar neste momento.</p>
        
        <div className="form-group">
          <select 
            value={selecionado} 
            onChange={(e) => setSelecionado(e.target.value)}
            className="full-width-select"
          >
            {hospitais.map(h => (
              <option key={h.nome_hosp} value={h.nome_hosp}>{h.nome_hosp}</option>
            ))}
          </select>
        </div>
        
        <button onClick={confirmar} className="primary-button">Confirmar e Entrar</button>
      </div>

      <style jsx>{`
        .select-hospital-card {
          background: white;
          padding: 30px;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          max-width: 400px;
          width: 100%;
          text-align: center;
        }
        .full-width-select {
          width: 100%;
          padding: 10px;
          margin: 20px 0;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 16px;
        }
        .primary-button {
          width: 100%;
          padding: 12px;
          background-color: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: bold;
        }
        .primary-button:hover {
          background-color: #0056b3;
        }
      `}</style>
    </div>
  );
};

export default SelectHospital;
