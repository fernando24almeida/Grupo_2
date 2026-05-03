from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .api import auth, clinical, analytics
from .core.db import inicializar_bd, obter_sessao
from fastapi import Depends
from .routes.analytics_ai import router as analytics_ai_router

app = FastAPI(title="API do Sistema de Gestão Clínica")

app.include_router(analytics_ai_router)

# Middleware para Cabeçalhos de Segurança (HSTS, CSP, etc)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
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
    inicializar_bd()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(sessao=Depends(obter_sessao)):
    try:
        from sqlmodel import text
        sessao.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}

@app.get("/")
async def root():
    return {"message": "Bem-vindo à API do Sistema de Gestão Clínica"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(clinical.router, prefix="/clinical", tags=["Gestão Clínica"])
app.include_router(analytics.router, prefix="/analytics", tags=["Análise Operacional"])

