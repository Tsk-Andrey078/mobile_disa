from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import MediaFiles, MediaFile, MediaFileNews, News, CustomUser
import boto3
from decouple import config

class MediaFileNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFileNews
        fields = ['id', 'video_file']


class NewsSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ['id', 'title', 'text', 'created_at', 'media']

    def get_media(self, obj):
        media_files = MediaFileNews.objects.filter(news=obj)
        return MediaFileNewsSerializer(media_files, many=True).data


class MediaFileSerializer(serializers.ModelSerializer):
    video_file = serializers.SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = ['id', 'video_file']

    def get_video_file(self, obj):
        if not obj.video_file:
            return None

        base_url = "https://video-oko-1.object.pscloud.io/"
        if not obj.video_file.startswith(base_url):
            return None

        # Получаем s3_key, удаляя base_url из video_file
        s3_key = obj.video_file[len(base_url):].strip().lstrip("/")

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=config("CLOUDFLARE_R2_ACCESS_KEY"),
            aws_secret_access_key=config("CLOUDFLARE_R2_SECRET_KEY"),
            endpoint_url=config("CLOUDFLARE_R2_BUCKET_ENDPOINT")
        )

        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': config("CLOUDFLARE_R2_BUCKET"), 'Key': s3_key},
            ExpiresIn=3600  # Ссылка будет действительна 1 час
        )

        return signed_url


class MediaFilesSerializer(serializers.ModelSerializer):
    videos = serializers.SerializerMethodField()

    class Meta:
        model = MediaFiles
        fields = ['id', 'user', 'city', 'street', 'description', 'was_at_date', 'was_at_time', 'uploaded_at', 'videos']

    def get_videos(self, obj):
        # Возвращаем сериализованные видеофайлы, связанные с текущей записью
        media_files = MediaFile.objects.filter(media=obj)
        return MediaFileSerializer(media_files, many=True).data


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'full_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            phone_number=validated_data['phone_number'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        # Попытка аутентификации через phone_number
        user = authenticate(username=phone_number, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        # Получаем токен и добавляем данные
        token = self.get_token(user)
        return {
            'access': str(token.access_token),
            'refresh': str(token),
            'full_name': user.full_name,
            'phone_number': user.phone_number,
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавляем пользовательские данные в токен
        token['full_name'] = user.full_name
        token['phone_number'] = user.phone_number

        return token
