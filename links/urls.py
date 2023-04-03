from django.urls import path
from .views import home, upload_mailing, succes, download
from django.urls import path


urlpatterns = [
    path('mailing/', upload_mailing, name="upload_mailing"),
    path('mailing/succes/', succes, name="succes"),
    path('download/<str:filename>/', download, name='download'),
]