from django.contrib import admin
from .models import CustomUser, MediaFiles, MediaFile
admin.site.register(CustomUser)
admin.site.register(MediaFiles)
admin.site.register(MediaFile)
