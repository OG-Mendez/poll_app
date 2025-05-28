from django.contrib import admin
from app.models import Tag, Anonymous, Question, Choice, ForumQuestion, Answer, Reply, Notification, Apikey


# Register your models here.
admin.site.register(Tag)
admin.site.register(Anonymous)  
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(ForumQuestion)
admin.site.register(Answer)
admin.site.register(Reply)  
admin.site.register(Notification)
admin.site.register(Apikey)