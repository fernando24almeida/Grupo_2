from app.core.db import motor
from app.models.models import Utente
from app.core.security import verificar_palavra_passe
from sqlmodel import Session

def verify():
    num = 111122223
    pin = "993999"
    with Session(motor) as sessao:
        utente = sessao.get(Utente, num)
        if not utente:
            print("Utente não encontrado")
            return
        
        result = verificar_palavra_passe(pin, utente.password_hash)
        print(f"PIN {pin} coincide com o hash do utente {num}? {'SIM' if result else 'NÃO'}")

if __name__ == "__main__":
    verify()
