from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from fcm_django.models import FCMDevice
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import make_password
from sentry_sdk import capture_exception

from .twilio_service import send_verification_code, check_verification_code
from .models import CustomUser, MediaFiles, MediaFile
from .serializer import CustomTokenObtainPairSerializer, MediaFilesSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SendVerificationCodeView(APIView):
    @swagger_auto_schema(
        operation_description="Отправка кода подтверждения на номер телефона",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона")
            },
            required=['phone_number']  # Указываем обязательные поля
        ),
        responses={
            200: 'Код отправлен успешно',
            400: 'Номер телефона обязателен',
            500: 'Ошибка при отправке кода'
        }
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Номер телефона обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        # Call the service function to send the verification code
        result = send_verification_code(phone_number)

        if 'status' in result:  # This means the code was successfully sent
            return Response({"message": "Код отправлен успешно"}, status=status.HTTP_200_OK)

        # If we get error details, we return them
        return Response({
            "error": result.get("error", "Неизвестная ошибка"),
            "message": result.get("message", "Ошибка при отправке кода"),
            "error_code": result.get("error_code", "Неизвестный код ошибки")
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyCodeAndRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="Проверка кода и регистрация нового пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Код подтверждения"),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description="Полное имя пользователя"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Пароль пользователя")
            },
            required=['phone_number', 'code', 'password']  # Указываем обязательные поля
        ),
        responses={
            201: 'Пользователь успешно зарегистрирован',
            400: 'Неверный код или обязательные поля отсутствуют',
            500: 'Ошибка при создании пользователя'
        }
    )
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

        try:
            # Проверяем код через Twilio
            is_verified = check_verification_code(phone_number, code)
            if not is_verified:
                return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, существует ли пользователь
            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response({"message": "Пользователь уже существует"}, status=status.HTTP_409_CONFLICT)

            # Создаем нового пользователя
            user = CustomUser.objects.create(
                phone_number=phone_number,
                full_name=full_name,
                password=make_password(password)  # Хэшируем пароль
            )
            return Response({"message": "Пользователь успешно зарегистрирован"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            capture_exception(e)
            return Response({"error": f"Ошибка при создании пользователя: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterDeviceView(APIView):
    @swagger_auto_schema(
        operation_description="Регистрация устройства для получения уведомлений",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'registration_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                  description="Id девайса или что то блэд в этом роде"),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description="Тест на яблокофон")
            },
            required=['registration_id', 'type']  # Указываем обязательные поля
        ),
        responses={
            200: 'Устройство успешно зарегистрировано',
            400: 'Token и type обязательны'
        }
    )
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


class MediaFilesUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="Создание записи с видео или фото",
        manual_parameters=[
            openapi.Parameter(
                'city', openapi.IN_FORM, description="Город", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'street', openapi.IN_FORM, description="Улица", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'description', openapi.IN_FORM, description="Описание", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'was_at_date', openapi.IN_FORM, description="Дата происшествия (YYYY-MM-DD)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'was_at_time', openapi.IN_FORM, description="Время происшествия (HH:MM:SS)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'video_files', openapi.IN_FORM, description="Видео файлы (можно несколько)", type=openapi.TYPE_FILE,
                multiple=True
            ),
        ],
        responses={
            201: "Запись успешно создана",
            400: "Ошибка в данных"
        }
    )
    def post(self, request, *args, **kwargs):
        data = {
            'user': request.user,
            'city': request.data.get('city'),
            'street': request.data.get('street'),
            'description': request.data.get('description'),
            'was_at_date': request.data.get('was_at_date'),
            'was_at_time': request.data.get('was_at_time'),
        }
        serializer = MediaFilesSerializer(data=data)
        if serializer.is_valid():
            media_instance = serializer.save()

            # Обрабатываем видео файлы
            video_files = request.FILES.getlist('video_files')
            for video in video_files:
                MediaFile.objects.create(media=media_instance, video_file=video)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET: Получение записи по ID
class MediaFilesDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение записи по ID",
        manual_parameters=[
            openapi.Parameter(
                'id', openapi.IN_QUERY, description="ID записи", type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: MediaFilesSerializer(),
            404: "Запись не найдена"
        }
    )
    def get(self, request, *args, **kwargs):
        record_id = request.query_params.get('id')
        try:
            media_instance = MediaFiles.objects.get(id=record_id)
            serializer = MediaFilesSerializer(media_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except MediaFiles.DoesNotExist:
            return Response({"error": "Запись не найдена"}, status=status.HTTP_404_NOT_FOUND)


# GET: Получение списка записей по пользователю
class MediaFilesListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение списка записей по пользователю",
        responses={
            200: MediaFilesSerializer(many=True),
            404: "Записи не найдены"
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = request.user
        media_instances = MediaFiles.objects.filter(user=user_id)
        if media_instances.exists():
            serializer = MediaFilesSerializer(media_instances, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Записи не найдены"}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema


class CheckToken(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Проверка авторизации",
        responses={
            200: "Авторизация успешна",
            401: "Ошибка авторизации"
        }
    )
    def get(self, request, *args, **kwargs):
        return Response({"message": "Авторизация успешна"}, status=status.HTTP_200_OK)
