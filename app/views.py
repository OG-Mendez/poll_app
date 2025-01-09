"""
Definition of views.
"""

from datetime import datetime
from django.utils.timezone import now
import random
from random import choices
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .serializers import QuestionSerializer
from .models import Question, Choice, Anonymous
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token


@api_view(['POST'])
@permission_classes([AllowAny])
def create_poll(request):
    tag = request.data.get('tag')
    question = request.data.get('question')
    end_time = request.data.get('end_time')
    choices = request.data.get('choices')

    if not tag or not question or not end_time or not choices:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    code = random.randint(100000, 999999)

    question_instance = Question.objects.create(
        title=question, 
        end_time=end_time, 
        unique_tag=tag,
        code=code,
        created_by=request.user)

    for choice_option in choices:
        Choice.objects.create(question=question_instance, option=choice_option['option'], text=choice_option.get('text'))
        
    return Response({"message": f"Poll created successfully, write down the TAG: {question_instance.unique_tag} and the code: {question_instance.code}"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_questions(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')

    if not tag or not code:
        return Response({"error": "Both tag and code are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = Question.objects.get(unique_tag=tag, code=code)
    except Question.DoesNotExist:
        return Response({"error": "Invalid tag or code"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "question": question.title,
            "choices": [choice.option for choice in question.choice_set.all()],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def vote(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')
    if not tag or not code:
        return Response({"error": "Tag and code are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = Question.objects.get(unique_tag=tag, code=code)
        if question.end_time < now():
            return Response({"error": "Poll has ended."}, status=status.HTTP_400_BAD_REQUEST)
    except Question.DoesNotExist:
        return Response({"error": "Invalid tag or code."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        choice = request.data.get('choice')
        try:
            selected_choice = question.choice_set.get(option=choice)
        except Choice.DoesNotExist:
            return Response({"error": "Invalid choice."}, status=status.HTTP_404_NOT_FOUND)
        
        selected_choice.votes += 1  
        selected_choice.save()
        return Response({"message": "Vote submitted successfully."}, status=status.HTTP_200_OK)
    elif request.method == 'GET':
        return Response({
            "question": question.title,
            "choices": [{"option": c.option, "text": c.text} for c in question.choice_set.all()],
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def results(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')
    
    if not tag or not code:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = Question.objects.get(unique_tag=tag, code=code)
        if question.end_time > now():
            serializer = QuestionSerializer(question)
            return Response(serializer.data)
    except Question.DoesNotExist:
        return Response({"error": "Poll not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({"error": "Unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )
