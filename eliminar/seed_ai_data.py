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

def seed_data():
    engine = create_engine(DATABASE_URL)
    
    # 1. Obter um hospital e um utente existente para evitar erros de FK
    with engine.connect() as conn:
        hosp = conn.execute(text("SELECT nome_hosp FROM hospital LIMIT 1")).fetchone()
        ut = conn.execute(text("SELECT num_utente FROM utente LIMIT 1")).fetchone()
        
        if not hosp or not ut:
            print("Erro: Precisa de pelo menos um hospital e um utente na BD.")
            return

        nome_hosp = hosp[0]
        num_utente = ut[0]

        print(f"Gerando dados para o hospital: {nome_hosp} e utente: {num_utente}")

        # 2. Gerar 200 episódios aleatórios nos últimos 30 dias
        episodios = []
        agora = datetime.now()
        
        for i in range(200):
            dias_atras = random.randint(0, 30)
            horas_atras = random.randint(0, 23)
            minutos_atras = random.randint(0, 59)
            
            data_entrada = agora - timedelta(days=dias_atras, hours=horas_atras, minutes=minutos_atras)
            cod_epis = f"AI-SEED-{i:03d}"
            
            episodios.append({
                "cod_epis": cod_epis,
                "data_h_entr": data_entrada,
                "id_utente": num_utente,
                "id_hosp": nome_hosp,
                "sintomas": "Gerado automaticamente para teste de AI"
            })

        # 3. Inserir na base de dados
        insert_query = text("""
            INSERT INTO episodio_urgencia (cod_epis, data_h_entr, id_utente, id_hosp, sintomas)
            VALUES (:cod_epis, :data_h_entr, :id_utente, :id_hosp, :sintomas)
            ON CONFLICT (cod_epis) DO NOTHING
        """)
        
        for ep in episodios:
            conn.execute(insert_query, ep)
        
        conn.commit()
        print(f"Sucesso! Foram inseridos {len(episodios)} episódios de teste.")

if __name__ == "__main__":
    seed_data()
