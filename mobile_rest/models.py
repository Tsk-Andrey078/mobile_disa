from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number must be set")
        extra_fields.setdefault("is_active", True)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=255)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",  # Измените related_name
        blank=True,
        verbose_name="groups",
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",  # Измените related_name
        blank=True,
        verbose_name="user permissions",
        help_text="Specific permissions for this user.",
        related_query_name="customuser",
    )
    objects = CustomUserManager()

    username = None  # Убираем стандартное поле username
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.phone_number
    
class MediaFiles(models.Model):
    id = models.AutoField(primary_key=True)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    description = models.TextField()
    video_file = models.FileField(upload_to='/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title