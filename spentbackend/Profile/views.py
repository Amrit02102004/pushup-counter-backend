
# Profile/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
import jwt
from mongodb import users_collection, profiles_collection

JWT_SECRET_KEY = settings.JWT_SECRET_KEY

@api_view(['GET'])
def get_user_profile(request):
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        return Response({"message": "Authentication token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token_data = jwt.decode(auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = token_data.get('email')
        uid = token_data.get('uid')
        if not email or not uid:
            return Response({"message": "Invalid token data"}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    user = users_collection.find_one({'userid': uid})
    if not user:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    profile = profiles_collection.find_one({'user_id': uid})
    if not profile:
        return Response({"message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

    # Remove MongoDB's _id field
    profile.pop('_id', None)
    return Response(profile)

@api_view(['POST'])
def set_user_profile(request):
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        return Response({"message": "Authentication token is missing"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token_data = jwt.decode(auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = token_data.get('email')
        uid = token_data.get('uid')
        if not email or not uid:
            return Response({"message": "Invalid token data"}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    profile_data = request.data
    if 'dob' in profile_data:
        profile_data['dob'] = profile_data['dob'].split('T')[0]

    required_fields = ['gender', 'dob', 'height_feet', 'height_inches', 'weight', 'weight_unit']
    for field in required_fields:
        if field not in profile_data:
            return Response({"message": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

    profile_data['user_id'] = uid
    profile_data['email'] = email
    profile_data['updated_at'] = timezone.now()

    result = profiles_collection.update_one(
        {'user_id': uid},
        {'$set': profile_data},
        upsert=True
    )

    if result.matched_count:
        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Profile set successfully"}, status=status.HTTP_201_CREATED)