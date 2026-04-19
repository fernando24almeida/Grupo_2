from __future__ import annotations

import random
from datetime import datetime, timedelta, date
from typing import List

from faker import Faker
from sqlmodel import Session, create_engine, select, SQLModel
from passlib.context import CryptContext

from app.models.models import (
    PapelUtilizador,
    Utilizador,
    Hospital,
    FuncionarioHospital,
    Medico,
    Enfermeiro,
    Utente,
    EpisodioUrgencia,
    Triagem,
    Ato,
    Envolve,
    Prescricao,
    ServicoHospitalar,
    Internamento,
)

DATABASE_URL = "postgresql://postgres:123456@localhost:5432/urgencias_g2"

SEED = 42
TOTAL_UTENTES = 1000
TOTAL_FUNCIONARIOS = 120
TOTAL_MEDICOS = 45
TOTAL_ENFERMEIROS = 45
TOTAL_UTILIZADORES = 100
TOTAL_EPISODIOS = 1200
TOTAL_ATOS = 2200
TOTAL_PRESCRICOES = 900
TOTAL_INTERNAMENTOS = 180

fake = Faker("pt_PT")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def configurar_seed(seed: int = SEED) -> None:
    random.seed(seed)
    Faker.seed(seed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def escolher(seq):
    return random.choice(seq)


def chance(prob: float) -> bool:
    return random.random() < prob


def codigo(prefixo: str, n: int, width: int = 5) -> str:
    return f"{prefixo}{n:0{width}d}"


def gerar_telemovel() -> str:
    return f"9{random.randint(10_000_000, 99_999_999)}"


def gerar_data_nascimento(min_age: int = 0, max_age: int = 95) -> date:
    hoje = date.today()
    idade = random.randint(min_age, max_age)
    dias_extra = random.randint(0, 364)
    return hoje - timedelta(days=idade * 365 + dias_extra)


def criar_roles(sessao: Session) -> dict[str, int]:
    existentes = {
        r.nome: r.id_role for r in sessao.exec(select(PapelUtilizador)).all()
    }

    nomes = ["ADMIN", "MEDICO", "ENFERMEIRO", "RECECIONISTA"]
    for nome in nomes:
        if nome not in existentes:
            role = PapelUtilizador(nome=nome)
            sessao.add(role)
            sessao.commit()
            sessao.refresh(role)
            existentes[nome] = role.id_role

    return existentes


def criar_hospitais(sessao: Session) -> List[str]:
    hospitais = [
        ("Hospital Central de Urgências", "Lisboa"),
        ("Hospital São João de Emergência", "Porto"),
        ("Hospital de Atendimento Rápido", "Coimbra"),
    ]

    ids = []
    for nome, local in hospitais:
        existente = sessao.get(Hospital, nome)
        if not existente:
            sessao.add(Hospital(nome_hosp=nome, local_hosp=local))
        ids.append(nome)

    sessao.commit()
    return ids


def criar_servicos(sessao: Session, hospitais: List[str]) -> List[int]:
    servicos_base = [
        "Medicina Interna",
        "Cirurgia",
        "Ortopedia",
        "Pediatria",
        "Neurologia",
        "Cardiologia",
    ]

    ids = []
    for hosp in hospitais:
        for nome in servicos_base:
            servico = ServicoHospitalar(nome=nome, id_hosp=hosp)
            sessao.add(servico)
            sessao.commit()
            sessao.refresh(servico)
            ids.append(servico.id_servico)
    return ids


def criar_funcionarios(sessao: Session):
    existentes = set(sessao.exec(select(FuncionarioHospital.num_func)).all())

    numeros = []
    proximo = 1000

    while len(numeros) < TOTAL_FUNCIONARIOS:
        if proximo not in existentes:
            numeros.append(proximo)
        proximo += 1

    medicos = set(random.sample(numeros, TOTAL_MEDICOS))

    restantes = [n for n in numeros if n not in medicos]

    enfermeiros = set(random.sample(restantes, TOTAL_ENFERMEIROS))

    for num in numeros:

        if num in medicos:
            tipo = "MEDICO"

        elif num in enfermeiros:
            tipo = "ENFERMEIRO"

        else:
            tipo = "RECECIONISTA"

        sessao.add(
            FuncionarioHospital(
                num_func=num,
                sexo=random.choice(["M", "F"]),
                tipo_func=tipo
            )
        )

    sessao.commit()

    for num in medicos:
        sessao.add(Medico(num_func=num, estagiario=random.choice(["S", "N"])))

    for num in enfermeiros:
        sessao.add(Enfermeiro(num_func=num))

    sessao.commit()

    return sorted(numeros), sorted(medicos), sorted(enfermeiros)


def criar_utilizadores(
    sessao: Session,
    role_ids: dict[str, int],
    funcionarios: List[int],
    medicos: List[int],
    enfermeiros: List[int],
) -> None:
    existentes = {
        u.nome_utilizador for u in sessao.exec(select(Utilizador)).all()
    }

    if "admin" not in existentes:
        admin = Utilizador(
            nome_utilizador="admin",
            nome_completo="Administrador do Sistema",
            email="admin@portalclinico.pt",
            hash_palavra_passe=hash_password("admin123"),
            num_func=funcionarios[0],
            id_role=role_ids["ADMIN"],
            ativo=True,
            mfa_secret=None,
            mfa_ativo=False,
        )
        sessao.add(admin)
        sessao.commit()

    candidatos = funcionarios[1:TOTAL_UTILIZADORES + 1]

    for idx, num_func in enumerate(candidatos, start=1):
        username = f"user{idx:03d}"
        if username in existentes:
            continue

        nome = fake.name()
        email = f"{username}@hospital.pt"

        if num_func in medicos:
            role_id = role_ids["MEDICO"]
        elif num_func in enfermeiros:
            role_id = role_ids["ENFERMEIRO"]
        else:
            role_id = role_ids["RECECIONISTA"]

        utilizador = Utilizador(
            nome_utilizador=username,
            nome_completo=nome,
            email=email,
            hash_palavra_passe=hash_password("admin123"),
            num_func=num_func,
            id_role=role_id,
            ativo=chance(0.92),
            mfa_secret=None,
            mfa_ativo=False,
        )
        sessao.add(utilizador)

    sessao.commit()


def criar_utentes(sessao: Session) -> List[int]:
    existentes = set(sessao.exec(select(Utente.num_utente)).all())
    ids = []

    atual = 200000000
    while len(ids) < TOTAL_UTENTES:
        if atual not in existentes:
            ids.append(atual)
        atual += 1

    for num in ids:
        sexo = escolher(["M", "F"])
        utente = Utente(
            num_utente=num,
            nome=fake.name_male() if sexo == "M" else fake.name_female(),
            telemovel=gerar_telemovel(),
            morada=fake.address().replace("\n", ", "),
            sexo=sexo,
            localidade=fake.city(),
            data_nascimento=gerar_data_nascimento(0, 95),
        )
        sessao.add(utente)

    sessao.commit()
    return ids


def criar_episodios(sessao: Session, utentes: List[int], hospitais: List[str]) -> List[tuple[str, str]]:
    sintomas_pool = [
        "Dor torácica", "Febre", "Falta de ar", "Dor abdominal", "Tonturas",
        "Náuseas", "Traumatismo", "Dor de cabeça", "Queda", "Palpitações",
    ]
    observacoes_pool = [
        "Encaminhado para observação",
        "Sem alergias conhecidas",
        "Utente estável à entrada",
        "Necessita avaliação médica",
        "Sintomas com 24h de evolução",
    ]

    episodios = []
    base = datetime.now() - timedelta(days=180)

    codigos_existentes = sessao.exec(select(EpisodioUrgencia.cod_epis)).all()

    ultimo_num = 0
    for cod in codigos_existentes:
        if cod and isinstance(cod, str) and cod.startswith("EP"):
            try:
                numero = int(cod[2:])
                if numero > ultimo_num:
                    ultimo_num = numero
            except ValueError:
                pass

    for i in range(ultimo_num + 1, ultimo_num + TOTAL_EPISODIOS + 1):
        cod = codigo("EP", i, 6)

        entrada = base + timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        com_alta = chance(0.75)
        saida = entrada + timedelta(hours=random.randint(1, 72)) if com_alta else None

        hosp = escolher(hospitais)

        episodio = EpisodioUrgencia(
            cod_epis=cod,
            data_h_entrada=entrada,
            data_h_saida=saida,
            id_utente=escolher(utentes),
            id_hospital=hosp,
            sintomas=escolher(sintomas_pool),
            observacoes=escolher(observacoes_pool),
        )

        sessao.add(episodio)
        episodios.append((cod, hosp))

    sessao.commit()
    return episodios


def criar_triagens(
    sessao: Session,
    episodios: List[tuple[str, str]],
    enfermeiros: List[int],
) -> None:
    prioridades = ["AZUL", "VERDE", "AMARELO", "LARANJA", "VERMELHO"]

    for cod_epis, _ in episodios:
        triagem = Triagem(
            cod_epis=cod_epis,
            prioridade=escolher(prioridades),
            sintomas=fake.sentence(nb_words=6),
            observacoes=fake.sentence(nb_words=10),
            data_h_triagem=datetime.now() - timedelta(days=random.randint(0, 180)),
            num_func_enfermeiro=escolher(enfermeiros),
        )
        sessao.add(triagem)

    sessao.commit()


def criar_atos(
    sessao: Session,
    episodios: List[tuple[str, str]],
    funcionarios: List[int],
) -> None:
    tipos = [
        "Observação", "Medicação", "Sutura", "Raio-X", "Eletrocardiograma",
        "Análises", "Avaliação médica", "Imobilização", "Curativo",
    ]

    for _ in range(TOTAL_ATOS):
        cod_epis, hosp = escolher(episodios)
        inicio = datetime.now() - timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
            microseconds=random.randint(0, 999999),
        )
        fim = inicio + timedelta(minutes=random.randint(10, 180))
        num_func = escolher(funcionarios)

        ato = Ato(
            tipo=escolher(tipos),
            data_h_inicio=inicio,
            data_h_fim=fim,
            cod_epis=cod_epis,
            id_hosp=hosp,
            num_func=num_func,
        )
        sessao.add(ato)
        sessao.commit()

        sessao.add(
            Envolve(
                data_h_inicio=ato.data_h_inicio,
                num_func=num_func,
                cod_epis=cod_epis,
                id_hosp=hosp,
            )
        )
        sessao.commit()


def criar_prescricoes(
    sessao: Session,
    episodios: List[tuple[str, str]],
    medicos: List[int],
) -> None:
    medicamentos = [
        "Paracetamol", "Ibuprofeno", "Amoxicilina", "Omeprazol",
        "Metformina", "Atorvastatina", "Salbutamol", "Diazepam",
    ]
    dosagens = ["500mg", "1g", "20mg", "40mg", "10ml", "2 comprimidos"]

    for _ in range(TOTAL_PRESCRICOES):
        cod_epis, _ = escolher(episodios)
        presc = Prescricao(
            cod_epis=cod_epis,
            medicamento=escolher(medicamentos),
            dosagem=escolher(dosagens),
            data_h_presc=datetime.now() - timedelta(days=random.randint(0, 180)),
            num_func_medico=escolher(medicos),
        )
        sessao.add(presc)

    sessao.commit()


def criar_internamentos(
    sessao: Session,
    episodios: List[tuple[str, str]],
    servicos: List[int],
) -> None:
    escolhidos = random.sample(episodios, min(TOTAL_INTERNAMENTOS, len(episodios)))

    for cod_epis, _ in escolhidos:
        entrada = datetime.now() - timedelta(days=random.randint(0, 120))
        saida = entrada + timedelta(days=random.randint(1, 12)) if chance(0.7) else None

        intern = Internamento(
            cod_epis=cod_epis,
            id_servico=escolher(servicos),
            num_cama=random.randint(1, 60),
            data_h_entrada=entrada,
            data_h_saida=saida,
        )
        sessao.add(intern)

    sessao.commit()


def main() -> None:
    configurar_seed()
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Criar tabelas se não existirem
    SQLModel.metadata.create_all(engine)

    with Session(engine) as sessao:
        role_ids = criar_roles(sessao)
        hospitais = criar_hospitais(sessao)
        servicos = criar_servicos(sessao, hospitais)
        funcionarios, medicos, enfermeiros = criar_funcionarios(sessao)
        criar_utilizadores(sessao, role_ids, funcionarios, medicos, enfermeiros)
        utentes = criar_utentes(sessao)
        episodios = criar_episodios(sessao, utentes, hospitais)
        criar_triagens(sessao, episodios, enfermeiros)
        criar_atos(sessao, episodios, funcionarios)
        criar_prescricoes(sessao, episodios, medicos)
        criar_internamentos(sessao, episodios, servicos)

    print("Seed concluído com sucesso.")
    print("Login admin:")
    print("  username: admin")
    print("  password: admin123")


if __name__ == "__main__":
    main()