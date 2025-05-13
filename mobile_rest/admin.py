from django.contrib import admin
from .models import CustomUser, MediaFiles, MediaFile, MediaFileNews, News
admin.site.register(CustomUser)
admin.site.register(MediaFiles)
admin.site.register(MediaFile)
admin.site.register(News)
admin.site.register(MediaFileNews)
