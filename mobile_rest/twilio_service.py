from twilio.rest import Client
from decouple import config

# Получаем учетные данные из .env
account_sid = config('TWILIO_ACCOUNT_SID')
auth_token = config('TWILIO_AUTH_TOKEN')
verify_service_sid = config('TWILIO_VERIFY_SERVICE_SID')

client = Client(account_sid, auth_token)

def send_verification_code(phone_number):
    """
    Отправляет код верификации на указанный номер телефона.
    """
    try:
        verification = client.verify.services(verify_service_sid).verifications.create(
            to=phone_number,
            channel="sms"  # Можно использовать "call" для звонков
        )
        return verification.status
    except Exception as e:
        print(f"Ошибка при отправке кода: {e}")
        return None

def check_verification_code(phone_number, code, full_name=None):
    """
    Проверяет код подтверждения через Twilio.
    """
    try:
        verification_check = client.verify.services(verify_service_sid).verification_checks.create(
            to=phone_number,
            code=code
        )
        return verification_check.status == "approved"
    except Exception as e:
        print(f"Ошибка при проверке кода: {e}")
        return False
