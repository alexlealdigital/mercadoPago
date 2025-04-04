import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 465  # Porta segura com SSL
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")  # Opcional: cópia para você mesmo

def enviar_email(destinatario, assunto, corpo):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))  # <- alterado aqui!

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, destinatario, msg.as_string())
            print(f"Email enviado para {destinatario}")
            
            # Enviar cópia para o administrador (opcional)
            if EMAIL_RECIPIENT and EMAIL_RECIPIENT != destinatario:
                server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
                print(f"Cópia enviada para {EMAIL_RECIPIENT}")

    except Exception as e:
        print("Erro ao enviar e-mail:", e)
