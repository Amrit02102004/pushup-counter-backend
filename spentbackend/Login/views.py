# Login/views.py

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth
from .models import User
from .serializers import UserSerializer
from pymongo import MongoClient
import os
from .models import UserProfile
from .serializers import UserProfileSerializer
from django.core.exceptions import ObjectDoesNotExist
# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["pushup_counter"]
profiles_collection = db["profile"]

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

@api_view(['POST'])
def login(request):
    id_token = request.data.get('id_token')

    try:
        decoded_token = auth.verify_id_token(id_token)
        user_data = {
            'userid': decoded_token['uid'],
            'email': decoded_token.get('email', 'No email provided'),
            'username': decoded_token.get('name', 'No username provided'),
            'profile_photo': decoded_token.get('picture', 'No profile photo'),
            'firebase_metadata': {
                'sign_in_provider': decoded_token.get('firebase', {}).get('sign_in_provider'),
                'identities': decoded_token.get('firebase', {}).get('identities')
            }
        }
        
        user, created = User.objects.update_or_create(
            userid=user_data['userid'], defaults=user_data
        )

        token_data = {"email": user.email, "uid": user.userid}
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")

        return JsonResponse({"message": "Login successful", "auth_token": token, "userid": user.userid, "email": user.email})

    except auth.InvalidIdTokenError as e:
        return Response({"detail": f"Invalid token: {e}"}, status=status.HTTP_401_UNAUTHORIZED)
    except ValueError as ve:
        return Response({"detail": f"Invalid token error: {ve}"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"detail": f"Unexpected error during login: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)@api_view(['POST'])

@api_view(['POST'])
def profile_set(request):
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        return Response({"message": "Authentication token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token_data = jwt.decode(auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = token_data.get('email')
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    if not email:
        return Response({"message": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except ObjectDoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    profile_data = request.data
    profile_data['dob'] = profile_data.get('dob').split('T')[0]  # Ensure date format is correct

    try:
        user_profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(user_profile, data=profile_data)
    except UserProfile.DoesNotExist:
        serializer = UserProfileSerializer(data=profile_data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"message": "Profile set successfully"}, status=status.HTTP_200_OK)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)