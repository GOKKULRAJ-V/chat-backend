from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel, Field
from typing import Optional, Literal
import time
import uuid

app = FastAPI(title="Chat API", version="v1")

# Request/Response Models
class Context(BaseModel):
    email: Optional[str] = None
    channel: Optional[Literal["web", "whatsapp", "email"]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Context

class TriageFields(BaseModel):
    company: Optional[str] = None
    contact_email: Optional[str] = None
    region: Optional[str] = None
    product: Optional[str] = None
    quantity: int = 0
    urgency: Optional[str] = None

class Triage(BaseModel):
    intent: Literal["quotation", "followup", "support", "maintenance", "other"]
    confidence: float
    fields: TriageFields
    summary: str

class Meta(BaseModel):
    model: str
    latency_ms: int

class ChatResponse(BaseModel):
    reply: str
    triage: Triage
    meta: Meta

class ErrorResponse(BaseModel):
    error: dict

# Middleware to add version header
@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response

@app.get("/health")
async def health_check():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    start_time = time.time()
    
    # Validate message is not empty (though Pydantic already handles min_length=1)
    if not chat_request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BAD_REQUEST", "message": "Message cannot be empty"}}
        )
    
    # Mock response based on message content
    message_lower = chat_request.message.lower()
    
    # Determine intent based on keywords
    if any(word in message_lower for word in ["quote", "quotation", "price", "cost"]):
        intent = "quotation"
        confidence = 0.95
        summary = "User is requesting pricing information"
        reply = "I'll help you get a quote for that. Our sales team will contact you shortly with pricing details."
        fields = TriageFields(
            company="Example Corp" if "company" in message_lower else None,
            contact_email=chat_request.context.email,
            region="Texas" if "texas" in message_lower else None,
            product="centrifuge" if "centrifuge" in message_lower else None,
            quantity=2 if "2" in message_lower else 1,
            urgency="high" if "urgent" in message_lower else "medium"
        )
    elif any(word in message_lower for word in ["support", "help", "issue", "problem"]):
        intent = "support"
        confidence = 0.88
        summary = "User needs technical support"
        reply = "I understand you're experiencing an issue. Our support team will help you resolve this."
        fields = TriageFields(
            contact_email=chat_request.context.email,
            product="centrifuge" if "centrifuge" in message_lower else None,
            urgency="high" if "urgent" in message_lower else "medium"
        )
    elif any(word in message_lower for word in ["follow", "update", "status"]):
        intent = "followup"
        confidence = 0.82
        summary = "User is following up on previous interaction"
        reply = "I'll check the status of your previous request and get back to you."
        fields = TriageFields(
            contact_email=chat_request.context.email
        )
    elif any(word in message_lower for word in ["maintain", "service", "repair"]):
        intent = "maintenance"
        confidence = 0.90
        summary = "User is requesting maintenance services"
        reply = "I'll connect you with our maintenance team to schedule service."
        fields = TriageFields(
            company="Example Corp" if "company" in message_lower else None,
            contact_email=chat_request.context.email,
            region="Texas" if "texas" in message_lower else None,
            product="centrifuge" if "centrifuge" in message_lower else None
        )
    else:
        intent = "other"
        confidence = 0.75
        summary = "General inquiry requiring human review"
        reply = "Thank you for your message. I'll make sure the right team gets back to you."
        fields = TriageFields(
            contact_email=chat_request.context.email
        )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        reply=reply,
        triage=Triage(
            intent=intent,
            confidence=confidence,
            fields=fields,
            summary=summary
        ),
        meta=Meta(
            model="mock-v1",
            latency_ms=latency_ms
        )
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "BAD_REQUEST", "message": exc.detail}},
        headers={"X-API-Version": "v1"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)