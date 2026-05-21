from sqlmodel import Session, create_engine, select
from app.models.models import EpisodioUrgencia, Triagem
import os

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def hex_dump(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

def debug_keys_hex():
    with Session(engine) as session:
        print("--- EpisodioUrgencia cod_epis ---")
        eps = session.exec(select(EpisodioUrgencia)).all()
        for ep in eps:
            print(f"'{ep.cod_epis}', Hex: {hex_dump(ep.cod_epis)}")

        print("\n--- Triagem cod_epis ---")
        tris = session.exec(select(Triagem)).all()
        for t in tris:
            print(f"'{t.cod_epis}', Hex: {hex_dump(t.cod_epis)}")

if __name__ == "__main__":
    debug_keys_hex()
