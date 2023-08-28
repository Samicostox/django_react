from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
     path('process_text/', views.ProcessTextView.as_view(), name='process_text'),
]