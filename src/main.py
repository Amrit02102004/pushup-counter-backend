import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv
import pymongo
import firebase_admin
from firebase_admin import credentials, auth
import cv2
import numpy as np
import mediapipe as mp
import jwt

# Load environment variables
load_dotenv()

# Initialize the exercise class
from exercise import Exercise
exercise = Exercise()

# Initialize Mediapipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MongoDB client
mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
db = client["pushup_counter"]
collection = db["profile"]

# Initialize Firebase Admin SDK
firebase_credentials = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
})
firebase_admin.initialize_app(firebase_credentials)

# JWT secret key
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic models
class PoseLandmarks(BaseModel):
    landmarks: List[Dict]
    feedback: str
    count: int
    image: str  # Hex string of the image

class Profile(BaseModel):
    gender: str
    dob: str
    height_feet: int
    height_inches: int
    weight: int
    weight_unit: str

class LoginRequest(BaseModel):
    id_token: str

class FirebaseMetadata(BaseModel):
    sign_in_provider: Optional[str] = None
    identities: Optional[Dict[str, List]] = None

class User(BaseModel):
    userid: str
    email: str
    username: str = Field(default="No username provided")
    profile_photo: str = Field(default="No profile photo")
    last_login: datetime = Field(default_factory=datetime.now)
    firebase_metadata: FirebaseMetadata = Field(default_factory=FirebaseMetadata)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
async def login(login_request: LoginRequest, response: Response):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(login_request.id_token)
        
        # Create User instance with data from decoded token
        user = User(
            userid=decoded_token['uid'],
            email=decoded_token.get('email', 'No email provided'),
            username=decoded_token.get('name', 'No username provided'),
            profile_photo=decoded_token.get('picture', 'No profile photo'),
            firebase_metadata=FirebaseMetadata(
                sign_in_provider=decoded_token.get('firebase', {}).get('sign_in_provider'),
                identities=decoded_token.get('firebase', {}).get('identities')
            )
        )
        
        # Update or insert user data in MongoDB
        db.users.update_one(
            {"userid": user.userid},
            {"$set": user.dict(by_alias=True)},
            upsert=True
        )
        
        # Create JWT token
        token_data = {"email": user.email, "uid": user.userid}
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")
        print(JWT_SECRET_KEY)
        # Set token in a cookie
        response.set_cookie(key="auth_token", value=token, httponly=True, max_age=3600)
        
        return {"message": "Login successful", "userid": user.userid, "email": user.email}

    except auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except ValueError as ve:
        raise HTTPException(status_code=401, detail=f"Invalid token error: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during login: {str(e)}")

@app.post("/profile-set")
async def profile_set(profile: Profile, email: str = Depends(get_current_user)):
    profile_data = {
        "email": email,
        "gender": profile.gender,
        "dob": profile.dob,
        "height_feet": profile.height_feet,
        "height_inches": profile.height_inches,
        "weight": profile.weight,
        "weight_unit": profile.weight_unit,
    }
    db["profiles"].update_one({"email": email}, {"$set": profile_data}, upsert=True)
    return JSONResponse(content={"message": "Profile set successfully"})

@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    # Read the image file
    contents = await file.read()
    np_img = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # Convert image to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = pose.process(img_rgb)

    # Check if landmarks are detected
    if result.pose_landmarks:
        # Define landmarks
        landmarks = []
        for lm in result.pose_landmarks.landmark:
            landmarks.append({'x': lm.x, 'y': lm.y, 'z': lm.z})

        # Check push-up form and get feedback
        completed = exercise.pushups(img, result.pose_landmarks.landmark, reps=10)
        feedback = exercise.get_feedback()
        count = exercise.counter

        # Draw landmarks and connections on the image
        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(img_rgb, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Convert image to bytes
        _, img_encoded = cv2.imencode('.jpg', img_rgb)
        img_bytes = img_encoded.tobytes()

        return JSONResponse(content={
            'feedback': feedback,
            'count': count,
            'landmarks': landmarks,
            'image': img_bytes.hex()  # Convert to hex string for easier handling
        })
    else:
        return JSONResponse(content={
            'feedback': 'No landmarks detected!',
            'count': exercise.counter,
            'landmarks': [],
            'image': ''
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
