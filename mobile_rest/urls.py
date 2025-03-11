from django.urls import path
from .views import SendVerificationCodeView, VerifyCodeAndRegisterView, CustomTokenObtainPairView, RegisterDeviceView, MediaFileUploadView, MediaFilesListView, MediaFilesDetailView, GetNewsListView, GetNewsView, PostNewsView, CheckToken, MediaFilesCreateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version='v1',
        description="API documentation for your mobile backend",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('sentry-debug/', trigger_error),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('send-code/', SendVerificationCodeView.as_view(), name='send_code'),
    path('verify-code/', VerifyCodeAndRegisterView.as_view(), name='verify_code'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register-device/', RegisterDeviceView.as_view(), name='register_device'),
    path('mediafiles/upload/', MediaFilesCreateView.as_view(), name='mediafiles-create'),
    path('mediafiles/upload-media/', MediaFileUploadView.as_view(), name='mediafiles-upload-media'),
    path('mediafiles/detail/', MediaFilesDetailView.as_view(), name='mediafiles-detail'),
    path('mediafiles/list/', MediaFilesListView.as_view(), name='mediafiles-list'),
    path('news/upload/', PostNewsView.as_view(), name='news-upload'),
    path('news/detail/', GetNewsView.as_view(), name='news-detail'),
    path('news/list/', GetNewsListView.as_view(), name='news-list'),
    path('check-token', CheckToken.as_view(), name='check-token')
]
