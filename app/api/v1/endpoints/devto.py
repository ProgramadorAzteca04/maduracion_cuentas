from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.devto.devto_autogui import interaction_devto, register_devto, login_devto, logout_devto

# Configura el logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

router = APIRouter()

# Modelo de datos de la solicitud para el registro
class DevtoRegisterRequest(BaseModel):
    email: str
    name: str
    username: str
    password: str

@router.post("/register")
async def register_via_autogui(request: DevtoRegisterRequest):
    try:
        
        logging.info("Iniciando el proceso de registro en dev.to...")
        result = await register_devto(
            name=request.name,
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        if result.get("captcha_detected"):
            return {"message": "Registro completado, pero se detectó un CAPTCHA. Por favor, resuélvelo manualmente."}
        
        return {"message": "Registro completado exitosamente en dev.to."}
    
    except Exception as e:
        logging.exception(f"Error inesperado durante el proceso de registro: {e}")
        raise HTTPException(status_code=500, detail="Hubo un error durante el proceso de registro.")

# Modelo de datos de la solicitud para el logeo
class DevtoLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login_via_autogui(request: DevtoLoginRequest):
    try:
        
        logging.info("Iniciando el proceso de login en dev.to...")
        result = await login_devto(
            email=request.email,
            password=request.password
        )
        
        if not result.get("success"):
            logging.error(f"Error durante el login: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {"message": "Login completado exitosamente en dev.to."}

    except Exception as e:
        logging.exception(f"Error inesperado durante el proceso de login: {e}")
        raise HTTPException(status_code=500, detail="Hubo un error durante el proceso de login.")

@router.post("/logout")
async def logout_via_autogui():
    try:

        logging.info("Iniciando el proceso de logout en dev.to...")
        result = await logout_devto(20)
        if not result.get("success"):
            logging.error(f"Error durante el logout: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {"message": "Logout completado exitosamente en dev.to."}

       
    except Exception as e:
        logging.exception(f"Error inesperado durante el proceso de logout: {e}")
        raise HTTPException(status_code=500, detail="Hubo un error durante el proceso de logout.")

# Modelo de datos de la solicitud para el logeo
class DevtoMadurateRequest(BaseModel):
    email: str
    password: str
    path_url: str

@router.post("/madurate")
async def madurate_via_autogui(request: DevtoMadurateRequest):
    try:
        
        logging.info("Iniciando el proceso de login e interaccion en dev.to...")
        result = await interaction_devto(
            email=request.email,
            path_url=request.path_url,
            password=request.password
        )
        
        if not result.get("success"):
            logging.error(f"Error durante proceso: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {"message": "Proceso completado exitosamente "}

    except Exception as e:
        logging.exception(f"Error inesperado durante el proceso de interaccion: {e}")
        raise HTTPException(status_code=500, detail="Hubo un error durante el proceso de interaccion.")

