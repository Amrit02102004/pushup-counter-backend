# Login/views.py
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth
from .models import User
from django.utils import timezone
import jwt
from mongodb import users_collection

JWT_SECRET_KEY = settings.JWT_SECRET_KEY

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
            },
            'last_login': timezone.now()
        }
        
        users_collection.update_one(
            {'userid': user_data['userid']},
            {'$set': user_data},
            upsert=True
        )

        token_data = {"email": user_data['email'], "uid": user_data['userid']}
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")

        return Response({
            "message": "Login successful", 
            "auth_token": token, 
            "userid": user_data['userid'], 
            "email": user_data['email']
        }, status=status.HTTP_200_OK)

    except auth.InvalidIdTokenError as e:
        return Response({"detail": f"Invalid token: {e}"}, status=status.HTTP_401_UNAUTHORIZED)
    except ValueError as ve:
        return Response({"detail": f"Invalid token error: {ve}"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"detail": f"Unexpected error during login: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
