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


class ForumQuestion(models.Model):
    asked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questioned_by', default=1)
    question = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    upvote_question = models.ManyToManyField(User, related_name='upvoted_question', blank=True)
    downvote_question = models.ManyToManyField(User, related_name='downvoted_question', blank=True)
    notification = models.ManyToManyField(User, related_name='notification')

    def total_upvote_question(self):
        return self.upvote_question.count()

    def total_downvote_question(self):
        return self.downvote_question.count()

    def total_answers(self):
        return self.answers.count()


class Answer(models.Model):
    answered_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answered_by', default=1)
    question_replied = models.ForeignKey(ForumQuestion, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    upvote_answer = models.ManyToManyField(User, related_name='upvoted_answer', blank=True)
    downvote_answer = models.ManyToManyField(User, related_name='downvoted_answer', blank=True)
    parent_answer = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,
                                      related_name='child_answers')

    def get_conversation_thread(self):
        thread = [self]
        for child in self.child_answers.all().order_by('created_at'):
            thread.extend(child.get_conversation_thread())
        return thread

    def total_upvote_answer(self):
        return self.upvote_answer.count()

    def total_downvote_answer(self):
        return self.downvote_answer.count()

    def total_replies(self):
        return self.replies.count()


class Reply(models.Model):
    replied_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replied_by')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_replies', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_replies', blank=True)

    def __str__(self):
        return f"Reply by {self.replied_by.username} for Answer {self.answer.id}"

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_notification")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="question_notification")
    notify = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} will be notified if new answers to {self.question.question}"


class Apikey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='apikey_user')
    key = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"API Key for {self.user.username}"
    
    class Meta:
        verbose_name_plural = "API Keys"