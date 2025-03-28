from django.urls import path
from . import views

# Define the URL patterns for the app
urlpatterns = [ 
    path('login/', views.login_view_api, name='login'),
    path('signup/', views.signup_view_api, name='login'),
    path('api/scraper/', views.scraper_api, name='scraper'),
    path('api/create_poll/', views.create_poll, name='create_poll'),
    path('api/get_questions/', views.get_questions, name='get_questions'),
    path('api/vote/', views.vote, name='vote'),
    path('api/results/', views.results, name='results'),
]
