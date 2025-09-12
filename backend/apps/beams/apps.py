# backend/apps/beams/apps.py
from django.apps import AppConfig

class BeamsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.beams"   # ← important if you use the apps/ container
    label = "beams"
