from django.urls import path
from .views import simkarta, simkarta_succes, simkarta_download


urlpatterns = [
    path('simkarta/', simkarta, name="simkarta"),
    path('simkarta/succes/', simkarta_succes, name='simkarta_succes'),
    path('simkarta-download/<str:filename>/', simkarta_download, name='simkarta_download'),
]