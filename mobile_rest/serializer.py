from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import MediaFiles, MediaFile, MediaFileNews, News, CustomUser

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
        media_files = MediaFileNews.objects.filter(news = obj)
        return MediaFileNewsSerializer(media_files, many = True).data

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['id', 'video_file']

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
            raise serializers.ValidationError("Invalid credentials")

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