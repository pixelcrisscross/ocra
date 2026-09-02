from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS
from session_store import SessionStore, init_db
from agents.orchestrator import Orchestrator
from routers.chat import router as chat_router
from routers.data import router as data_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.orca = Orchestrator(SessionStore())
    yield


app = FastAPI(
    title="ORCA Marine Intelligence API",
    version="2.0.0",
    description="Agentic marine decision-support backend with conversational AI, live ocean data, official hazard feeds, INCOIS enrichment, PFZ evidence, geofencing, route analysis and provenance.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(data_router)


@app.get("/")
def root():
    return {"name": "ORCA Marine Intelligence API", "version": "2.0.0", "docs": "/docs", "chat": "/api/chat", "websocket": "/api/chat/ws/{conversation_id}"}


@app.get("/health")
def health():
    return {"status": "ok"}
