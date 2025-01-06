from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from fcm_django.models import FCMDevice
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from .twilio_service import send_verification_code, check_verification_code
from .models import CustomUser
from .serializer import CustomTokenObtainPairSerializer

class SendVerificationCodeView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Номер телефона обязателен"}, status=status.HTTP_400_BAD_REQUEST)
        
        status_code = send_verification_code(phone_number)
        if status_code:
            return Response({"message": "Код отправлен успешно"}, status=status.HTTP_200_OK)
        return Response({"error": "Ошибка при отправке кода"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyCodeAndRegisterView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')
        full_name = request.data.get('full_name')
        password = request.data.get('password')

        if not phone_number or not code or not full_name or not password:
            return Response(
                {"error": "Номер телефона, ФИО, код и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем код через Twilio
        is_verified = check_verification_code(phone_number, code)
        if not is_verified:
            return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, существует ли пользователь
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response({"message": "Пользователь уже существует"}, status=status.HTTP_200_OK)

        # Создаем нового пользователя
        try:
            user = CustomUser.objects.create(
                phone_number=phone_number,
                full_name=full_name,
                password=make_password(password)  # Хэшируем пароль
            )
            return Response({"message": "Пользователь успешно зарегистрирован"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Ошибка при создании пользователя: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("registration_id")
        device_type = request.data.get("type")  # Например, "ios" или "android"

        if not token or not device_type:
            return Response({"error": "Token and type are required"}, status=400)

        device, created = FCMDevice.objects.get_or_create(
            user=request.user,
            registration_id=token,
            type=device_type,
        )
        if not created:
            device.save()

        return Response({"message": "Device registered successfully"})
    
