import sentry_sdk
import sentry_sdk.scope
import re

from twilio.rest import Client
from decouple import config
from twilio.base.exceptions import TwilioRestException

# Получаем учетные данные из .env
account_sid = config('TWILIO_ACCOUNT_SID')
auth_token = config('TWILIO_AUTH_TOKEN')
verify_service_sid = config('TWILIO_VERIFY_SERVICE_SID')

client = Client(account_sid, auth_token)


def clean_twilio_error_message(raw_message):
    """
    Очищает сообщение от управляющих символов и формирует более читаемое сообщение.
    """
    # Убираем управляющие символы
    cleaned_message = re.sub(r'\x1b\[.*?m', '', raw_message)
    return cleaned_message


def send_verification_code(phone_number):
    """
    Отправляет код верификации на указанный номер телефона.
    """
    try:
        verification = client.verify.v2.services(verify_service_sid).verifications.create(
            to=phone_number,
            channel="sms"  # Можно использовать "call" для звонков
        )
        return {"status": verification.status}
    except TwilioRestException as e:

        cleaned_message = clean_twilio_error_message(str(e))

        with sentry_sdk.isolation_scope() as scope:
            scope.set_extra("phone_number", phone_number)
            scope.set_extra("twilio_error_message", cleaned_message)
            sentry_sdk.capture_exception(e)

        error_details = {
            "error": "Ошибка при отправке кода",
            "message": "Произошла ошибка при отправке кода верификации. Пожалуйста, попробуйте еще раз.",
            "error_code": getattr(e, 'code', 'Неизвестный код ошибки'),
            "twilio_message": cleaned_message
        }

        return error_details


def check_verification_code(phone_number, code, full_name=None):
    """
    Проверяет код подтверждения через Twilio.
    """
    try:
        verification_check = client.verify.v2.services(verify_service_sid).verification_checks.create(
            to=phone_number,
            code=code
        )
        return verification_check.status == "approved"
    except Exception as e:
        # sentry_sdk.capture_exception(e)
        print(f"Ошибка при проверке кода: {e}")
        return False
