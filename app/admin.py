from django.contrib import admin
from app.models import Tag, Anonymous, Question, Choice


# Register your models here.
admin.site.register(Tag)
admin.site.register(Anonymous)  
admin.site.register(Question)
admin.site.register(Choice)