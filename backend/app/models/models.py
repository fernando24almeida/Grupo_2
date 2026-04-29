from sqlmodel import SQLModel, Field, Column, String, ForeignKey, Integer, Boolean, DateTime, Text, Date
from typing import Optional, List
from datetime import datetime, date

class PapelUtilizador(SQLModel, table=True):
    __tablename__ = "role"
    id_role: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True)

class Utilizador(SQLModel, table=True):
    __tablename__ = "utilizador"
    id_utilizador: Optional[int] = Field(default=None, primary_key=True)
    nome_utilizador: str = Field(sa_column=Column("username", String, unique=True, index=True))
    nome_completo: str
    email: str = Field(unique=True, index=True)
    telemovel: Optional[str] = None
    hash_palavra_passe: str = Field(sa_column=Column("password_hash", String))
    mfa_secret: Optional[str] = None
    mfa_ativo: bool = Field(default=False)
    num_func: Optional[int] = Field(default=None, foreign_key="funcionario_hospital.num_func")
    id_role: int = Field(foreign_key="role.id_role") # Coincide com o nome físico
    ativo: bool = Field(default=False)

class EmailValidation(SQLModel, table=True):
    __tablename__ = "email_validation"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    codigo: str
    expira_em: datetime
    utilizado: bool = Field(default=False)

class PasswordReset(SQLModel, table=True):
    __tablename__ = "password_reset"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    expira_em: datetime
    utilizado: bool = Field(default=False)

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    id_utilizador: Optional[int] = Field(default=None, foreign_key="utilizador.id_utilizador")
    acao: str
    recurso: str
    id_recurso: Optional[str] = None
    detalhes: Optional[str] = None
    ip_origem: Optional[str] = None
    data_hora: datetime = Field(default_factory=datetime.now)

class Hospital(SQLModel, table=True):
    nome_hosp: str = Field(primary_key=True)
    local_hosp: str

class Utente(SQLModel, table=True):
    num_utente: int = Field(primary_key=True)
    nome: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    telemovel: Optional[str] = Field(default=None, index=True)
    morada: Optional[str] = None
    sexo: Optional[str] = None
    localidade: Optional[str] = None
    data_nascimento: Optional[date] = Field(sa_column=Column("data_nasc", Date, nullable=True))
    password_hash: Optional[str] = None
    ativo: bool = Field(default=False)
    primeiro_acesso: bool = Field(default=True)

class FuncionarioHospital(SQLModel, table=True):
    __tablename__ = "funcionario_hospital"
    num_func: int = Field(primary_key=True)
    sexo: Optional[str] = None
    tipo_func: str

class Medico(SQLModel, table=True):
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")
    estagiario: Optional[str] = None

class Enfermeiro(SQLModel, table=True):
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")

class EpisodioUrgencia(SQLModel, table=True):
    __tablename__ = "episodio_urgencia"
    cod_epis: str = Field(primary_key=True)
    data_h_entrada: datetime = Field(sa_column=Column("data_h_entr", DateTime, nullable=False))
    data_h_saida: Optional[datetime] = None
    id_utente: int = Field(foreign_key="utente.num_utente")
    id_hospital: str = Field(sa_column=Column("id_hosp", String, ForeignKey("hospital.nome_hosp")))
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

class Triagem(SQLModel, table=True):
    num_triagem: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    prioridade: Optional[str] = None
    tensao_arterial: Optional[str] = None
    temperatura: Optional[float] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None
    data_h_triagem: datetime = Field(sa_column=Column("data_h_triage", DateTime, default=datetime.now))
    num_func_enfermeiro: int = Field(foreign_key="enfermeiro.num_func")

class Ato(SQLModel, table=True):
    tipo: str
    data_h_inicio: datetime = Field(primary_key=True)
    data_h_fim: Optional[datetime] = None
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    id_hosp: str = Field(foreign_key="hospital.nome_hosp")
    num_func: int = Field(foreign_key="funcionario_hospital.num_func")

class Envolve(SQLModel, table=True):
    __tablename__ = "Envolve"
    data_h_inicio: datetime = Field(primary_key=True, foreign_key="ato.data_h_inicio")
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")
    cod_epis: str = Field(primary_key=True, foreign_key="episodio_urgencia.cod_epis")
    id_hosp: str = Field(primary_key=True, foreign_key="hospital.nome_hosp")

class Prescricao(SQLModel, table=True):
    num_prescricao: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    medicamento: str
    dosagem: Optional[str] = None
    data_h_presc: datetime = Field(default_factory=datetime.now)
    num_func_medico: int = Field(foreign_key="medico.num_func")

class ServicoHospitalar(SQLModel, table=True):
    __tablename__ = "servico_hospitalar"
    id_servico: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    id_hosp: str = Field(foreign_key="hospital.nome_hosp")

class Internamento(SQLModel, table=True):
    num_internamento: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    id_servico: int = Field(foreign_key="servico_hospitalar.id_servico")
    num_cama: Optional[int] = None
    data_h_entrada: datetime = Field(default_factory=datetime.now)
    data_h_saida: Optional[datetime] = None
