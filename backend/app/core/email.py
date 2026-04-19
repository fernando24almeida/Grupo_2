from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from .config import configuracoes
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=configuracoes.MAIL_USERNAME,
    MAIL_PASSWORD=configuracoes.MAIL_PASSWORD,
    MAIL_FROM=configuracoes.MAIL_FROM,
    MAIL_PORT=configuracoes.MAIL_PORT,
    MAIL_SERVER=configuracoes.MAIL_SERVER,
    MAIL_FROM_NAME=configuracoes.MAIL_FROM_NAME,
    MAIL_STARTTLS=configuracoes.MAIL_STARTTLS,
    MAIL_SSL_TLS=configuracoes.MAIL_SSL_TLS,
    USE_CREDENTIALS=configuracoes.USE_CREDENTIALS
)

async def enviar_email_ativacao(email: EmailStr, nome: str, codigo: str):
    html = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <h2 style="color: #2563eb;">Bem-vindo ao Portal Clínico G2</h2>
            <p>Olá <strong>{nome}</strong>,</p>
            <p>A sua conta de utilizador foi criada pelo administrador. Para começar a utilizar o sistema, utilize o código de ativação abaixo:</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #2563eb;">{codigo}</span>
            </div>
            <p>Este código expira em 24 horas.</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 12px; color: #64748b;">Se não esperava este e-mail, por favor ignore-o.</p>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Ativação de Conta - Portal Clínico G2",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def enviar_email_recuperacao_username(email: EmailStr, nome: str, username: str):
    html = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <h2 style="color: #2563eb;">Recuperação de Utilizador</h2>
            <p>Olá <strong>{nome}</strong>,</p>
            <p>Recebemos um pedido de recuperação do nome de utilizador associado a este e-mail.</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <p style="margin-bottom: 5px; color: #64748b;">O seu nome de utilizador é:</p>
                <span style="font-size: 24px; font-weight: bold; color: #2563eb;">{username}</span>
            </div>
            <p>Já pode voltar a aceder ao Portal Clínico utilizando estas credenciais.</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 12px; color: #64748b;">Se não solicitou esta informação, por favor ignore este e-mail.</p>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(subject="Recuperação de Utilizador - Portal Clínico G2", recipients=[email], body=html, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)

async def enviar_email_recuperacao_password(email: EmailStr, nome: str, link: str):
    html = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <h2 style="color: #2563eb;">Recuperação de Palavra-passe</h2>
            <p>Olá <strong>{nome}</strong>,</p>
            <p>Recebemos um pedido para redefinir a palavra-passe da sua conta.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Redefinir Palavra-passe</a>
            </div>
            <p>Este link é válido por 1 hora. Se o botão não funcionar, copie e cole o seguinte link no seu navegador:</p>
            <p style="word-break: break-all; font-size: 12px; color: #2563eb;">{link}</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 12px; color: #64748b;">Se não solicitou a redefinição da sua palavra-passe, pode ignorar este e-mail com segurança.</p>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(subject="Recuperação de Palavra-passe - Portal Clínico G2", recipients=[email], body=html, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)
