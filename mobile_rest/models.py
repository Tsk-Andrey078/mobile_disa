from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.db import models
from django.utils.timezone import now

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password = None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number must be set")
        extra_fields.setdefault("is_active", True)
        user = self.model(phone_number = phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length = 15, unique = True)
    full_name = models.CharField(max_length = 255, default = None, blank = True, null = True)

    groups = models.ManyToManyField(
        Group,
        related_name = "customuser_set",  # Измените related_name
        blank = True,
        verbose_name = "groups",
        help_text = "The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_query_name = "customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name = "customuser_set",  # Измените related_name
        blank = True,
        verbose_name = "user permissions",
        help_text = "Specific permissions for this user.",
        related_query_name = "customuser",
    )
    objects = CustomUserManager()

    username = None  # Убираем стандартное поле username
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.phone_number

class VerificationCode(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Код действителен 5 минут
        return (now() - self.created_at).seconds > 300

class MediaFile(models.Model):
    id = models.AutoField(primary_key = True)
    media = models.ForeignKey('MediaFiles', on_delete = models.CASCADE, related_name = 'videos')
    video_file = models.FileField(upload_to='video/', blank=True, default=None, null=True)

class MediaFiles(models.Model):
    id = models.AutoField(primary_key = True)
    user = models.ForeignKey(CustomUser, on_delete = models.CASCADE)
    city = models.CharField(max_length = 255)
    street = models.CharField(max_length = 255)
    description = models.TextField()
    was_at_date = models.DateField()
    was_at_time = models.TimeField()
    uploaded_at = models.DateTimeField(auto_now_add = True)
    status = models.CharField(max_length = 16)

class MediaFileNews(models.Model):
    id = models.AutoField(primary_key = True)
    news = models.ForeignKey('News', on_delete = models.CASCADE, related_name = 'media')
    video_file = models.FileField(upload_to ='video/')

class News(models.Model):
    id = models.AutoField(primary_key = True)
    title = models.CharField(max_length=512)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)