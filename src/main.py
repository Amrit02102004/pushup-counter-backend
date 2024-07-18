import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import pymongo
from exercise import Exercise
import cv2
import numpy as np
import mediapipe as mp
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Initialize the exercise class
exercise = Exercise()

# Initialize Mediapipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MongoDB client
mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
db = client["pushup_counter"]
collection = db["profile"]

# JWT secret and algorithm
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://spent-one.vercel.app/" , "http://localhost:5173"],  # Allow only "spent-org.com"
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Define the data model for the response
class PoseLandmarks(BaseModel):
    landmarks: list[dict]
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

class User(BaseModel):
    email: EmailStr

def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode = {"exp": expire, "sub": email}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.post("/login")
async def login(user: User):
    existing_user = db["users"].find_one({"email": user.email})
    if not existing_user:
        # Create a new user if it doesn't exist
        db["users"].insert_one({"email": user.email})
    
    access_token = create_access_token(email=user.email)
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

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
