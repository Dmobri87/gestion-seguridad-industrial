"""
Servicio de notificaciones para envío de códigos OTP.
Soporta SMS y WhatsApp a través de Twilio.

Si Twilio no está configurado, el código se devuelve en modo dev.
"""

import logging
from app.core.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    TWILIO_WHATSAPP_FROM,
    APP_NAME,
    OTP_EXPIRE_MINUTES,
)

logger = logging.getLogger(__name__)


def is_twilio_configured() -> bool:
    """Verifica si las credenciales de Twilio están configuradas."""
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)


def is_whatsapp_configured() -> bool:
    """Verifica si el canal de WhatsApp de Twilio está configurado."""
    return is_twilio_configured() and bool(TWILIO_WHATSAPP_FROM)


def _normalize_phone(phone: str) -> str:
    """
    Asegura que el número tenga formato E.164 (+57XXXXXXXXXX).
    Si no tiene '+', asume Colombia (+57).
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = f"+57{phone}"
    return phone


def send_otp_sms(phone: str, otp_code: str, user_name: str) -> bool:
    """
    Envía el código OTP por SMS usando Twilio.
    Retorna True si el mensaje se envió correctamente.
    """
    if not is_twilio_configured():
        logger.warning("Twilio SMS no configurado — se omite envío.")
        return False

    try:
        from twilio.rest import Client  # type: ignore

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        phone_e164 = _normalize_phone(phone)
        first_name = user_name.split()[0] if user_name else "Usuario"

        body = (
            f"[{APP_NAME}] Hola {first_name}, tu código de acceso es: "
            f"{otp_code}. "
            f"Válido por {OTP_EXPIRE_MINUTES} minutos. "
            f"No lo compartas con nadie."
        )

        message = client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_e164,
        )
        logger.info(
            "SMS OTP enviado a ...%s (sid=%s, status=%s)",
            phone_e164[-4:], message.sid, message.status,
        )
        return True

    except Exception:
        logger.exception("Error enviando SMS OTP a ...%s", phone[-4:])
        return False


def send_otp_whatsapp(phone: str, otp_code: str, user_name: str) -> bool:
    """
    Envía el código OTP por WhatsApp usando Twilio.
    Retorna True si el mensaje se envió correctamente.
    """
    if not is_whatsapp_configured():
        logger.warning("Twilio WhatsApp no configurado — se omite envío.")
        return False

    try:
        from twilio.rest import Client  # type: ignore

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        phone_e164 = _normalize_phone(phone)
        first_name = user_name.split()[0] if user_name else "Usuario"

        wa_to = (
            f"whatsapp:{phone_e164}"
            if not phone_e164.startswith("whatsapp:")
            else phone_e164
        )
        wa_from = (
            TWILIO_WHATSAPP_FROM
            if TWILIO_WHATSAPP_FROM.startswith("whatsapp:")
            else f"whatsapp:{TWILIO_WHATSAPP_FROM}"
        )

        body = (
            f"🔐 *{APP_NAME}*\n\n"
            f"Hola {first_name}, tu código de verificación es:\n\n"
            f"*{otp_code}*\n\n"
            f"⏱ Válido por {OTP_EXPIRE_MINUTES} minutos.\n"
            f"🚫 No compartas este código con nadie."
        )

        message = client.messages.create(
            body=body,
            from_=wa_from,
            to=wa_to,
        )
        logger.info(
            "WhatsApp OTP enviado a ...%s (sid=%s, status=%s)",
            phone_e164[-4:], message.sid, message.status,
        )
        return True

    except Exception:
        logger.exception("Error enviando WhatsApp OTP a ...%s", phone[-4:])
        return False


def send_otp_notification(phone: str, otp_code: str, user_name: str) -> dict:
    """
    Envía el OTP por SMS y WhatsApp simultáneamente.

    Retorna un dict con:
        sms       : bool — si el SMS fue enviado
        whatsapp  : bool — si el WhatsApp fue enviado
        any_sent  : bool — si se envió por al menos un canal
        channels  : list[str] — nombres de canales exitosos
    """
    sms_sent = send_otp_sms(phone, otp_code, user_name)
    whatsapp_sent = send_otp_whatsapp(phone, otp_code, user_name)

    channels = []
    if sms_sent:
        channels.append("SMS")
    if whatsapp_sent:
        channels.append("WhatsApp")

    return {
        "sms": sms_sent,
        "whatsapp": whatsapp_sent,
        "any_sent": sms_sent or whatsapp_sent,
        "channels": channels,
    }
