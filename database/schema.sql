-- Database Schema for Clinical Management System

-- 1. Base Entities
CREATE TABLE utente ( 
    num_utente INT PRIMARY KEY, 
    nome VARCHAR(255) NOT NULL,
    telemovel VARCHAR(20),
    morada VARCHAR(255),
    sexo VARCHAR(12),
    localidade VARCHAR(100),
    data_nasc DATE 
);

CREATE TABLE hospital (  
    nome_hosp VARCHAR(100) PRIMARY KEY,
    local_hosp VARCHAR(100)
);

CREATE TABLE funcionario_hospital ( 
    num_func INT PRIMARY KEY,
    sexo VARCHAR(10),
    tipo_func VARCHAR(20) -- EX: 'MEDICO', 'ENFERMEIRO', 'RECECIONISTA', 'ADMIN'
);

CREATE TABLE medico ( 
    num_func INT PRIMARY KEY,
    estagiario VARCHAR(10),
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

CREATE TABLE enfermeiro ( 
    num_func INT PRIMARY KEY,
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

-- 2. Auth & Security
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(20) UNIQUE NOT NULL
);

INSERT INTO role (nome) VALUES ('ADMIN'), ('MEDICO'), ('ENFERMEIRO'), ('RECECIONISTA');

CREATE TABLE utilizador (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    num_func INT UNIQUE, -- Link to hospital employee
    id_role INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func),
    FOREIGN KEY (id_role) REFERENCES role(id)
);

-- 3. Clinical Workflow
CREATE TABLE episodio_urgencia (
    cod_epis VARCHAR (50) PRIMARY KEY,
    data_h_entr TIMESTAMP NOT NULL,
    data_h_saida TIMESTAMP, -- Nullable until discharge
    id_utente INT NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_utente) REFERENCES utente (num_utente),
    FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp)
); 

CREATE TABLE triagem (
    id SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    prioridade VARCHAR(20), -- Ex: Manchester Scale
    sintomas TEXT,
    observacoes TEXT,
    data_h_triage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_func_enfermeiro INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (num_func_enfermeiro) REFERENCES enfermeiro(num_func)
);

CREATE TABLE ato ( 
    tipo VARCHAR (50),
    data_h_inicio TIMESTAMP PRIMARY KEY,
    data_h_fim TIMESTAMP NULL,
    cod_epis VARCHAR(50) NOT NULL,
    id_hosp VARCHAR (100) NOT NULL,
    num_func INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp),
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

CREATE TABLE Envolve ( 
    data_h_inicio TIMESTAMP NOT NULL,
    num_func INT NOT NULL,
    cod_epis VARCHAR(50) NOT NULL,
    id_hosp VARCHAR (100) NOT NULL,
    PRIMARY KEY (cod_epis, num_func, data_h_inicio),
    FOREIGN KEY (data_h_inicio) REFERENCES ato(data_h_inicio),
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_hosp) REFERENCES hospital(nome_hosp),
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

CREATE TABLE prescricao (
    id SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    medicamento VARCHAR(200) NOT NULL,
    dosagem VARCHAR(100),
    data_h_presc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_func_medico INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (num_func_medico) REFERENCES medico(num_func)
);

-- 4. Inpatient Workflow
CREATE TABLE servico_hospitalar (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_hosp) REFERENCES hospital(nome_hosp)
);

CREATE TABLE internamento (
    id SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    id_servico INT NOT NULL,
    num_cama INT,
    data_h_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_h_saida TIMESTAMP,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_servico) REFERENCES servico_hospitalar(id)
);

-- 5. Privacy & Anonymization
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    id_utilizador INT NOT NULL,
    tabela_acesso VARCHAR(50) NOT NULL,
    id_registo VARCHAR(50),
    data_h_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acao VARCHAR(20), -- 'SELECT', 'UPDATE', 'DELETE'
    FOREIGN KEY (id_utilizador) REFERENCES utilizador(id)
);

-- Pseudonymized view for analytics
CREATE VIEW utente_analitico AS
SELECT 
    MD5(num_utente::text) as id_anonimo, -- Pseudonymization
    sexo,
    localidade,
    data_nasc
FROM utente;
