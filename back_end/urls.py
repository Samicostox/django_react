from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()


urlpatterns = [
     path('', include(router.urls)),
     path('process_text/', views.ProcessTextView.as_view(), name='process_text'),
     path('ask_chatbot/', views.AskChatbotView.as_view(), name='ask_chatbot'),  
     path('signup/', views.SignUpView.as_view(), name='signup'),
     path('login/', views.LoginView.as_view(), name='login'),
     path('activate/<slug:uidb64>/<slug:token>/', views.activate, name='activate'),
     path('verify-email-code/', views.VerifyEmailCode.as_view(), name='verify-email-code'),
    
]