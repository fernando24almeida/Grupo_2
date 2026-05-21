import random
import string
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

def seed_rich_data():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Limpar dados anteriores de teste em todas as tabelas dependentes
        print("Limpando dados antigos...")
        filtros = "cod_epis LIKE 'EP2026%' OR cod_epis LIKE 'AI-SEED-%'"
        
        conn.execute(text(f"DELETE FROM internamento WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM prescricao WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM ato WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM triagem WHERE {filtros}"))
        conn.execute(text(f"DELETE FROM episodio_urgencia WHERE {filtros}"))
        
        hosp = conn.execute(text("SELECT nome_hosp FROM hospital LIMIT 1")).fetchone()
        if not hosp:
            print("Erro: Hospital não encontrado.")
            return
        nome_hosp = hosp[0]

        # 2. Criar utentes fictícios
        print("Criando utentes e episódios realistas...")
        for i in range(1, 101): # 100 utentes
            num_utente = 900000000 + i
            nome = generate_random_name()
            morada = generate_random_address()
            sexo = random.choice(["M", "F"])
            localidade = morada.split(", ")[-1]
            data_nasc = datetime(random.randint(1950, 2010), random.randint(1, 12), random.randint(1, 28)).date()
            
            # Inserir Utente
            conn.execute(text("""
                INSERT INTO utente (num_utente, nome, morada, sexo, localidade, data_nasc)
                VALUES (:n, :nom, :m, :s, :l, :d)
                ON CONFLICT (num_utente) DO UPDATE SET nome = EXCLUDED.nome
            """), {"n": num_utente, "nom": nome, "m": morada, "s": sexo, "l": localidade, "d": data_nasc})

            # Gerar 2 episódios para cada utente (200 total)
            for j in range(2):
                agora = datetime.now()
                dias_atras = random.randint(0, 60)
                data_entrada = agora - timedelta(days=dias_atras, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                # Formato solicitado: EP202605 + sequencial
                cod_epis = f"EP202605{((i-1)*2 + j + 1):04d}"
                
                sintomas = random.choice([
                    "Dor abdominal aguda", "Febre persistente e tosse", "Traumatismo no membro inferior",
                    "Cefaleia intensa", "Dificuldade respiratória", "Dor torácica", "Vómitos e náuseas"
                ])
                
                # Gerar data de saída (entre 2 a 12 horas após a entrada)
                data_saida = data_entrada + timedelta(hours=random.randint(2, 12), minutes=random.randint(0, 59))
                
                # Inserir Episódio com data de saída
                conn.execute(text("""
                    INSERT INTO episodio_urgencia (cod_epis, data_h_entr, data_h_saida, id_utente, id_hosp, sintomas)
                    VALUES (:c, :d, :ds, :u, :h, :s)
                """), {"c": cod_epis, "d": data_entrada, "ds": data_saida, "u": num_utente, "h": nome_hosp, "s": sintomas})
                
                # Adicionar uma Triagem para cada episódio para tornar os dados mais "reais"
                prioridade = random.choice(["VERMELHO", "LARANJA", "AMARELO", "VERDE", "AZUL"])
                conn.execute(text("""
                    INSERT INTO triagem (cod_epis, prioridade, data_h_triage, num_func_enfermeiro)
                    VALUES (:c, :p, :d, 1001)
                """), {"c": cod_epis, "p": prioridade, "d": data_entrada + timedelta(minutes=random.randint(5, 30))})

        conn.commit()
        print(f"Sucesso! 200 episódios sequenciais (EP202605...) e 100 utentes criados.")

if __name__ == "__main__":
    seed_rich_data()
