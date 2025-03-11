from rest_framework_simplejwt.views import TokenObtainPairView
from fcm_django.models import FCMDevice
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import make_password
from sentry_sdk import capture_exception
from drf_yasg import openapi

from .twilio_service import send_verification_code, check_verification_code
from .models import CustomUser, MediaFiles, MediaFile, MediaFileNews, News
from .serializer import (
    CustomTokenObtainPairSerializer,
    MediaFilesSerializer,
    NewsSerializer
)


# ===================================
#   RESET / UPDATE PASSWORD VIEWS
# ===================================

class RequestPasswordResetView(APIView):
    """
    Отправка SMS-кода для восстановления пароля.
    Пользователь указывает свой phone_number,
    если пользователь с таким номером существует, отправляем код.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Отправка кода для сброса пароля по номеру телефона",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Номер телефона, на который отправляем код"
                ),
            },
            required=['phone_number'],
        ),
        responses={
            200: 'Код отправлен успешно',
            400: 'Номер телефона не указан',
            404: 'Пользователь с таким номером не найден',
            500: 'Ошибка при отправке кода'
        }
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response(
                {"error": "Номер телефона обязателен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response(
                {"error": "Пользователь с таким номером не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        result = send_verification_code(phone_number)
        if 'status' in result:
            return Response(
                {"message": "Код для сброса пароля успешно отправлен."},
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "error": result.get("error", "Неизвестная ошибка"),
                "message": result.get("message", "Ошибка при отправке кода"),
                "error_code": result.get("error_code", "Неизвестный код ошибки")
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConfirmPasswordResetView(APIView):
    """
    Подтверждение кода из SMS и установка нового пароля.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Подтверждение кода и сброс пароля",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Номер телефона"
                ),
                'code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Код подтверждения из SMS"
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый пароль"
                ),
            },
            required=['phone_number', 'code', 'new_password'],
        ),
        responses={
            200: 'Пароль успешно обновлён',
            400: 'Код неверен или не указаны обязательные поля',
            404: 'Пользователь с таким номером не найден',
            500: 'Ошибка при обновлении пароля'
        }
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not phone_number or not code or not new_password:
            return Response(
                {"error": "Необходимо указать phone_number, code и new_password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(phone_number=phone_number).first()
        if not user:
            return Response(
                {"error": "Пользователь с таким номером не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not check_verification_code(phone_number, code):
            return Response(
                {"error": "Неверный код подтверждения."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user.password = make_password(new_password)
            user.save()
            return Response(
                {"message": "Пароль успешно обновлён."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"error": f"Ошибка при обновлении пароля: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===================================
#   AUTH / REGISTRATION VIEWS
# ===================================

class SendVerificationCodeView(APIView):
    """
    Отправляет код подтверждения на указанный номер телефона.
    """

    @swagger_auto_schema(
        operation_description="Отправка кода подтверждения на номер телефона",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Номер телефона"
                )
            },
            required=['phone_number'],
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
            return Response(
                {"error": "Номер телефона обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_verification_code(phone_number)
        if 'status' in result:
            return Response(
                {"message": "Код подтверждения успешно отправлен"},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "error": result.get("error", "Неизвестная ошибка"),
                "message": result.get("message", "Ошибка при отправке кода"),
                "error_code": result.get("error_code", "Неизвестный код ошибки")
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VerifyCodeAndRegisterView(APIView):
    """
    Проверяет код подтверждения и регистрирует нового пользователя.
    """

    @swagger_auto_schema(
        operation_description="Проверка кода и регистрация нового пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Номер телефона"
                ),
                'code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Код подтверждения из SMS"
                ),
                'full_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="ФИО или имя пользователя"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Пароль пользователя"
                )
            },
            required=['phone_number', 'code', 'password']
        ),
        responses={
            201: 'Пользователь успешно зарегистрирован',
            400: 'Неверный код или обязательные поля отсутствуют',
            409: 'Пользователь уже существует',
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
                {"error": "Необходимо указать номер телефона, код, ФИО и пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if not check_verification_code(phone_number, code):
                return Response(
                    {"error": "Указанный код подтверждения неверен"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "Пользователь с таким номером уже существует"},
                    status=status.HTTP_409_CONFLICT
                )

            CustomUser.objects.create(
                phone_number=phone_number,
                full_name=full_name,
                password=make_password(password)
            )
            return Response(
                {"message": "Пользователь успешно зарегистрирован"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"error": f"Ошибка при создании пользователя: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Кастомная JWT-аутентификация с использованием номера телефона.
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterDeviceView(APIView):
    """
    Регистрация устройства для получения push-уведомлений.
    """

    @swagger_auto_schema(
        operation_description="Регистрация устройства (FCM) для уведомлений",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'registration_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="FCM-токен устройства"
                ),
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Тип устройства (ios / android и т.д.)"
                )
            },
            required=['registration_id', 'type']
        ),
        responses={
            200: 'Устройство успешно зарегистрировано',
            400: 'Отсутствуют токен или тип устройства'
        }
    )
    def post(self, request):
        token = request.data.get("registration_id")
        device_type = request.data.get("type")

        if not token or not device_type:
            return Response(
                {"error": "Необходимо указать registration_id и type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        device, created = FCMDevice.objects.get_or_create(
            user=request.user,
            registration_id=token,
            type=device_type
        )
        # Если устройство уже существовало, можно обновить информацию
        if not created:
            device.type = device_type
            device.save()

        return Response(
            {"message": "Устройство успешно зарегистрировано"},
            status=status.HTTP_200_OK
        )

class MediaFilesCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Создание записи без видео",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'city': openapi.Schema(type=openapi.TYPE_STRING, description="Город"),
                'street': openapi.Schema(type=openapi.TYPE_STRING, description="Улица"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Описание"),
                'was_at_date': openapi.Schema(type=openapi.TYPE_STRING, description="Дата (YYYY-MM-DD)"),
                'was_at_time': openapi.Schema(type=openapi.TYPE_STRING, description="Время (HH:MM:SS)"),
            },
            required=['city', 'street', 'description', 'was_at_date', 'was_at_time']
        ),
        responses={201: "Запись создана", 400: "Ошибка в данных"}
    )
    def post(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'city': request.data.get('city'),
            'street': request.data.get('street'),
            'description': request.data.get('description'),
            'was_at_date': request.data.get('was_at_date'),
            'was_at_time': request.data.get('was_at_time'),
            'status': 'Waiting',
        }
        serializer = MediaFilesSerializer(data=data)

        if serializer.is_valid():
            media_instance = serializer.save()
            return Response(MediaFilesSerializer(media_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MediaFileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        video_file = request.FILES.get('video')

        if not media_id or not video_file:
            return Response({'error': 'media_id и video обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            media_instance = MediaFiles.objects.get(id=media_id)
        except MediaFiles.DoesNotExist:
            return Response({'error': 'MediaFiles не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем новую запись
        MediaFile.objects.create(media=media_instance, video_file=video_file)

        return Response({'message': 'Видео загружено'}, status=status.HTTP_201_CREATED)


class MediaFilesDetailView(APIView):
    """
    Получение информации о конкретной записи MediaFiles по ID.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение записи MediaFiles по ID",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="ID записи",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: MediaFilesSerializer(),
            400: "Не указан параметр id",
            404: "Запись не найдена"
        }
    )
    def get(self, request, *args, **kwargs):
        record_id = request.query_params.get('id')
        if not record_id:
            return Response(
                {"error": "Необходимо указать параметр 'id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            media_instance = MediaFiles.objects.get(id=record_id)
            serializer = MediaFilesSerializer(media_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except MediaFiles.DoesNotExist:
            return Response({"error": "Запись не найдена"}, status=status.HTTP_404_NOT_FOUND)


class MediaFilesListView(APIView):
    """
    Получение списка записей MediaFiles (по пользователю или всех).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение списка записей (по пользователю или всех)",
        manual_parameters=[
            openapi.Parameter(
                'type',
                openapi.IN_QUERY,
                description="Тип запроса: 'user' или 'all'",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Количество записей в выборке",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: MediaFilesSerializer(many=True),
            400: "Некорректные параметры запроса",
            404: "Записи не найдены"
        }
    )
    def get(self, request, *args, **kwargs):
        query_type = request.query_params.get("type")
        limit_str = request.query_params.get("limit")

        if not query_type or not limit_str:
            return Response(
                {'error': 'Параметры "type" и "limit" обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit_value = int(limit_str)
        except ValueError:
            return Response(
                {'error': 'Параметр "limit" должен быть числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if query_type == "user":
            media_qs = MediaFiles.objects.filter(user=request.user)[:limit_value]
        elif query_type == "all":
            media_qs = MediaFiles.objects.all()[:limit_value]
        else:
            return Response(
                {"error": 'Допустимые значения "type": "user" или "all"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not media_qs.exists():
            return Response({"error": "Записи не найдены"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MediaFilesSerializer(media_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===================================
#   NEWS VIEWS
# ===================================

class PostNewsView(APIView):
    """
    Создание новости с загрузкой медиафайлов (video_file).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = {
            'title': request.data.get('title'),
            'text': request.data.get('text'),
        }
        serializer = NewsSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        news_instance = serializer.save()
        media_files = request.FILES.getlist('media')
        for media_item in media_files:
            MediaFileNews.objects.create(
                news=news_instance,
                video_file=media_item
            )
        return Response(
            NewsSerializer(news_instance).data,
            status=status.HTTP_201_CREATED
        )


class GetNewsView(APIView):
    """
    Получение одной новости по её ID.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение новости по ID",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="ID новости",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: NewsSerializer(),
            400: "Не указан параметр id",
            404: "Новость не найдена"
        }
    )
    def get(self, request, *args, **kwargs):
        news_id = request.query_params.get('id')
        if not news_id:
            return Response(
                {"error": "Необходимо указать параметр 'id'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            news_obj = News.objects.get(id=news_id)
            serializer = NewsSerializer(news_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except News.DoesNotExist:
            return Response({'error': 'Новость не найдена'}, status=status.HTTP_404_NOT_FOUND)


class GetNewsListView(APIView):
    """
    Получение списка новостей, ограниченного параметром limit.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение списка новостей с ограничением по количеству (limit)",
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Сколько новостей нужно получить",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: NewsSerializer(many=True),
            400: "Некорректный параметр limit"
        }
    )
    def get(self, request, *args, **kwargs):
        limit_str = request.query_params.get('limit')
        if not limit_str:
            return Response(
                {"error": "Параметр 'limit' обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit_value = int(limit_str)
        except ValueError:
            return Response(
                {"error": "Параметр 'limit' должен быть числом"},
                status=status.HTTP_400_BAD_REQUEST
            )

        news_qs = News.objects.all()[:limit_value]
        serializer = NewsSerializer(news_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===================================
#   NEW FUNCTIONALITY: UPDATE/DELETE NEWS
# ===================================

class UpdateNewsView(APIView):
    """
    Обновление (PUT) новости по её ID. Допускает частичный апдейт (title/text).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def put(self, request, *args, **kwargs):
        news_id = request.query_params.get('id')
        if not news_id:
            return Response(
                {"error": "Необходимо указать параметр 'id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            news_obj = News.objects.get(id=news_id)
        except News.DoesNotExist:
            return Response(
                {"error": "Новость не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Сформируем обновлённые данные (partial update)
        updated_data = {}
        if 'title' in request.data:
            updated_data['title'] = request.data['title']
        if 'text' in request.data:
            updated_data['text'] = request.data['text']

        # Если пользователь не передал ничего для обновления
        if not updated_data:
            return Response(
                {"error": "Нет данных для обновления (title, text)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = NewsSerializer(
            news_obj,
            data=updated_data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Новость успешно обновлена"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteNewsView(APIView):
    """
    Удаление новости по её ID.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        news_id = request.query_params.get('id')
        if not news_id:
            return Response(
                {"error": "Необходимо указать параметр 'id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            news_obj = News.objects.get(id=news_id)
            news_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except News.DoesNotExist:
            return Response(
                {"error": "Новость не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )


# ===================================
#   UTILS / MISC
# ===================================

class CheckToken(APIView):
    """
    Проверяет валидность JWT-токена (Simple JWT).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {"message": "Авторизация успешна"},
            status=status.HTTP_200_OK
        )
