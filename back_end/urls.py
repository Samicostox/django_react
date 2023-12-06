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
     path('generate_requirements_pdf/', views.GenerateRequirementsPDF.as_view(), name='generate_requirements_pdf'),
     path('fetch_venues/', views.FetchVenuesView.as_view(), name='fetch_venues'),
     path('user_pdfs/', views.FetchUserPDFsView.as_view(), name='retrieve-user-pdfs'),
     path('retrieve_user_info/', views.RetrieveUserInfo.as_view(), name='retrieve_user_info'),
     path('add_university/', views.AddUniversityView.as_view(), name='add-university'),
     path('coldoutreach/', views.FetchUserPhoneCSVsView.as_view(), name='coldoutreach'),
     path('emailcsv/', views.FetchUserEmailCSVsView.as_view(), name='emailcsv'),
     path('usercsv/', views.FetchUserCSVsView.as_view(), name='emailcsv'),
     path('update_user/', views.UpdateUserInfo.as_view(), name='update-user-info'),
     path('generate_pdf_after/', views.GenerateCustomRequirementsPDF.as_view(), name='generate_pdf_after'),
     path('delete_csv/', views.DeleteUserCSVView.as_view(), name='delete_csv'),
     path('delete_pdf/', views.DeleteUserPDFView.as_view(), name='delete_pdf'),
     path('forgot-password/', views.ForgotPassword.as_view(), name='forgot-password'),
     path('reset-password/', views.ResetPassword.as_view(), name='reset-password'),
     path('create_client/', views.CreateClientView.as_view(), name='create-client'),
     path('fetch_all_clients/', views.FetchAllClientsView.as_view(), name='fetch-all-clients'),
     path('fetch_all_users/', views.FetchAllUsersView.as_view(), name='fetch-all-users'),
     path('chatbot/', views.ChatBotView.as_view(), name='chatbot'),
    
]