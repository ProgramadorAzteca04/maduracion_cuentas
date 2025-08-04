from fastapi import APIRouter, HTTPException
from app.services.reddit_autogui import RedditAutoGUIService
from pydantic import BaseModel

router = APIRouter()

class RedditRegisterRequest(BaseModel):
    email: str
    username: str
    password: str

@router.post("/register")
async def register_via_autogui(request: RedditRegisterRequest):
    service = RedditAutoGUIService()
    success = service.register_account(
        email=request.email,
        username=request.username,
        password=request.password
    )
    if not success:
        raise HTTPException(status_code=500, detail="Error en PyAutoGUI")
    return {"message": "Flujo completado. Verifica captchas manualmente."}