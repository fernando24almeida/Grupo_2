-- Script para apagar todas as tabelas e vistas (Drop Tables)
-- Ordem inversa às dependências para evitar erros de Foreign Key

-- 1. Vistas
DROP VIEW IF EXISTS utente_analitico CASCADE;

-- 2. Tabelas de Auditoria e Logs
DROP TABLE IF EXISTS auditoria CASCADE;

-- 3. Tabelas de Fluxo Clínico (Nível 3)
DROP TABLE IF EXISTS internamento CASCADE;
DROP TABLE IF EXISTS prescricao CASCADE;
DROP TABLE IF EXISTS Envolve CASCADE;
DROP TABLE IF EXISTS triagem CASCADE;
DROP TABLE IF EXISTS ato CASCADE;

-- 4. Tabelas de Fluxo Clínico (Nível 2)
DROP TABLE IF EXISTS episodio_urgencia CASCADE;
DROP TABLE IF EXISTS servico_hospitalar CASCADE;
DROP TABLE IF EXISTS utilizador CASCADE;

-- 5. Tabelas Base (Nível 1)
DROP TABLE IF EXISTS role CASCADE;
DROP TABLE IF EXISTS medico CASCADE;
DROP TABLE IF EXISTS enfermeiro CASCADE;
DROP TABLE IF EXISTS funcionario_hospital CASCADE;
DROP TABLE IF EXISTS hospital CASCADE;
DROP TABLE IF EXISTS utente CASCADE;
