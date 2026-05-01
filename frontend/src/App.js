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
import Profile from './pages/Profile';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { utilizador } = usarAutenticacao();

  if (!utilizador) return <Navigate to="/login" />;
  
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
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
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
