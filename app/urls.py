from django.urls import path
from . import views

# Define the URL patterns for the app
urlpatterns = [ 
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('api/login/', views.login_view_api, name='login_api'),
    path('api/signup/', views.signup_view_api, name='signup_api'),
    path('api/scraper/', views.scraper_api, name='scraper_api'),
    path('api/create_poll/', views.create_poll, name='create_poll'),
    path('api/get_questions/', views.get_questions, name='get_questions'),
    path('api/vote/', views.vote, name='vote'),
    path('api/results/', views.results, name='results'),
    path('request_api_key/', views.get_apikey, name='request_api_key'),
    #path('api/create_question/', views.create_question, name='create_question'),
    path('api/forum_questions/', views.list_questions, name='list_questions'),
    #path('api/create_answer/', views.create_answer, name='create_answer'),
    path('api/answers/', views.list_answers, name='list_answers'),
    path('api/stacked_answers/', views.list_answers_stacked, name='list_answers_stacked'),
    path('api/create_reply/', views.create_reply, name='create_reply'),
    path('api/replies/', views.list_replies, name='list_replies'),
    path('api/homepage/', views.homepage, name='homepage'),
    path('api/vote_forumquestion/', views.vote_forumquestion, name='vote_forumquestion'),
    path('api/vote_answer/', views.vote_answer, name='vote_answer'),
    path('api/like_dislike_reply/', views.like_dislike_reply, name='like_dislike_reply'),
    path('api/question_notification/', views.question_notification, name='question_notification'),
    path('api/notify_user/', views.notify_user, name='notify_user')
]
