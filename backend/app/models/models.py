from sqlmodel import SQLModel, Field, Column, String, ForeignKey, Integer, Boolean, DateTime, Text, Date
from typing import Optional, List
from datetime import datetime, date, timezone
from pydantic import ConfigDict

# =============================================================================
# MODELOS DE DADOS (ESTRUTURA DA BASE DE DADOS)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro define as "plantas" ou "moldes" de todas as tabelas que 
# existem na nossa base de dados. Cada classe aqui representa uma tabela 
# real no PostgreSQL. É aqui que dizemos o que cada coisa guarda (nomes, 
# números, datas) e como elas se ligam umas às outras.
# =============================================================================

class PapelUtilizador(SQLModel, table=True):
    """ Define os cargos (Admin, Médico, etc.) para sabermos quem pode fazer o quê. """
    __tablename__ = "role"
    id_role: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True)

class Utilizador(SQLModel, table=True):
    """ Contas de acesso dos funcionários (Staff) ao Portal Web. """
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
    id_role: int = Field(foreign_key="role.id_role")
    ativo: bool = Field(default=False)
    role_name: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")

class EmailValidation(SQLModel, table=True):
    """ Guarda os códigos de 6 dígitos que enviamos por e-mail para ativar contas. """
    __tablename__ = "email_validation"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    codigo: str
    expira_em: datetime
    utilizado: bool = Field(default=False)

class PasswordReset(SQLModel, table=True):
    """ Tokens temporários para quando alguém se esquece da password. """
    __tablename__ = "password_reset"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    expira_em: datetime
    utilizado: bool = Field(default=False)

class AuditLog(SQLModel, table=True):
    """ A 'caixa negra' do sistema. Regista tudo o que é importante por segurança. """
    __tablename__ = "audit_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    id_utilizador: Optional[int] = Field(default=None, foreign_key="utilizador.id_utilizador")
    acao: str # Ex: 'LOGIN', 'CRIAR_UTENTE'
    recurso: str # Ex: 'utente'
    id_recurso: Optional[str] = None
    detalhes: Optional[str] = None
    ip_origem: Optional[str] = None
    data_hora: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Hospital(SQLModel, table=True):
    """ Unidades hospitalares registadas no nosso sistema. """
    nome_hosp: str = Field(primary_key=True)
    local_hosp: str

class Utente(SQLModel, table=True):
    """ Dados biográficos e de acesso dos pacientes (App Mobile). """
    num_utente: int = Field(primary_key=True)
    nome: str = Field(index=True)
    email: str = Field(index=True)
    telemovel: Optional[str] = Field(default=None, index=True)
    morada: Optional[str] = None
    sexo: Optional[str] = None
    localidade: Optional[str] = None
    data_nascimento: Optional[date] = Field(sa_column=Column("data_nasc", Date, nullable=True))
    password_hash: Optional[str] = None
    ativo: bool = Field(default=False)
    primeiro_acesso: bool = Field(default=True)
    parentesco: Optional[str] = None
    id_role: Optional[int] = Field(default=None, foreign_key="role.id_role")
    role_name: Optional[str] = None

    model_config = ConfigDict(extra="allow")

class FuncionarioHospital(SQLModel, table=True):
    """ Registo base de qualquer pessoa que trabalhe no hospital. """
    __tablename__ = "funcionario_hospital"
    num_func: int = Field(primary_key=True)
    sexo: Optional[str] = None
    tipo_func: str # Ex: 'MEDICO', 'ENFERMEIRO'

class Medico(SQLModel, table=True):
    """ Dados específicos para médicos (especialidade, se é estagiário). """
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")
    estagiario: Optional[str] = None
    especialidade: Optional[str] = None

class Enfermeiro(SQLModel, table=True):
    """ Simplesmente identifica que aquele funcionário é enfermeiro. """
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")

class EpisodioUrgencia(SQLModel, table=True):
    """ 
    O registo mais importante: Representa a visita de um utente à urgência. 
    Contém a hora de entrada, saída e sintomas iniciais.
    """
    __tablename__ = "episodio_urgencia"
    cod_epis: str = Field(primary_key=True)
    data_h_entrada: datetime = Field(sa_column=Column("data_h_entr", DateTime, nullable=False))
    data_h_saida: Optional[datetime] = None
    id_utente: int = Field(foreign_key="utente.num_utente")
    id_hospital: str = Field(sa_column=Column("id_hosp", String, ForeignKey("hospital.nome_hosp")))
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None
    id_utilizador_rececao: Optional[int] = Field(default=None, foreign_key="utilizador.id_utilizador")

class Triagem(SQLModel, table=True):
    """ Avaliação de sinais vitais e cor de prioridade (Manchester). """
    num_triagem: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    prioridade: Optional[str] = None # VERMELHO, LARANJA...
    tensao_arterial: Optional[str] = None
    temperatura: Optional[float] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None
    data_h_triagem: datetime = Field(sa_column=Column("data_h_triage", DateTime, default=lambda: datetime.now(timezone.utc)))
    num_func_enfermeiro: int = Field(foreign_key="enfermeiro.num_func")

class Ato(SQLModel, table=True):
    """ Registo de uma consulta ou exame médico durante o episódio. """
    id_ato: Optional[int] = Field(default=None, primary_key=True)
    tipo: str # Ex: 'CONSULTA'
    data_h_inicio: datetime = Field(index=True)
    data_h_fim: Optional[datetime] = None
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    id_hosp: str = Field(foreign_key="hospital.nome_hosp")
    num_func: int = Field(foreign_key="funcionario_hospital.num_func")
    diagnostico: Optional[str] = None
    notas_clinicas: Optional[str] = None
    exame_fisico: Optional[str] = None
    decisao_clinica: Optional[str] = None

class Envolve(SQLModel, table=True):
    """ Tabela de ligação para quando vários médicos colaboram no mesmo ato. """
    __tablename__ = "Envolve"
    id_ato: int = Field(primary_key=True, foreign_key="ato.id_ato")
    num_func: int = Field(primary_key=True, foreign_key="funcionario_hospital.num_func")

class Prescricao(SQLModel, table=True):
    """ Receita de medicamentos passada pelo médico. """
    num_prescricao: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    medicamento: str
    dosagem: Optional[str] = None
    data_h_presc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    num_func_medico: int = Field(foreign_key="medico.num_func")

class ServicoHospitalar(SQLModel, table=True):
    """ Alas do hospital (ex: 'Cardiologia') onde as pessoas ficam internadas. """
    __tablename__ = "servico_hospitalar"
    id_servico: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    id_hosp: str = Field(foreign_key="hospital.nome_hosp")

class Internamento(SQLModel, table=True):
    """ Registo de quando um doente sai da urgência e fica a dormir no hospital. """
    num_internamento: Optional[int] = Field(default=None, primary_key=True)
    cod_epis: str = Field(foreign_key="episodio_urgencia.cod_epis")
    id_servico: int = Field(foreign_key="servico_hospitalar.id_servico")
    num_cama: Optional[int] = None
    data_h_entrada: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_h_saida: Optional[datetime] = None
    num_func_medico: Optional[int] = Field(default=None, foreign_key="medico.num_func")
