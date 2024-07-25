from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import jwt

from Login.models import User 
from .models import UserProfile
from .serializers import UserProfileSerializer

@api_view(['GET'])
def get_user_profile(request):
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        return Response({"message": "Authentication token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token_data = jwt.decode(auth_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        email = token_data.get('email')
        if not email:
            return Response({"message": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = User.objects.get(email=email)
        user_profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except UserProfile.DoesNotExist:
        return Response({"message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def set_user_profile(request):
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        return Response({"message": "Authentication token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token_data = jwt.decode(auth_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        email = token_data.get('email')
        if not email:
            return Response({"message": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    profile_data = request.data
    if 'dob' in profile_data:
        profile_data['dob'] = profile_data['dob'].split('T')[0]  # Ensure date format is correct

    try:
        user = User.objects.get(email=email)
        # Ensure profile_data includes required fields
        required_fields = ['gender', 'dob', 'height_feet', 'height_inches', 'weight', 'weight_unit']
        for field in required_fields:
            if field not in profile_data:
                return Response({"message": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

        user_profile, created = UserProfile.objects.update_or_create(
            user=user,
            defaults=profile_data
        )

        if created:
            return Response({"message": "Profile set successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)