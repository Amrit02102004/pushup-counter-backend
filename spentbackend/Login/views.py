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

        response = JsonResponse({"message": "Login successful", "userid": user.userid, "email": user.email})
        response.set_cookie(key="auth_token", value=token, httponly=True, max_age=3600)

        return response

    except auth.InvalidIdTokenError as e:
        return Response({"detail": f"Invalid token: {e}"}, status=status.HTTP_401_UNAUTHORIZED)
    except ValueError as ve:
        return Response({"detail": f"Invalid token error: {ve}"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"detail": f"Unexpected error during login: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def profile_set(request):
    email = request.data.get('email')
    profile_data = request.data

    profiles_collection.update_one({"email": email}, {"$set": profile_data}, upsert=True)
    return Response({"message": "Profile set successfully"}, status=status.HTTP_200_OK)
