-- ==========================================
-- 1. LIMPEZA TOTAL (DROP)
-- ==========================================
DROP VIEW IF EXISTS utente_analitico CASCADE;
DROP TABLE IF EXISTS auditoria CASCADE;
DROP TABLE IF EXISTS internamento CASCADE;
DROP TABLE IF EXISTS servico_hospitalar CASCADE;
DROP TABLE IF EXISTS prescricao CASCADE;
DROP TABLE IF EXISTS "Envolve" CASCADE;
DROP TABLE IF EXISTS ato CASCADE;
DROP TABLE IF EXISTS triagem CASCADE;
DROP TABLE IF EXISTS episodio_urgencia CASCADE;
DROP TABLE IF EXISTS utilizador CASCADE;
DROP TABLE IF EXISTS role CASCADE;
DROP TABLE IF EXISTS medico CASCADE;
DROP TABLE IF EXISTS enfermeiro CASCADE;
DROP TABLE IF EXISTS funcionario_hospital CASCADE;
DROP TABLE IF EXISTS hospital CASCADE;
DROP TABLE IF EXISTS utente CASCADE;

-- ==========================================
-- 2. ENTIDADES BASE (ORIGINAIS)
-- ==========================================
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
    tipo_func VARCHAR(20)
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

-- ==========================================
-- 3. SEGURANÇA (ORIGINAIS + CAMPOS APP)
-- ==========================================
CREATE TABLE role (
    id_role SERIAL PRIMARY KEY,
    nome VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE utilizador (
    id_utilizador SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Campo extra para App
    num_func INT UNIQUE,
    id_role INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func),
    FOREIGN KEY (id_role) REFERENCES role(id_role)
);

-- ==========================================
-- 4. FLUXO CLÍNICO (ORIGINAIS + CAMPOS APP)
-- ==========================================
CREATE TABLE episodio_urgencia (
    cod_epis VARCHAR(50) PRIMARY KEY,
    data_h_entr TIMESTAMP NOT NULL,
    data_h_saida TIMESTAMP,
    id_utente INT NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    sintomas TEXT, -- Campo extra para App
    observacoes TEXT, -- Campo extra para App
    FOREIGN KEY (id_utente) REFERENCES utente (num_utente),
    FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp)
); 

CREATE TABLE triagem (
    num_triagem SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    prioridade VARCHAR(20),
    sintomas TEXT,
    observacoes TEXT,
    data_h_triage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_func_enfermeiro INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (num_func_enfermeiro) REFERENCES enfermeiro(num_func)
);

CREATE TABLE ato ( 
    tipo VARCHAR(50),
    data_h_inicio TIMESTAMP PRIMARY KEY, -- Chave original
    data_h_fim TIMESTAMP NULL,
    cod_epis VARCHAR(50) NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    num_func INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp),
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

-- Relacionamento N:M Original
CREATE TABLE "Envolve" ( 
    data_h_inicio TIMESTAMP NOT NULL,
    num_func INT NOT NULL,
    cod_epis VARCHAR(50) NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    PRIMARY KEY (cod_epis, num_func, data_h_inicio),
    FOREIGN KEY (data_h_inicio) REFERENCES ato(data_h_inicio),
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_hosp) REFERENCES hospital(nome_hosp),
    FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func)
);

CREATE TABLE prescricao (
    num_prescricao SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    medicamento VARCHAR(200) NOT NULL,
    dosagem VARCHAR(100),
    data_h_presc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_func_medico INT NOT NULL,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (num_func_medico) REFERENCES medico(num_func)
);

-- ==========================================
-- 5. INTERNAMENTO E AUDITORIA (ORIGINAIS)
-- ==========================================
CREATE TABLE servico_hospitalar (
    id_servico SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    id_hosp VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_hosp) REFERENCES hospital(nome_hosp)
);

CREATE TABLE internamento (
    num_internamento SERIAL PRIMARY KEY,
    cod_epis VARCHAR(50) NOT NULL,
    id_servico INT NOT NULL,
    num_cama INT,
    data_h_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_h_saida TIMESTAMP,
    FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
    FOREIGN KEY (id_servico) REFERENCES servico_hospitalar(id_servico)
);

CREATE TABLE auditoria (
    num_auditoria SERIAL PRIMARY KEY,
    id_utilizador INT NOT NULL,
    tabela_acesso VARCHAR(50) NOT NULL,
    id_registo VARCHAR(50),
    data_h_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acao VARCHAR(20),
    FOREIGN KEY (id_utilizador) REFERENCES utilizador(id_utilizador)
);

-- ==========================================
-- 6. VISTAS ANALÍTICAS (ORIGINAL)
-- ==========================================
CREATE VIEW utente_analitico AS
SELECT 
    MD5(num_utente::text) as id_anonimo,
    sexo,
    localidade,
    data_nasc -- Mantido conforme original
FROM utente;

-- ==========================================
-- 7. DADOS INICIAIS
-- ==========================================
INSERT INTO role (nome) VALUES ('ADMIN'), ('MEDICO'), ('ENFERMEIRO'), ('RECECIONISTA');
INSERT INTO hospital (nome_hosp, local_hosp) VALUES ('Hospital Central de Urgências', 'Lisboa');
INSERT INTO funcionario_hospital (num_func, sexo, tipo_func) VALUES (1, 'M', 'ADMIN');
INSERT INTO utilizador (username, password_hash, num_func, id_role, ativo) 
VALUES ('admin', '$2b$12$iQbr53Cb/HNKypqfoD4cVOdB6MNqcXvRL/KRL/Vw6KGCY6xsYOZFO', 1, 1, TRUE);
