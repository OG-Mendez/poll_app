from rest_framework import serializers
from .models import Question, Choice, ForumQuestion, Answer, Notification, Reply


class ChoiceSerializer(serializers.ModelSerializer):
    """Serializer for question choices"""
    class Meta:
        model = Choice
        fields = ['id', 'option', 'text']

class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions"""
    choices = ChoiceSerializer(many=True, read_only=True, source='choice_set')  

    class Meta:
        model = Question
        fields = ['id', 'title', 'end_time', 'unique_tag', 'code', 'created_at', 'created_by', 'choices']

class AnswerSerializer(serializers.ModelSerializer):
    net_score = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ['id', 'question_replied', 'answered_by', 'content', 'created_at', 'net_score', 'total_replies']

    def get_net_score(self, obj):
        return obj.upvote_answer.count() - obj.downvote_answer.count()

    def get_total_replies(self, obj):
        return obj.total_replies.count()


class ForumQuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True, source='answers.all')

    class Meta:
        model = ForumQuestion
        fields = ['id', 'asked_by', 'question', 'created_at', 'upvote_question', 'downvote_question', 'answers',
                  'total_answers']

    def get_net_score(self, obj):
        return obj.upvote_answer.count() - obj.downvote_answer.count()

    def get_total_answers(self, obj):
        return obj.total_answers.count()


class ReplySerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = ['id', 'replied_by', 'answer', 'content', 'created_at', 'likes', 'dislikes']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

