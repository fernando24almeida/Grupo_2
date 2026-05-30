import random
from datetime import datetime, timedelta, timezone, date
from typing import Optional, List
from sqlmodel import Session, select
from ..models.models import (
    EpisodioUrgencia,
    Triagem,
    Ato,
    Internamento,
    Utente,
    Hospital,
    Enfermeiro,
    Medico,
    ServicoHospitalar,
    FuncionarioHospital,
    Utilizador
)

def get_next_cod_epis(session: Session) -> int:
    codigos = session.exec(select(EpisodioUrgencia.cod_epis)).all()
    ultimo_num = 0
    for cod in codigos:
        if cod.startswith("EP"):
            try:
                num = int(cod[2:])
                if num > ultimo_num:
                    ultimo_num = num
            except ValueError:
                continue
    return ultimo_num + 1

def seed_episodes_today(session: Session, hospital_name: Optional[str] = None):
    # 1. Carregar dados base
    utentes = session.exec(select(Utente)).all()
    
    if hospital_name:
        hospitais = session.exec(select(Hospital).where(Hospital.nome_hosp == hospital_name)).all()
    else:
        hospitais = session.exec(select(Hospital)).all()
        
    # Obter profissionais por tipo
    # Enfermeiros
    enfermeiros = session.exec(select(Enfermeiro)).all()
    # Médicos
    medicos = session.exec(select(Medico)).all()
    # Rececionistas (Utilizadores vinculados a funcionários do tipo RECECIONISTA)
    rececionistas = session.exec(
        select(Utilizador).join(FuncionarioHospital, Utilizador.num_func == FuncionarioHospital.num_func)
        .where(FuncionarioHospital.tipo_func == "RECECIONISTA")
    ).all()
    
    # Se não houver rececionistas vinculados, tentar obter utilizadores com role de rececionista
    if not rececionistas:
        rececionistas = session.exec(select(Utilizador).where(Utilizador.role_name == "RECECIONISTA")).all()

    servicos = session.exec(select(ServicoHospitalar)).all()

    if not all([utentes, hospitais, enfermeiros, medicos, rececionistas, servicos]):
        raise Exception(f"Dados base insuficientes para simulação (verifique se existem Utentes, Hospitais, Enfermeiros, Médicos, Rececionistas e Serviços).")

    agora = datetime.now(timezone.utc)
    hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    prioridades = ["AZUL", "VERDE", "AMARELO", "LARANJA", "VERMELHO"]
    sintomas_pool = ["Febre", "Dor Abdominal", "Cefaleia", "Dispneia", "Traumatismo", "Vómitos", "Tosse"]
    
    next_num = get_next_cod_epis(session)
    
    for i in range(200):
        cod_epis = f"EP{next_num + i:06d}"
        hosp = random.choice(hospitais)
        utente = random.choice(utentes)
        recep = random.choice(rececionistas)
        
        # Determinar estado do episódio
        if i < 5: # EM ESPERA PARA TRIAGEM
            data_entrada = agora - timedelta(minutes=random.randint(5, 20))
            status = "ESPERA_TRIAGEM"
        elif i < 9: # EM ESPERA PARA CONSULTA
            data_entrada = agora - timedelta(minutes=random.randint(40, 90))
            status = "ESPERA_CONSULTA"
        elif i < 14: # INTERNAMENTO ATIVO
            data_entrada = agora - timedelta(minutes=random.randint(120, 300))
            status = "INTERNAMENTO_ATIVO"
        else: # RESTANTES (FECHADOS)
            segundos_no_dia = (agora - hoje_inicio).total_seconds()
            random_sec = random.randint(0, int(segundos_no_dia) - 3600)
            data_entrada = hoje_inicio + timedelta(seconds=random_sec)
            status = "FECHADO"

        # Criar Episódio
        episodio = EpisodioUrgencia(
            cod_epis=cod_epis,
            data_h_entrada=data_entrada,
            id_utente=utente.num_utente,
            id_hospital=hosp.nome_hosp,
            sintomas=random.choice(sintomas_pool),
            observacoes=f"Simulação: {status} ({hosp.nome_hosp})",
            id_utilizador_rececao=recep.id_utilizador # ATRIBUIÇÃO DO RECECIONISTA
        )
        session.add(episodio)
        session.flush()
        
        # Triagem
        if status != "ESPERA_TRIAGEM":
            data_triagem = data_entrada + timedelta(minutes=random.randint(5, 15))
            enf = random.choice(enfermeiros)
            triagem = Triagem(
                cod_epis=cod_epis,
                prioridade=random.choice(prioridades),
                sintomas=episodio.sintomas,
                data_h_triagem=data_triagem,
                num_func_enfermeiro=enf.num_func # ATRIBUIÇÃO DO ENFERMEIRO
            )
            session.add(triagem)
            
            # Ato Médico
            if status != "ESPERA_CONSULTA":
                data_ato_inicio = data_triagem + timedelta(minutes=random.randint(20, 60))
                data_ato_fim = data_ato_inicio + timedelta(minutes=random.randint(15, 45))
                
                e_internamento = (status == "INTERNAMENTO_ATIVO") or (status == "FECHADO" and i < 54)
                decisao = "Internamento" if e_internamento else "Alta"
                
                med = random.choice(medicos)
                ato = Ato(
                    tipo="Consulta de Urgência",
                    data_h_inicio=data_ato_inicio,
                    data_h_fim=data_ato_fim,
                    cod_epis=cod_epis,
                    id_hosp=hosp.nome_hosp,
                    num_func=med.num_func, # ATRIBUIÇÃO DO MÉDICO
                    diagnostico="Simulação de diagnóstico.",
                    decisao_clinica=decisao
                )
                session.add(ato)
                
                if e_internamento:
                    hosp_servicos = [s for s in servicos if s.id_hosp == hosp.nome_hosp]
                    servico = random.choice(hosp_servicos if hosp_servicos else servicos)
                    
                    data_int_entrada = data_ato_fim + timedelta(minutes=random.randint(10, 30))
                    
                    if status == "INTERNAMENTO_ATIVO":
                        cama = (i - 9) + 1 # Camas 1 a 5
                        data_int_saida = None
                    else:
                        cama = random.randint(1, 15)
                        data_int_saida = data_int_entrada + timedelta(hours=random.randint(2, 6))
                        episodio.data_h_saida = data_int_saida + timedelta(minutes=5)

                    internamento = Internamento(
                        cod_epis=cod_epis,
                        id_servico=servico.id_servico,
                        num_cama=cama,
                        data_h_entrada=data_int_entrada,
                        data_h_saida=data_int_saida,
                        num_func_medico=med.num_func # ATRIBUIÇÃO DO MÉDICO NO INTERNAMENTO
                    )
                    session.add(internamento)
                else:
                    episodio.data_h_saida = data_ato_fim + timedelta(minutes=5)

    session.commit()
    return {
        "message": f"Simulação concluída para o hospital: {hospital_name if hospital_name else 'Todos'}", 
        "total": 200, 
        "detalhes": "5 espera triagem, 4 espera consulta, 5 internamento ativo, 186 fechados. Profissionais atribuídos."
    }
