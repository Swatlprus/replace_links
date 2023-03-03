from django.urls import path
from .views import upload_mailing, download


urlpatterns = [
    path('', upload_mailing, name="upload_mailing"),
    path('download/', download),
]