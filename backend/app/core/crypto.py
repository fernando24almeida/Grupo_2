from cryptography.fernet import Fernet
from .config import configuracoes

fernet = Fernet(configuracoes.ENCRYPTION_KEY.encode())

def encriptar_dado(texto: str) -> str:
    if not texto:
        return None
    return fernet.encrypt(texto.encode()).decode()

def desencriptar_dado(texto_encriptado: str) -> str:
    if not texto_encriptado:
        return None
    try:
        return fernet.decrypt(texto_encriptado.encode()).decode()
    except Exception:
        # Se falhar a desencriptação (ex: dado não encriptado), devolve o original ou erro controlado
        return texto_encriptado
