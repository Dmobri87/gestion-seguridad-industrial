"""
Utilidad para envío de emails con OTP.
Soporta SMTP configurado por variables de entorno.
En modo desarrollo (sin SMTP), registra el OTP en logs.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Verifica si las credenciales SMTP están configuradas."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _build_otp_html(otp_code: str, user_name: str) -> str:
    """Genera el template HTML profesional para el email de OTP."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px; margin: 0 auto;">
        <tr>
            <td style="padding: 40px 0;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a365d 0%, #2563eb 100%); padding: 32px 40px; text-align: center;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="text-align: center;">
                                        <div style="width: 56px; height: 56px; background-color: rgba(255,255,255,0.2); border-radius: 50%; display: inline-block; line-height: 56px; font-size: 28px; margin-bottom: 12px;">
                                            &#128274;
                                        </div>
                                        <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px;">
                                            Sistema de Gesti&oacute;n de Seguridad Industrial
                                        </h1>
                                        <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0 0; font-size: 13px;">
                                            Verificaci&oacute;n de identidad
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #334155; font-size: 16px; margin: 0 0 8px 0;">
                                Hola, <strong>{user_name}</strong>
                            </p>
                            <p style="color: #64748b; font-size: 14px; margin: 0 0 28px 0; line-height: 1.6;">
                                Hemos recibido una solicitud de inicio de sesi&oacute;n en su cuenta.
                                Utilice el siguiente c&oacute;digo de verificaci&oacute;n para completar el acceso:
                            </p>

                            <!-- OTP Code -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="text-align: center; padding: 24px 0;">
                                        <div style="background-color: #f0f4ff; border: 2px dashed #2563eb; border-radius: 12px; padding: 20px 32px; display: inline-block;">
                                            <span style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700; letter-spacing: 12px; color: #1a365d;">
                                                {otp_code}
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #ef4444; font-size: 13px; text-align: center; margin: 16px 0 28px 0; font-weight: 500;">
                                &#9202; Este c&oacute;digo expira en 5 minutos.
                            </p>

                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">

                            <p style="color: #94a3b8; font-size: 12px; line-height: 1.6; margin: 0;">
                                <strong>&#9888; Nota de seguridad:</strong> Si usted no solicit&oacute; este c&oacute;digo,
                                ignore este mensaje. Nunca comparta su c&oacute;digo de verificaci&oacute;n con nadie.
                                Nuestro equipo nunca le solicitar&aacute; este c&oacute;digo.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="color: #94a3b8; font-size: 11px; margin: 0; line-height: 1.5;">
                                Sistema de Gesti&oacute;n de Seguridad Industrial y Salud Ocupacional v2.0
                                <br>
                                Este es un mensaje autom&aacute;tico, por favor no responda a este correo.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def send_otp_email(to_email: str, otp_code: str, user_name: str) -> bool:
    """
    Envía el código OTP al email del usuario.

    Args:
        to_email: Dirección de email del destinatario.
        otp_code: Código OTP de 6 dígitos.
        user_name: Nombre del usuario para personalizar el mensaje.

    Returns:
        True si el email se envió correctamente, False en caso contrario.
    """
    if not is_smtp_configured():
        logger.warning(
            "SMTP no configurado. OTP para %s: %s (solo visible en modo desarrollo)",
            to_email,
            otp_code,
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Código de verificación - Sistema de Gestión de Seguridad Industrial"
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        # Versión texto plano como fallback
        text_content = (
            f"Hola {user_name},\n\n"
            f"Su código de verificación es: {otp_code}\n\n"
            f"Este código expira en 5 minutos.\n\n"
            f"Si usted no solicitó este código, ignore este mensaje.\n\n"
            f"Sistema de Gestión de Seguridad Industrial y Salud Ocupacional"
        )

        # Versión HTML
        html_content = _build_otp_html(otp_code, user_name)

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        logger.info("Email OTP enviado exitosamente a %s", to_email)
        return True

    except smtplib.SMTPException as e:
        logger.error("Error SMTP enviando OTP a %s: %s", to_email, str(e))
        return False
    except Exception as e:
        logger.error("Error inesperado enviando OTP a %s: %s", to_email, str(e))
        return False
