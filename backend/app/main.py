from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.upload import router as upload_router
from app.api.routes.agent import router as agent_router
from app.api.routes.tool import router as tool_router

app = FastAPI(title="AI Career Elevate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default port
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",  # Vite alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_class=JSONResponse)
def health() -> dict:
    return {"status": "ok"}

app.include_router(upload_router)
app.include_router(agent_router)
app.include_router(tool_router)