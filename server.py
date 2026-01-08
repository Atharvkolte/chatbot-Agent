from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from GPTv2 import OllamaGpt
import uvicorn

# -------------------- APP --------------------
app = FastAPI(
    title="GPTv2 API",
    description="FastAPI wrapper over Ollama Qwen2.5",
    version="1.0.0"
)

# -------------------- MODEL --------------------
bot = OllamaGpt()

# -------------------- SCHEMAS --------------------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# -------------------- ROUTES --------------------
@app.get("/")
def health_check():
    return {"status": "ok", "model": "qwen2.5:3b"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        response = bot.generate_response(req.message)
        return ChatResponse(reply=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- RUN --------------------
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
