"""
Definition of views.
"""

from math import perm
import requests
from datetime import datetime
from optparse import Option
from django.utils.timezone import now
import random
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .serializers import QuestionSerializer
from .models import Question, Choice
from django.contrib.auth.models import User
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from bs4 import BeautifulSoup


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already taken'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    user.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'message': 'User created successfully', 'token': token.key}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Invalid credentials, please check to make sure the email and/or password is correct'},
            status=status.HTTP_400_BAD_REQUEST)

     
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view_api(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_400_BAD_REQUEST)



# The create_poll view is used to create a poll with a unique tag, end time, and choices.
@extend_schema(
    summary="Create a poll",
    description="Create a new poll with a unique tag, end time, and a list of choices.",
    request={
        "application/json": {
            "example": {
                "tag": "poll123",
                "question": "What's your favorite color?",
                "end_time": "2025-01-15T12:00:00Z",
                "choices": [
                    {"text": "Red"},
                    {"text": "Blue"},
                    {"text": "Green"}
                ]
            }
        }
    },
    responses={
        201: OpenApiResponse(
            description="Poll created successfully",
            examples=[
                OpenApiExample(
                    "Poll created successfully",
                    value={"message": "Poll created successfully, write down the TAG: poll123"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error message",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "All fields are required"}
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
        for option, text in choice_option.items():
            Choice.objects.create(question=question_instance, text=text, option=option)
        
    return Response({"message": f"Poll created successfully, write down the TAG: {question_instance.unique_tag} and the code: {question_instance.code}"}, status=status.HTTP_201_CREATED)


# The get_questions view is used to get the question and choices for a poll using the tag and code.
@extend_schema(
    summary="Get questions and choices for a poll",
    description="Retrieve questions and their choices based on the provided tag and code.",
    parameters=[
        OpenApiParameter(name="tag", description="Unique tag of the poll", required=True, type=str),
        OpenApiParameter(name="code", description="Code of the poll", required=True, type=str),
    ],
    responses={
        200: OpenApiResponse(
            description="List of questions and choices",
            examples=[
                OpenApiExample(
                    "List of questions and choices",
                    value=[
                        {
                            "id": 1,
                            "question": "What's your favorite color?",
                            "choices": [
                                {"text": "Red"},
                                {"text": "Blue"},
                                {"text": "Green"}
                            ]
                        }
                    ]
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error message",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "Both tag and code are required."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_questions(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')

    if not tag or not code:
        return Response({"error": "Both tag and code are required."}, status=status.HTTP_400_BAD_REQUEST)

    questions = Question.objects.filter(unique_tag=tag, code=code)

    if not questions.exists():
        return Response({"error": "Invalid tag or code"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        [
            {
                "id": question.id,
                "question": question.title,
                "choices": [{"option": choice.option, "text": choice.text} for choice in question.choice_set.all()],
            }
            for question in questions
        ],
        status=status.HTTP_200_OK,
    )


# The vote view is used to submit a vote for a poll using the tag, code, and choice.
@extend_schema(
    summary="Submit a vote for a poll",
    description="Cast a vote for a specific choice in a poll using the tag and code.",
    parameters=[
        OpenApiParameter(name="tag", description="Unique tag of the poll", required=True, type=str),
        OpenApiParameter(name="code", description="Code of the poll", required=True, type=str),
    ],
    request={
        "application/json": {
            "example": {
                "question_id": 1,
                "choice": "Blue"
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description="Vote submitted successfully",
            examples=[
                OpenApiExample(
                    "Vote submitted successfully",
                    value={"message": "Vote submitted successfully."}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error message",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "Tag and code are required."}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Error message",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "Invalid choice or question."}
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')

    if not tag or not code:
        return Response({"error": "Tag and code are required."}, status=status.HTTP_400_BAD_REQUEST)

    questions = Question.objects.filter(unique_tag=tag, code=code)
    if not questions.exists():
        return Response({"error": "Invalid tag or code."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        question_id = request.data.get('question_id')  
        choice = request.data.get('choice')
        try:
            question = questions.get(id=question_id)
            selected_choice = question.choice_set.get(option=choice)
        except (Question.DoesNotExist, Choice.DoesNotExist):
            return Response({"error": "Invalid choice or question."}, status=status.HTTP_404_NOT_FOUND)

        selected_choice.votes += 1  
        selected_choice.save()
        return Response({"message": "Vote submitted successfully."}, status=status.HTTP_200_OK)


# The results view is used to get the results of a poll using the tag and code.
@extend_schema(
    summary="Get results of a poll",
    description="Retrieve poll results, including votes per choice, using tag and code.",
    parameters=[
        OpenApiParameter(name="tag", description="Unique tag of the poll", required=True, type=str),
        OpenApiParameter(name="code", description="Code of the poll", required=True, type=str),
    ],
    responses={
        200: OpenApiResponse(
            description="List of questions with choices and votes",
            examples=[
                OpenApiExample(
                    "List of questions with choices and votes",
                    value=[
                        {
                            "id": 1,
                            "question": "What's your favorite color?",
                            "choices": [
                                {"A": "Red", "votes": 10},
                                {"B": "Blue", "votes": 20},
                                {"C": "Green", "votes": 5}
                            ]
                        }
                    ]
                )
            ]
        ),
        404: OpenApiResponse(
            description="No polls found or polls haven't ended",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "No polls found or polls haven't ended."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def results(request):
    tag = request.query_params.get('tag')
    code = request.query_params.get('code')

    if not tag or not code:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    questions = Question.objects.filter(unique_tag=tag, code=code, end_time__lte=now())

    if not questions.exists():
        return Response({"error": "No polls found or polls haven't ended."}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        [
            {
                "id": question.id,
                "question": question.title,
                "choices": [{"option": choice.option, "text": choice.text, "votes": choice.votes} for choice in question.choice_set.all()],
            }
            for question in questions
        ],
        status=status.HTTP_200_OK,
    )



def scraper(request):
    data = []
    error = None
    
    if request.method == "POST":
        url = request.POST.get("url")  
        tag = request.POST.get("tag")  
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  
            
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(tag)  
            
            data = [element.get_text(strip=True) for element in elements]
            
        except requests.exceptions.RequestException as e:
            error = f"Error: {str(e)}"
    
    return render(request, 'app/scraper.html', {"data": data, "error": error})


@api_view(['POST'])
@permission_classes([AllowAny])
def scraper_api(request):
    url = request.data.get("url")
    tag = request.data.get("tag")
    data = []
    error = None

    if not url or not tag:
        return Response({"error": "Both 'url' and 'tag' fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select(tag)

        data = [element.get_text(strip=True) for element in elements]

    except requests.exceptions.RequestException as e:
        error = f"Error: {str(e)}"
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"data": data}, status=status.HTTP_200_OK)


# Everything below is default Microsoft Visual Studio 2022 code snippet for Django and was not tampered with
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

