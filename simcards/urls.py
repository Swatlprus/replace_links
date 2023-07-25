from django.urls import path
from .views import application_generation, display_results, download_docx


urlpatterns = [
    path('simcards/', application_generation, name="application_generation"),
    path('simcards/result/', display_results, name='display_results'),
    path('simcards-download/<str:filename>/', download_docx, name='download_docx'),
]