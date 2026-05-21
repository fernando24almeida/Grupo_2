import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.core.config import configuracoes
    DATABASE_URL = configuracoes.DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql://postgres:admin@127.0.0.1:5432/urgencias_g2"

def generate_random_name():
    primeiros = ["João", "Maria", "Ana", "Pedro", "Rui", "Sílvia", "Carlos", "Isabel", "Tiago", "Marta"]
    apelidos = ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins"]
    return f"{random.choice(primeiros)} {random.choice(apelidos)} {random.choice(apelidos)}"

def generate_random_address():
    ruas = ["Rua da Liberdade", "Avenida da República", "Rua das Flores", "Praça Central", "Rua do Ouro"]
    cidades = ["Lisboa", "Porto", "Coimbra", "Braga", "Faro", "Aveiro"]
    return f"{random.choice(ruas)}, nº {random.randint(1, 200)}, {random.choice(cidades)}"

def seed_complete_history():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Limpando dados antigos de teste...")
        filtros = "cod_epis LIKE 'EP202%' OR cod_epis LIKE 'AI-SEED-%'"
        conn.execute(text(f"DELETE FROM internamento WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM prescricao WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM ato WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM triagem WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM episodio_urgencia WHERE {filtros}"))
        
        hosp = conn.execute(text("SELECT nome_hosp FROM hospital LIMIT 1")).fetchone()
        servicos = conn.execute(text("SELECT id_servico FROM servico_hospitalar")).fetchall()
        id_servicos = [s[0] for s in servicos] if servicos else [1]
        
        if not hosp:
            print("Erro: Hospital não encontrado.")
            return
        nome_hosp = hosp[0]

        print("Gerando 200 episódios completos (24 meses)...")
        
        for i in range(1, 201):
            # 1. Utente
            num_utente = 900000000 + i
            conn.execute(text("""
                INSERT INTO utente (num_utente, nome, morada, sexo, localidade, data_nasc)
                VALUES (:n, :nom, :m, :s, :l, :d)
                ON CONFLICT (num_utente) DO UPDATE SET nome = EXCLUDED.nome
            """), {
                "n": num_utente, "nom": generate_random_name(), 
                "m": generate_random_address(), "s": random.choice(["M", "F"]),
                "l": "Portugal", "d": datetime(random.randint(1940, 2015), 1, 1).date()
            })

            # 2. Episódio (Histórico de 24 meses)
            dias_atras = random.randint(0, 730)
            data_entrada = datetime.now() - timedelta(days=dias_atras, hours=random.randint(0, 23))
            data_saida = data_entrada + timedelta(hours=random.randint(4, 48))
            cod_epis = f"EP2024{i:05d}"

            conn.execute(text("""
                INSERT INTO episodio_urgencia (cod_epis, data_h_entr, data_h_saida, id_utente, id_hosp, sintomas)
                VALUES (:c, :de, :ds, :u, :h, :s)
            """), {
                "c": cod_epis, "de": data_entrada, "ds": data_saida, 
                "u": num_utente, "h": nome_hosp, "s": "Sintomas variados para análise de IA"
            })

            # 3. Triagem
            prioridade = random.choice(["VERMELHO", "LARANJA", "AMARELO", "VERDE", "AZUL"])
            conn.execute(text("""
                INSERT INTO triagem (cod_epis, prioridade, data_h_triage, num_func_enfermeiro, sintomas)
                VALUES (:c, :p, :d, 1001, :s)
            """), {
                "c": cod_epis, "p": prioridade, "d": data_entrada + timedelta(minutes=15),
                "s": "Paciente apresenta queixas compatíveis com a prioridade selecionada."
            })

            # 4. Consulta (Ato Médico)
            data_inicio_ato = data_entrada + timedelta(hours=random.randint(1, 3))
            conn.execute(text("""
                INSERT INTO ato (tipo, data_h_inicio, data_h_fim, cod_epis, id_hosp, num_func, diagnostico, notas_clinicas, decisao_clinica)
                VALUES (:t, :di, :df, :c, :h, 1002, :diag, :not, :dec)
            """), {
                "t": "CONSULTA URGÊNCIA", "di": data_inicio_ato, "df": data_inicio_ato + timedelta(minutes=45),
                "c": cod_epis, "h": nome_hosp, "diag": "Diagnóstico clínico efetuado",
                "not": "Paciente estável após medicação inicial.", "dec": random.choice(["ALTA", "INTERNAMENTO", "TRANSFERÊNCIA"])
            })

            # 5. Internamento (em 20% dos casos)
            if random.random() < 0.2:
                conn.execute(text("""
                    INSERT INTO internamento (cod_epis, id_servico, num_cama, data_h_entrada, data_h_saida, num_func_medico)
                    VALUES (:c, :s, :cam, :de, :ds, 1002)
                """), {
                    "c": cod_epis, "s": random.choice(id_servicos), "cam": random.randint(1, 50),
                    "de": data_saida - timedelta(hours=1), "ds": data_saida + timedelta(days=random.randint(1, 5)),
                    "num_func_medico": 1002
                })

        conn.commit()
        print(f"Sucesso! 200 episódios completos gerados cobrindo os últimos 24 meses.")

if __name__ == "__main__":
    seed_complete_history()
