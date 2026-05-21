from sqlmodel import Session, create_engine, select
from app.models.models import EpisodioUrgencia, Hospital, Utente
from app.api.clinical import CriarEpisodio, criar_episodio
from fastapi import HTTPException
import os
from datetime import datetime

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def reproduce():
    with Session(engine) as session:
        # Create a new utente for testing to avoid "already has open episode"
        num_utente = 888888888
        utente = session.get(Utente, num_utente)
        if not utente:
            utente = Utente(num_utente=num_utente, nome="Teste Repro", email="repro@teste.pt")
            session.add(utente)
            session.commit()
            print(f"Utente {num_utente} criado.")
        
        dados = CriarEpisodio(
            id_utente=num_utente,
            id_hospital="Hospital Inexistente",
            sintomas="Dor de cabeça",
            observacoes="Teste de reprodução"
        )
        
        print(f"A tentar criar episódio para utente {num_utente} no hospital '{dados.id_hospital}'...")
        try:
            # We need to mock obtaining session if we call the function directly
            # Or just simulate the logic.
            # Let's call the function logic manually or import it if possible.
            # Since it's a FastAPI dependency, calling it directly with a real session should work.
            res = criar_episodio(dados, session)
            print(f"SUCESSO: Episódio criado com código {res.cod_epis}")
        except HTTPException as e:
            print(f"FALHA (HTTPException): {e.status_code} - {e.detail}")
        except Exception as e:
            print(f"ERRO INESPERADO: {type(e).__name__}: {e}")

if __name__ == "__main__":
    reproduce()
