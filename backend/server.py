from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from SimpleGPT import SimpleGPT

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

# Initialize the bot
try:
    bot = SimpleGPT()
except Exception as e:
    print(f"Error initializing bot: {e}")
    bot = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):   # here we are giving the input by calling in the frontend files throught the api function takes the request
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    try:
        response_message = bot.generate_response(request.message, thread_id=request.thread_id) #generating
        return ChatResponse(response=str(response_message.content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "SimpleGPT API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
