from django.contrib import admin
from .models import CustomUser, MediaFiles
admin.site.register(CustomUser)
admin.site.register(MediaFiles)