from sqlmodel import Session, create_engine, select
from app.models.models import Hospital, EpisodioUrgencia
import os

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def hex_dump(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

def debug_hospital_hex():
    with Session(engine) as session:
        print("--- Hospitais na tabela 'Hospital' ---")
        hospitals = session.exec(select(Hospital)).all()
        for h in hospitals:
            print(f"Name: '{h.nome_hosp}', Hex: {hex_dump(h.nome_hosp)}")

        print("\n--- id_hospital na tabela 'EpisodioUrgencia' ---")
        eps = session.exec(select(EpisodioUrgencia)).all()
        for ep in eps:
            print(f"Ep: {ep.cod_epis}, id_hosp: '{ep.id_hospital}', Hex: {hex_dump(ep.id_hospital)}")

if __name__ == "__main__":
    debug_hospital_hex()
