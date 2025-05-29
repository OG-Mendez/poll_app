"""
Definition of views.
"""

from math import perm
from random import sample, seed

from django.views.decorators.csrf import csrf_exempt
import requests
import os
from datetime import datetime
from optparse import Option
from django.utils.timezone import now
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import csrf_exempt
from .serializers import QuestionSerializer, AnswerSerializer, ForumQuestionSerializer, NotificationSerializer, ReplySerializer
from .models import ForumQuestion, Question, Choice, Answer, Reply, Notification, Apikey
from django.contrib.auth.models import User
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
from io import StringIO
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.db.models import Count


def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Account created successfully!')
            return redirect('login')

    return render(request, 'app/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('request_api_key')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'app/login.html')


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
    """
    Renders a form for scraping HTML tags from a given URL.
    On POST, scrapes the specified tags and displays or downloads the results as CSV.

    Args:
        request: Django HttpRequest object.

    Returns:
        Rendered HTML page or downloadable CSV file.
    """
    data = []
    error = None

    if request.method == "POST":
        url = request.POST.get("url")
        tags_str = request.POST.get("tags")

        if not url or not tags_str:
            error = "Please provide a URL and at least one tag."
        else:
            tags = [tag.strip() for tag in tags_str.split(',')]

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                all_elements_data = {}

                for tag in tags:
                    elements = soup.select(tag)
                    all_elements_data[tag] = [element.get_text(strip=True) for element in elements]

                max_len = max(len(items) for items in all_elements_data.values()) if all_elements_data else 0

                csv_data = [["Tag"] + [f"Item {i+1}" for i in range(max_len)]]
                for tag, items in all_elements_data.items():
                    row = [tag] + items + [""] * (max_len - len(items))
                    csv_data.append(row)

                data = csv_data

                if 'download' in request.POST:
                    output = StringIO()
                    writer = csv.writer(output)
                    for row in csv_data:
                        writer.writerow(row)

                    csv_content = output.getvalue()
                    response = HttpResponse(csv_content, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="scraped_data.csv"'
                    return response

            except requests.exceptions.RequestException as e:
                error = f"Error: {str(e)}"

    return render(request, 'app/scraper.html', {"data": data, "error": error})


# This function scrpaes data from a given URL and specified tags
@extend_schema(
    summary="Scrape data from a given URL and specified tags",
    description="Scrapes the content from the provided URL based on the specified tags and returns a downloadable CSV file.",
    parameters=[
        OpenApiParameter(name="url", description="The URL to scrape data from", required=True, type=str),
        OpenApiParameter(name="tags", description="Comma-separated list of tags to scrape", required=True, type=str),
    ],
    responses={
        200: OpenApiResponse(
            description="CSV file containing the scraped data",
            examples=[
                OpenApiExample(
                    "Sample CSV response",
                    value="Tag,Item 1,Item 2\nchange,Deep thoughts,Thinking\n",
                    media_type="text/csv",
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error response due to invalid input or request",
            examples=[
                OpenApiExample(
                    "Error message",
                    value={"error": "Both 'url' and 'tags' fields are required."}
                )
            ]
        ),
    }
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def scraper_api(request):
    url = request.data.get("url")
    tags_str = request.data.get("tags")
    data = []
    error = None

    if not url or not tags_str:
        return Response({"error": "Both 'url' and 'tags' fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    tags = [tag.strip() for tag in tags_str.split(',')]

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        all_elements_data = {}

        for tag in tags:
            elements = soup.select(tag)
            all_elements_data[tag] = [element.get_text(strip=True) for element in elements]

        
        max_len = max(len(items) for items in all_elements_data.values()) if all_elements_data else 0

        
        output = StringIO()
        writer = csv.writer(output)

       
        header = ["Tag"] + [f"Item {i+1}" for i in range(max_len)]
        writer.writerow(header)

        
        for tag, items in all_elements_data.items():
            row = [tag] + items + [""] * (max_len - len(items))
            writer.writerow(row)

        csv_content = output.getvalue()

        response = Response(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="scraped_data.csv"'
        return response

    except requests.exceptions.RequestException as e:
        error = f"Error: {str(e)}"
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
def get_apikey(request):
    """
    Generates or retrieves an API key for the authenticated user.
    If the user already has an API key, it returns the existing one.
    If not, it creates a new API key and returns it.
    """

    user = request.user
    existing = Apikey.objects.filter(user=user).first()
    if existing:
        return render(request, 'app/api_key_request.html', context)
    
    context = {}
    api_keys = [k for k in getattr(settings, 'API_KEYS', []) if k]
    if not api_keys:
        context['error'] = "No API keys are configured. Please contact support."
        return render(request, 'app/api_key_request.html', context)

    if request.method == "POST":
        api_key = random.choice(api_keys)
        context['api_key'] = api_key
        context['message'] = "Here is your API key."
        return render(request, 'app/api_key_request.html', context)

    return render(request, 'app/api_key_request.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_question(request):
    content = request.data.get('content')
    similarity_threshold = 0.7

    if not content:
        return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        new_question_embedding = model.encode(content, convert_to_numpy=True)

        existing_questions = ForumQuestion.objects.all()

        suggested_questions = []
        for existing_question in existing_questions:
            existing_embedding = model.encode(existing_question.question, convert_to_numpy=True)
            similarity = np.dot(new_question_embedding, existing_embedding) / (
                np.linalg.norm(new_question_embedding) * np.linalg.norm(existing_embedding)
            )

            if similarity >= similarity_threshold:
                suggested_questions.append({
                    'id': existing_question.id})
                break

        question = ForumQuestion.objects.create(asked_by=request.user, question=content)
        serializer = ForumQuestionSerializer(question)

        response_data = {
            'question': serializer.data,
            'suggested_similar_questions': suggested_questions
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="List all forum questions",
    description="Returns all forum questions ordered by creation date (newest first).",
    responses={
        200: OpenApiResponse(
            description="List of forum questions",
            examples=[OpenApiExample("Questions", value=[{"id": 1, "question": "Example?"}])]
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_questions(request):
    """
    Returns all forum questions ordered by creation date (newest first).

    Returns:
        200 OK: List of questions.
    """

    questions = ForumQuestion.objects.all().order_by('-created_at')
    serializer = ForumQuestionSerializer(questions, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get random forum questions for homepage",
    description="Returns up to 10 random forum questions for the authenticated user, seeded by user and date.",
    responses={
        200: OpenApiResponse(
            description="Random questions",
            examples=[OpenApiExample("Random questions", value={"random_questions": []})]
        ),
        500: OpenApiResponse(
            description="Error",
            examples=[OpenApiExample("Error", value={"error": "Some error message"})]
        ),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def homepage(request):
    """
    Returns up to 10 random forum questions for the authenticated user.
    The selection is seeded by user and date for consistency within a day.

    Returns:
        200 OK: List of random questions.
        500 Internal Server Error: On error.
    """

    try:
        user = request.user
        all_question_ids = list(ForumQuestion.objects.values_list('pk', flat=True))
        today = datetime.now().strftime("%Y-%m-%d")  # Format: "YYYY-MM-DD"
        seed(f"{user.id}-{today}")
        random_question_ids = sample(all_question_ids, min(10, len(all_question_ids)))
        random_questions = ForumQuestion.objects.filter(pk__in=random_question_ids)
        serializer = ForumQuestionSerializer(random_questions, many=True)

        return Response({'random_questions': serializer.data})

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@extend_schema(
    summary="Create an answer for a forum question",
    description="Creates an answer for a forum question. If a similar answer exists, it is threaded.",
    request={
        "application/json": {
            "example": {
                "content": "This is my answer to the question."
            }
        }
    },
    parameters=[
        OpenApiParameter(name="id", description="ForumQuestion ID", required=True, type=int),
    ],
    responses={
        201: OpenApiResponse(
            description="Answer created",
            examples=[OpenApiExample("Success", value={
                "new_answer": {"id": 1, "content": "This is my answer to the question."},
                "conversation_thread": []
            })]
        ),
        400: OpenApiResponse(
            description="Error",
            examples=[OpenApiExample("Error", value={"error": "Content is required"})]
        ),
        404: OpenApiResponse(
            description="Question not found",
            examples=[OpenApiExample("Error", value={"error": "Question not found"})]
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_answer(request):
    """
    Creates an answer for a forum question. If a similar answer exists, it is threaded.
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")
    similarity_threshold = 0.7

    question_id = request.query_params.get("id")
    content = request.data.get('content')
    if not content:
        return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = ForumQuestion.objects.get(id=question_id)
        existing_answers = Answer.objects.filter(question_replied=question).order_by('-created_at')

        new_answer_embedding = model.encode(content, convert_to_numpy=True)

        parent_answer = None

        for answer in existing_answers:
            existing_embedding = model.encode(answer.content, convert_to_numpy=True)
            similarity = np.dot(new_answer_embedding, existing_embedding) / (
                np.linalg.norm(new_answer_embedding) * np.linalg.norm(existing_embedding)
            )

            if similarity >= similarity_threshold:
                parent_answer = answer
                break

        answer = Answer.objects.create(answered_by=request.user, question_replied=question, content=content, parent_answer=parent_answer)

        thread = answer.get_conversation_thread()
        serializer = AnswerSerializer(thread, many=True)

        return Response({
            'new_answer': AnswerSerializer(answer).data,
            'conversation_thread': serializer.data
        }, status=status.HTTP_201_CREATED)

    except ForumQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="List answers for a forum question",
    description="Returns all answers for a given forum question, ordered by net score and creation date.",
    parameters=[
        OpenApiParameter(name="id", description="ForumQuestion ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="List of answers",
            examples=[OpenApiExample("Answers", value=[{"id": 1, "content": "Answer text"}])]
        ),
        404: OpenApiResponse(
            description="Question not found",
            examples=[OpenApiExample("Error", value={"error": "Question not found"})]
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_answers(request):
    """
    Returns all answers for a given forum question, ordered by net score and creation date.

    Query Params:
        id: ForumQuestion ID

    Returns:
        200 OK: List of answers.
        404 Not Found: If question does not exist.
    """

    question_id = request.query_params.get("id")
    try:
        question = ForumQuestion.objects.get(id=question_id)
        answers = Answer.objects.filter(question_replied=question).annotate(
            net_score=Count('upvote_answer') - Count('downvote_answer')
        ).order_by('-net_score', '-created_at')

        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)
    except ForumQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="List answers in stacked/threaded format",
    description="Returns answers for a forum question in a threaded (stacked) format.",
    parameters=[
        OpenApiParameter(name="id", description="ForumQuestion ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="Stacked answers",
            examples=[OpenApiExample("Stacked", value=[{"stack": [{"id": 1, "content": "Answer"}]}])]
        ),
        404: OpenApiResponse(
            description="Question not found",
            examples=[OpenApiExample("Error", value={"error": "Question not found"})]
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_answers_stacked(request):
    """
    Returns answers for a forum question in a threaded (stacked) format.

    Query Params:
        id: ForumQuestion ID

    Returns:
        200 OK: List of answer threads.
        404 Not Found: If question does not exist.
    """

    question_id = request.query_params.get("id")
    try:
        question = ForumQuestion.objects.get(id=question_id)
        answers = Answer.objects.filter(question_replied=question, parent_answer__isnull=True).order_by('-created_at')

        conversation_threads = []
        for answer in answers:
            thread = answer.get_conversation_thread()
            conversation_threads.append({
                'stack': AnswerSerializer(thread, many=True).data
            })

        return Response(conversation_threads)

    except ForumQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Create a reply to an answer",
    description="Creates a reply to a specific answer.",
    request={
        "application/json": {
            "example": {
                "content": "This is a reply to the answer."
            }
        }
    },
    parameters=[
        OpenApiParameter(name="id", description="Answer ID", required=True, type=int),
    ],
    responses={
        201: OpenApiResponse(
            description="Reply created",
            examples=[OpenApiExample("Success", value={"id": 1, "content": "This is a reply to the answer."})]
        ),
        400: OpenApiResponse(
            description="Error",
            examples=[OpenApiExample("Error", value={"error": "Content is required"})]
        ),
        404: OpenApiResponse(
            description="Answer not found",
            examples=[OpenApiExample("Error", value={"error": "Answer not found"})]
        ),
    }
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reply(request):
    """
    Creates a reply to a specific answer.
    """

    answer_id = request.query_params.get("id")
    content = request.data.get('content')
    if not content:
        return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        answer = Answer.objects.get(id=answer_id)
        reply = Reply.objects.create(replied_by=request.user, answer=answer, content=content)
        serializer = ReplySerializer(reply)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Answer.DoesNotExist:
        return Response({'error': 'Answer not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="List replies for an answer",
    description="Returns all replies for a given answer, ordered by creation date.",
    parameters=[
        OpenApiParameter(name="id", description="Answer ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="List of replies",
            examples=[OpenApiExample("Replies", value=[{"id": 1, "content": "Reply text"}])]
        ),
        404: OpenApiResponse(
            description="Answer not found",
            examples=[OpenApiExample("Error", value={"error": "Answer not found"})]
        ),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_replies(request):
    """
    Returns all replies for a given answer, ordered by creation date.

    Query Params:
        id: Answer ID

    Returns:
        200 OK: List of replies.
        404 Not Found: If answer does not exist.
    """

    answer_id = request.query_params.get('id')
    try:
        answer = Answer.objects.get(id=answer_id)
        replies = Reply.objects.filter(answer=answer).order_by('-created_at')
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)
    except Answer.DoesNotExist:
        return Response({'error': 'Answer not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Vote on a forum question",
    description="Upvote or downvote a forum question.",
    request={
        "application/json": {
            "example": {
                "action": "upvote"
            }
        }
    },
    parameters=[
        OpenApiParameter(name="id", description="ForumQuestion ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="Vote successful",
            examples=[OpenApiExample("Success", value={
                "message": "Question upvoted successfully!",
                "total_upvotes": 5,
                "total_downvotes": 2
            })]
        ),
        400: OpenApiResponse(
            description="Invalid action",
            examples=[OpenApiExample("Error", value={"error": "Invalid action"})]
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_forumquestion(request):
    """
    Upvote or downvote a forum question.
    """

    question_id = request.query_params.get('id')
    question = get_object_or_404(ForumQuestion, id=question_id)
    action = request.data.get('action')

    if action not in ['upvote', 'downvote']:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'upvote':
        if request.user in question.downvote_question.all():
            question.downvote_question.remove(request.user)
        question.upvote_question.add(request.user) if request.user not in question.upvote_question.all() else question.upvote_question.remove(request.user)
    else:
        if request.user in question.upvote_question.all():
            question.upvote_question.remove(request.user)
        question.downvote_question.add(request.user) if request.user not in question.downvote_question.all() else question.downvote_question.remove(request.user)

    return Response({'message': f'Question {action}d successfully!', 'total_upvotes': question.upvote_question.count(), 'total_downvotes': question.downvote_question.count()}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Vote on an answer",
    description="Upvote or downvote an answer.",
    request={
        "application/json": {
            "example": {
                "id": 1,
                "action": "upvote"
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description="Vote successful",
            examples=[OpenApiExample("Success", value={
                "message": "Answer upvoted successfully!",
                "total_upvotes": 3,
                "total_downvotes": 1
            })]
        ),
        400: OpenApiResponse(
            description="Invalid action",
            examples=[OpenApiExample("Error", value={"error": "Invalid action"})]
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_answer(request):
    """
    Upvote or downvote an answer.
    """

    answer_id = request.data.get('id')
    answer = get_object_or_404(Answer, id=answer_id)
    action = request.data.get('action')
    if action not in ['upvote', 'downvote']:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'upvote':
        if request.user in answer.downvote_answer.all():
            answer.downvote_answer.remove(request.user)
        answer.upvote_answer.add(request.user) if request.user not in answer.upvote_answer.all() else answer.upvote_answer.remove(request.user)
    else:
        if request.user in answer.upvote_answer.all():
            answer.upvote_answer.remove(request.user)
        answer.downvote_answer.add(request.user) if request.user not in answer.downvote_answer.all() else answer.downvote_answer.remove(request.user)

    return Response({'message': f'Answer {action}d successfully!', 'total_upvotes': answer.upvote_answer.count(), 'total_downvotes': answer.downvote_answer.count()}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Like or dislike a reply",
    description="Like or dislike a reply to an answer.",
    request={
        "application/json": {
            "example": {
                "action": "like"
            }
        }
    },
    parameters=[
        OpenApiParameter(name="id", description="Reply ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="Action successful",
            examples=[OpenApiExample("Success", value={
                "message": "Review liked successfully!",
                "reply_id": 1,
                "total_likes": 2,
                "total_dislikes": 0
            })]
        ),
        400: OpenApiResponse(
            description="Invalid action",
            examples=[OpenApiExample("Error", value={"error": "Invalid action. Use \"like\" or \"dislike\"."})]
        ),
        404: OpenApiResponse(
            description="Reply not found",
            examples=[OpenApiExample("Error", value={"error": "Review not found"})]
        ),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_dislike_reply(request):
    """
    Like or dislike a reply to an answer.
    """

    reply_id = request.query_params.get('id')
    reply = get_object_or_404(Reply, id=reply_id)
    action = request.data.get('action')
    if not reply_id or not action:
        return Response({'error': 'Reply ID and action are required'}, status=status.HTTP_400_BAD_REQUEST)

    if action not in ['like', 'dislike']:
        return Response({'error': 'Invalid action. Use "like" or "dislike".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if action == 'like':
            if request.user in reply.dislikes.all():
                reply.dislikes.remove(request.user)
            reply.likes.add(request.user)
        elif action == 'dislike':
            if request.user in reply.likes.all():
                reply.likes.remove(request.user)
            reply.dislikes.add(request.user)

        return Response({
            'message': f'Review {action}d successfully!',
            'reply_id': reply.id,
            'total_likes': reply.likes.count(),
            'total_dislikes': reply.dislikes.count()
        }, status=status.HTTP_200_OK)

    except Reply.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
   

@extend_schema(
    summary="Set or get notification for a forum question",
    description="Set notification for a forum question (POST) or get notification status (GET).",
    request={
        "application/json": {
            "example": {
                "notification": "yes"
            }
        }
    },
    parameters=[
        OpenApiParameter(name="id", description="ForumQuestion ID", required=True, type=int),
    ],
    responses={
        200: OpenApiResponse(
            description="Notification set or retrieved",
            examples=[
                OpenApiExample("Set", value={"message": "Notification set for question 1"}),
                OpenApiExample("Get", value=[{"id": 1, "notify": True}])
            ]
        ),
        404: OpenApiResponse(
            description="Question not found",
            examples=[OpenApiExample("Error", value={"error": "Question does not exist"})]
        ),
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def question_notification(request):
    """
    Set notification for a forum question (POST) or get notification status (GET).
    """

    question_id = request.query_params.get("id")
    noti = request.data.get('notification')

    try:
        question = ForumQuestion.objects.get(id=question_id)

        if request.method == "POST":
            if noti.lower() == 'yes':
                notify, created = Notification.objects.get_or_create(user=request.user, defaults={'notify': True}, question=question)
            return Response({
                "message": f"Notification {'updated' if not created else 'set'} for question {question.id}"
            }, status=status.HTTP_200_OK)

        elif request.method == "GET":
            notifications = Notification.objects.filter(question=question, user=request.user)

            serializer = NotificationSerializer(notifications, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
    except ForumQuestion.DoesNotExist:
        return Response({'error': 'Question does not exist'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notify_user(request):
    """
    Returns notifications for the authenticated user about questions they are following
    that have received new answers since notification was set.

    Returns:
        200 OK: List of notifications.
    """
    data = []
    for notification in Notification.objects.filter(user=request.user, notify=True):
        question = ForumQuestion.objects.get(id=notification.question.id)
        answer = Answer.objects.filter(question=question)
        if answer.created_at >= notification.created_at:
            data.append({question: 'A question you are interested in has been answered'})

    return Response(data, status=status.HTTP_200_OK)


# Everything below is default Microsoft Visual Studio 2022 code snippet for Django and was not tampered with
def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/layout.html',
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

