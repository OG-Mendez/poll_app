"""This code was written by Uchenna David using Microsoft Visual Studio 2022."""

"""
Definition of models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# The tag model is used to categorize questions under a psecific tag permitting users to create more than one question.
class Tag(models.Model):
    name = models.CharField(max_length=200)
    code =  models.IntegerField()
    def __str__(self):
        return self.name


# The anonymous model is used to store the name of users who vote anonymously.
class Anonymous(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# The question model is used to create a question with a unique tag and end time, the code is generated to identify the question.
class Question(models.Model):
    title = models.CharField(max_length=200)
    end_time = models.DateTimeField()
    unique_tag = models.CharField(max_length=9)
    code = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        return now() <= self.end_time

    def __str__(self):
        return self.title


# The choice model is used to create options for a question, the votes are stored in the database and the text is used to store custom text for the 'Others' option.
class Choice(models.Model):

    OPTION_CHOICES = [
        ("A", "Option A"),
        ("B", "Option B"),
        ("C", "Option C"),
        ("D", "Option D"),
        ("E", "Others")  
    ]
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choice_set')
    option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    votes = models.PositiveIntegerField(default=0)
    text = models.CharField(max_length=200, blank=True, null=True, help_text="Custom text for 'Others' option")

    def __str__(self):
        if self.option == 'E' and self.text: 
            return f"Others: {self.text}"
        return self.get_option_display()  

    class Meta:
        verbose_name_plural = "Choices"
        ordering = ['option']