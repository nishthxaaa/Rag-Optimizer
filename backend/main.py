import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router as http_router
from backend.api.chat import router as ws_router

app = FastAPI(
    title="RAG Optimizer API",
    description="Autonomous self-optimizing RAG pipeline",
    version="1.0.0",
)

# Allow the React dev server to call the API
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
production_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
] + production_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")


@app.get("/")
async def root():
    return {"message": "RAG Optimizer API is running."}