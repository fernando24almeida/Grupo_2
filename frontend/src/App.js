import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ProvedorAutenticacao, usarAutenticacao } from './services/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Activate from './pages/Activate';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import SelectHospital from './pages/SelectHospital';
import Dashboard from './pages/Dashboard';
import Admin from './pages/Admin';
import NewEpisode from './pages/NewEpisode';
import Triage from './pages/Triage';
import ClinicalActs from './pages/ClinicalActs';
import Analytics from './pages/Analytics';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { utilizador } = usarAutenticacao();
  const location = window.location.pathname;

  if (!utilizador) return <Navigate to="/login" />;
  
  // Apenas RECECIONISTA, MEDICO e ENFERMEIRO precisam de selecionar hospital
  // O ADMIN tem visão global e não deve ser obrigado a selecionar
  const needsHospital = ['RECECIONISTA', 'MEDICO', 'ENFERMEIRO'].includes(utilizador.role);
  if (needsHospital && !utilizador.hospital && location !== '/select-hospital') {
    return <Navigate to="/select-hospital" />;
  }
  
  return <Layout>{children}</Layout>;
};

function App() {
  return (
    <ProvedorAutenticacao>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/activate" element={<Activate />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/select-hospital" element={<ProtectedRoute><SelectHospital /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
          <Route path="/new-episode" element={<ProtectedRoute><NewEpisode /></ProtectedRoute>} />
          <Route path="/triage" element={<ProtectedRoute><Triage /></ProtectedRoute>} />
          <Route path="/clinical-acts" element={<ProtectedRoute><ClinicalActs /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </Router>
    </ProvedorAutenticacao>
  );
}

export default App;
