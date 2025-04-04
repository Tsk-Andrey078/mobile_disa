
import re
import requests
from decouple import config

MOBIZON_API_KEY = config("MOBIZON_API_KEY")
MOBIZON_API_URL = config("MOBIZON_API_URL")

def send_verification_code(phone_number, code):
    """
    Отправляет SMS с кодом подтверждения на указанный номер телефона через Mobizon API.
    """
    payload = {
        'recipient': phone_number,
        'text': f'Проверочный код для регистрации на сайте iSPARK.kz: {code}',
        'apiKey': MOBIZON_API_KEY,
    }
    response = requests.get(MOBIZON_API_URL, params=payload)
    result = response.json()
    if result.get('code') == 0:
        return {'status': 'success'}
    else:
        return {
            'status': 'error',
            'message': result.get('message', 'Ошибка при отправке SMS')
        }
