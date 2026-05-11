from sqlmodel import Session, create_engine, select
from app.models.models import Hospital, EpisodioUrgencia
import os

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def check_hospitals():
    with Session(engine) as session:
        print("--- Hospitais ---")
        hospitais = session.exec(select(Hospital)).all()
        for h in hospitais:
            print(f"- Nome: '{h.nome_hosp}', Local: '{h.local_hosp}'")
        
        print("\n--- Episódios ---")
        episodios = session.exec(select(EpisodioUrgencia)).all()
        for e in episodios:
            u = session.get(Utente, e.id_utente)
            nome_u = u.nome if u else "Desconhecido"
            print(f"- Cod: {e.cod_epis}, Utente: {nome_u} ({e.id_utente}), Hosp: '{e.id_hospital}', Saída: {e.data_h_saida}")

if __name__ == "__main__":
    check_hospitals()
