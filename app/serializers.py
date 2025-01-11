from rest_framework import serializers
from .models import Question, Choice


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
