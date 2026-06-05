from cryptography.fernet import Fernet
from .config import configuracoes

# =============================================================================
# MÓDULO DE CRIPTOGRAFIA (AES)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro é a 'máquina de códigos' do hospital. Ele serve para 
# embaralhar dados sensíveis (como notas de exames) antes de os guardarmos 
# na base de dados. Mesmo que alguém roube o disco rígido, não conseguirá 
# ler nada sem a 'chave' secreta que está guardada no nosso Docker.
# =============================================================================

# Inicializa a máquina com a chave secreta das configurações
fernet = Fernet(configuracoes.ENCRYPTION_KEY.encode())

def criptografar_dado(dado: str) -> str:
    """ Transforma texto normal em 'garatujas' ilegíveis. """
    if not dado:
        return None
    return fernet.encrypt(dado.encode()).decode()

def descriptografar_dado(dado_criptografado: str) -> str:
    """ Transforma as 'garatujas' de volta em texto normal. """
    if not dado_criptografado:
        return None
    try:
        return fernet.decrypt(dado_criptografado.encode()).decode()
    except Exception:
        # Se a chave estiver errada ou o dado for inválido, devolve o original
        return dado_criptografado
