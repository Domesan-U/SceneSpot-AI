import os
import shutil
import json
import time
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
from groq import Groq
from smtp_utils import send_mail_with_json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- CONFIG ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY") # Ensure this is loaded from .env or hardcoded
MODEL_NAME = "gemini-2.5-flash"          # Use standard model for best stability
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
INDICES_DIR = "indices"                  # <--- NEW: Folder to store the JSON files

# Ensure the folder exists
os.makedirs(INDICES_DIR, exist_ok=True)

print(f"Groq Key Loaded: {GROQ_API_KEY[:5]}...") # Security check
question_model = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def serve_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/player", response_class=HTMLResponse)
async def serve_player_page(request: Request):
    return templates.TemplateResponse("player.html", {"request": request})

# --- API ---
@app.post("/api/upload")
async def process_video(file: UploadFile = File(...)):
    # 1. Define the Index Path (Where we save the JSON)
    clean_name = file.filename.replace(" ", "_")
    index_path = f"{INDICES_DIR}/{clean_name}.json"

    # --- CACHE CHECK ---
    # If we already have the JSON file, skip the heavy AI work!
    if os.path.exists(index_path):
        print(f"⚡ CACHE HIT: Found existing index for {clean_name}")
        return {"status": "success", "filename": clean_name}

    # 2. Save Video to TEMP file (for upload only)
    temp_filename = f"temp_{int(time.time())}_{clean_name}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Upload to Gemini
        print(f"🚀 Uploading to AI: {temp_filename}")
        video_file = genai.upload_file(temp_filename)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            return JSONResponse(status_code=500, content={"error": "AI Failed"})

        # 4. Create Index
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = """
        Analyze this video. Create a JSON list of events.
        For each 5 second interval, provide:
        1. start (integer seconds)
        2. end (integer seconds)
        3. audio_description (describe clearly about what is said without changing the meaning, It should be like a actual subtitles)
        4. video_description (Clearly describe what is happening (i.e)-> a person(name if you know) in white dress holding some blue object and they are scary and fight is happening)
        JSON Format: [{"start": 0, "end": 5, "audio_description": "...","video_description": "..."}]
        """
        response = model.generate_content(
            [video_file, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # --- SAVE TO DISK (THE FIX) ---
        # Instead of saving to a variable, we write to a file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"✅ Index saved to: {index_path}")
        send_mail_with_json(index_path)
        
        return {"status": "success", "filename": clean_name}

    finally:
        # 5. Clean up the temp video file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print(f"🗑️ Deleted temp video: {temp_filename}")

@app.post("/api/ask")
async def ask_question(query: str = Form(...), filename: str = Form(...)):
    # 1. Locate the file on disk
    clean_name = filename.replace(" ", "_")
    index_path = f"{INDICES_DIR}/{clean_name}.json"
    
    if not os.path.exists(index_path):
        return {"found": False, "answer": "Index not found. Please re-upload."}

    # 2. Read the file
    with open(index_path, "r", encoding="utf-8") as f:
        video_log = f.read()

    # 3. Ask Groq
    prompt = f"""
    Video Log: {video_log}
    User Query: "{query}"
    Task: Find the BEST single scene.
    Return JSON ONLY: {{ "found": true, "start": 10, "end": 20, "answer": "..." }}
    """
    
    chat_completion = question_model.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a video assistant. Output ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile", # Changed to a valid Groq model name
        response_format={"type": "json_object"} # Force JSON mode if available
    )
    
    print("Groq Response:", chat_completion.choices[0].message.content)
    
    return json.loads(chat_completion.choices[0].message.content)