from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .api import auth, clinical, analytics
from .core.db import inicializar_bd, obter_sessao
from fastapi import Depends

# =============================================================================
# FICHEIRO PRINCIPAL (ENTRADA DA API)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este é o "rececionista" do nosso servidor. É o primeiro ficheiro a correr.
# Ele configura as regras de segurança, liga as rotas (os caminhos da API) 
# e garante que a base de dados está pronta a funcionar quando ligamos o sistema.
# =============================================================================

app = FastAPI(title="API do Sistema de Gestão Clínica")

# Middleware para Cabeçalhos de Segurança (HSTS, CSP, etc)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Este bloco adiciona 'escudos' de segurança a todas as respostas do servidor.
    Diz ao browser para ser rígido com a segurança e não permitir ataques comuns.
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.on_event("startup")
def on_startup():
    """ Corre automaticamente quando o servidor liga. Cria as tabelas na BD. """
    inicializar_bd()

# Configuração de CORS (Cross-Origin Resource Sharing)
# Permite que o Frontend (React) fale com este Backend mesmo estando em 'portas' diferentes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, devemos colocar aqui apenas o URL do Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(sessao=Depends(obter_sessao)):
    """ Endpoint de 'saúde' para verificar se o servidor e a BD estão vivos. """
    try:
        from sqlmodel import text
        sessao.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}

@app.get("/")
async def root():
    """ Mensagem de boas-vindas na raiz da API. """
    return {"message": "Bem-vindo à API do Sistema de Gestão Clínica"}

# INCLUSÃO DOS ROTEADORES (Agrupamento de rotas por tema)
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(clinical.router, prefix="/clinical", tags=["Gestão Clínica"])
app.include_router(analytics.router, prefix="/analytics", tags=["Análise Operacional"])
