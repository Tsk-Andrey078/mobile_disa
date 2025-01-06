from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class PhoneNumberBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(phone_number=username)  # Ищем по phone_number
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None