from django.urls import path
from .views import SendVerificationCodeView, VerifyCodeAndRegisterView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('send-code/', SendVerificationCodeView.as_view(), name='send_code'),
    path('verify-code/', VerifyCodeAndRegisterView.as_view(), name='verify_code'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]