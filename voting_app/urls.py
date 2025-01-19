"""
Definition of urls for voting_app.
"""

from datetime import datetime
from django.urls import include, path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('api/signup/', views.signup_view_api, name='signup'),
    path('api/login/', views.login_view_api, name='login'),
    path('api/logout/', views.logout_view_api, name='logout'),
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
