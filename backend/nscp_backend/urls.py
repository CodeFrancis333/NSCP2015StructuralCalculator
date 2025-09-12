"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def catalog(_request):
    # Return whatever calculators you want to expose.
    # `slug` should match your future app routes.
    return JsonResponse({
        "calculators": [
            {"slug": "beams", "name": "Beam Calculator"},
            {"slug": "footing", "name": "Footing Calculator"},
            {"slug": "slab", "name": "Slab Calculator"},
            {"slug": "retaining-wall", "name": "Retaining Wall Calculator"},
            {"slug": "column", "name": "Column Calculator"},
        ]
    })

urlpatterns = [
    path("api/v1/catalog/", catalog),  # names come from backend
    path("api/v1/beams/", include(("apps.beams.urls", "beams"), namespace="beams")),
]
