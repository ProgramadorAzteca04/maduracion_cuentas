# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1.endpoints import reddit_autogui
settings = get_settings()

# Crea las tablas en la base de datos

app = FastAPI(
    title="My FastAPI App",
    debug=settings.DEBUG,
    version="1.0.0"
)

app.include_router(
    reddit_autogui.router,
    prefix="/reddit",
    tags=["Reddit Automation"]
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Reddit Clone"}