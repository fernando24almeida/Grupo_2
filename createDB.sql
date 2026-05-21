CREATE TABLE utente ( 
	num_utente INT PRIMARY KEY, 
	sexo VARCHAR(12),
	localidade VARCHAR(100),
	idade_atual INT 
);

CREATE TABLE hospital (  
	nome_hosp VARCHAR(100) PRIMARY KEY,
	local_hosp VARCHAR(100)
);

CREATE TABLE episodio_urgencia (
	cod_epis VARCHAR (50) PRIMARY KEY,
	data_h_entr TIMESTAMP NOT NULL,
	data_h_saida TIMESTAMP NOT NULL,
	id_utente INT NOT NULL,
	id_hosp VARCHAR(100) NOT NULL
); 

CREATE TABLE ato ( 
	id_ato SERIAL PRIMARY KEY,
	tipo VARCHAR (50),
	data_h_inicio TIMESTAMP NOT NULL,
	data_h_fim TIMESTAMP NULL,
	cod_epis VARCHAR(50) NOT NULL,
	id_hosp VARCHAR (100) NOT NULL,
	num_func INT NOT NULL  
);

CREATE TABLE Envolve ( 
	id_ato INT NOT NULL,
	num_func INT NOT NULL,
	PRIMARY KEY (id_ato, num_func)
);

CREATE TABLE funcionario_hospital ( 
	num_func INT PRIMARY KEY,
	sexo VARCHAR(10),
	tipo_func VARCHAR(20) 
);

CREATE TABLE medico ( 
	num_func INT PRIMARY KEY,
	estagiario VARCHAR(10)
);

CREATE TABLE enfermeiro ( 
	num_func INT PRIMARY KEY
);

ALTER TABLE episodio_urgencia
ADD FOREIGN KEY (id_utente) REFERENCES utente (num_utente),
ADD FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp);

ALTER TABLE ato
ADD FOREIGN KEY (cod_epis) REFERENCES episodio_urgencia(cod_epis),
ADD FOREIGN KEY (id_hosp) REFERENCES hospital (nome_hosp),
ADD FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func);

ALTER TABLE Envolve
ADD FOREIGN KEY (id_ato) REFERENCES ato(id_ato),
ADD FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func);

ALTER TABLE medico
ADD FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func);

ALTER TABLE enfermeiro
ADD FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func);