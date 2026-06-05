-- =============================================================================
-- ESQUEMA DE BASE DE DADOS - SISTEMA DE GESTÃO CLÍNICA G2
-- Arquitetura atualizada baseada nos modelos SQLModel do Backend
-- =============================================================================

-- 1. LIMPEZA TOTAL
DROP TABLE IF EXISTS internamento CASCADE;
DROP TABLE IF EXISTS servico_hospitalar CASCADE;
DROP TABLE IF EXISTS prescricao CASCADE;
DROP TABLE IF EXISTS "Envolve" CASCADE;
DROP TABLE IF EXISTS ato CASCADE;
DROP TABLE IF EXISTS triagem CASCADE;
DROP TABLE IF EXISTS episodio_urgencia CASCADE;
DROP TABLE IF EXISTS medico CASCADE;
DROP TABLE IF EXISTS enfermeiro CASCADE;
DROP TABLE IF EXISTS funcionario_hospital CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS password_reset CASCADE;
DROP TABLE IF EXISTS email_validation CASCADE;
DROP TABLE IF EXISTS utilizador CASCADE;
DROP TABLE IF EXISTS utente CASCADE;
DROP TABLE IF EXISTS hospital CASCADE;
DROP TABLE IF EXISTS role CASCADE;

-- 2. TABELAS DE APOIO E SEGURANÇA
CREATE TABLE role (
    id_role SERIAL PRIMARY KEY,
    nome VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE hospital (
    nome_hosp VARCHAR(255) PRIMARY KEY,
    local_hosp VARCHAR(255) NOT NULL
);

CREATE TABLE utente (
    num_utente INT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    telemovel VARCHAR(255),
    morada VARCHAR(255),
    sexo VARCHAR(255),
    localidade VARCHAR(255),
    data_nasc DATE,
    password_hash VARCHAR(255),
    ativo BOOLEAN DEFAULT FALSE,
    primeiro_acesso BOOLEAN DEFAULT TRUE,
    parentesco VARCHAR(255),
    id_role INT REFERENCES role(id_role),
    role_name VARCHAR(255)
);

CREATE TABLE funcionario_hospital (
    num_func INT PRIMARY KEY,
    sexo VARCHAR(255),
    tipo_func VARCHAR(255) NOT NULL
);

CREATE TABLE utilizador (
    id_utilizador SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telemovel VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    mfa_secret VARCHAR(255),
    mfa_ativo BOOLEAN DEFAULT FALSE,
    num_func INT UNIQUE REFERENCES funcionario_hospital(num_func),
    id_role INT NOT NULL REFERENCES role(id_role),
    ativo BOOLEAN DEFAULT FALSE,
    role_name VARCHAR(255)
);

CREATE TABLE email_validation (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    codigo VARCHAR(255) NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    utilizado BOOLEAN DEFAULT FALSE
);

CREATE TABLE password_reset (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    utilizado BOOLEAN DEFAULT FALSE
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    id_utilizador INT REFERENCES utilizador(id_utilizador),
    acao VARCHAR(255) NOT NULL,
    recurso VARCHAR(255) NOT NULL,
    id_recurso VARCHAR(255),
    detalhes TEXT,
    ip_origem VARCHAR(255),
    data_hora TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc')
);

-- 3. ESPECIALIZAÇÕES DE PROFISSIONAIS
CREATE TABLE medico (
    num_func INT PRIMARY KEY REFERENCES funcionario_hospital(num_func),
    estagiario VARCHAR(255),
    especialidade VARCHAR(255)
);

CREATE TABLE enfermeiro (
    num_func INT PRIMARY KEY REFERENCES funcionario_hospital(num_func)
);

-- 4. FLUXO CLÍNICO
CREATE TABLE episodio_urgencia (
    cod_epis VARCHAR(255) PRIMARY KEY,
    data_h_entr TIMESTAMP NOT NULL,
    data_h_saida TIMESTAMP,
    id_utente INT NOT NULL REFERENCES utente(num_utente),
    id_hosp VARCHAR(255) NOT NULL REFERENCES hospital(nome_hosp),
    sintomas TEXT,
    observacoes TEXT,
    id_utilizador_rececao INT REFERENCES utilizador(id_utilizador)
);

CREATE TABLE triagem (
    num_triagem SERIAL PRIMARY KEY,
    cod_epis VARCHAR(255) NOT NULL REFERENCES episodio_urgencia(cod_epis),
    prioridade VARCHAR(255),
    tensao_arterial VARCHAR(255),
    temperatura FLOAT,
    sintomas TEXT,
    observacoes TEXT,
    data_h_triage TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
    num_func_enfermeiro INT NOT NULL REFERENCES enfermeiro(num_func)
);

CREATE TABLE ato (
    id_ato SERIAL PRIMARY KEY,
    tipo VARCHAR(255) NOT NULL,
    data_h_inicio TIMESTAMP NOT NULL,
    data_h_fim TIMESTAMP,
    cod_epis VARCHAR(255) NOT NULL REFERENCES episodio_urgencia(cod_epis),
    id_hosp VARCHAR(255) NOT NULL REFERENCES hospital(nome_hosp),
    num_func INT NOT NULL REFERENCES funcionario_hospital(num_func),
    diagnostico TEXT,
    notas_clinicas TEXT,
    exame_fisico TEXT,
    decisao_clinica VARCHAR(255)
);

CREATE TABLE "Envolve" (
    id_ato INT NOT NULL REFERENCES ato(id_ato),
    num_func INT NOT NULL REFERENCES funcionario_hospital(num_func),
    PRIMARY KEY (id_ato, num_func)
);

CREATE TABLE prescricao (
    num_prescricao SERIAL PRIMARY KEY,
    cod_epis VARCHAR(255) NOT NULL REFERENCES episodio_urgencia(cod_epis),
    medicamento VARCHAR(255) NOT NULL,
    dosagem VARCHAR(255),
    data_h_presc TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
    num_func_medico INT NOT NULL REFERENCES medico(num_func)
);

-- 5. INTERNAMENTO
CREATE TABLE servico_hospitalar (
    id_servico SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    id_hosp VARCHAR(255) NOT NULL REFERENCES hospital(nome_hosp)
);

CREATE TABLE internamento (
    num_internamento SERIAL PRIMARY KEY,
    cod_epis VARCHAR(255) NOT NULL REFERENCES episodio_urgencia(cod_epis),
    id_servico INT NOT NULL REFERENCES servico_hospitalar(id_servico),
    num_cama INT,
    data_h_entrada TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
    data_h_saida TIMESTAMP,
    num_func_medico INT REFERENCES medico(num_func)
);

-- 6. DADOS INICIAIS
INSERT INTO role (nome) VALUES ('ADMIN'), ('MEDICO'), ('ENFERMEIRO'), ('RECECIONISTA'), ('UTENTE');
INSERT INTO hospital (nome_hosp, local_hosp) VALUES ('Hospital Central de Urgências', 'Lisboa');
