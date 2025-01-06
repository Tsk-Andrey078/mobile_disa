from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

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

    username = None  # Убираем стандартное поле username
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.phone_number