# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from GPTv2 import OllamaGpt

app = FastAPI(
    title="Ollama GPT API",
    description="FastAPI backend for Qwen2.5 via Ollama",
    version="1.0.0"
)

gpt = OllamaGpt()


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = gpt.generate_response(request.message,request.thread_id)
    return {"response": reply}


@app.get("/health")
def health():
    return {"status": "ok"}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
