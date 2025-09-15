# backend/apps/beams/urls.py
from django.urls import path
from .views import BeamCalcView

urlpatterns = [
    path("calc/", BeamCalcView.as_view(), name="calc"),  # ← add slash
]
