# endpoints.py
from fastapi import APIRouter, BackgroundTasks

# <<< MODIFICADO: Importamos el nuevo flujo y modelo de datos >>>
from app.services.reddit.auth import (
    run_registration_flow, 
    AutomationRequest,
    run_login_and_browse_flow,
    LoginAndBrowseRequest
)

# Creamos un router para organizar los endpoints de la API
router = APIRouter(
    prefix="/api/v1",  # Prefijo para todas las rutas en este archivo
    tags=["Automation"], # Etiqueta para la documentación de Swagger UI
)

@router.post("/register", status_code=202)
async def start_reddit_registration(request: AutomationRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar el proceso de registro de Reddit.
    Se ejecuta como una tarea en segundo plano para no bloquear la respuesta.
    """
    print(f"🚀 Petición recibida para registrar el correo: {request.email}")
    background_tasks.add_task(run_registration_flow, request.email, request.url)
    return {"message": "El proceso de registro ha comenzado en segundo plano."}

# <<< NUEVO: Endpoint para el login y la navegación >>>
@router.post("/login-and-browse", status_code=202)
async def start_login_and_browse(request: LoginAndBrowseRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar sesión en Reddit y simular navegación humana.
    Se ejecuta como una tarea de larga duración en segundo plano.
    """
    print(f"🚀 Petición recibida para iniciar sesión y navegar con el usuario: {request.username}")
    
    # Añadimos el nuevo flujo a las tareas en segundo plano
    background_tasks.add_task(
        run_login_and_browse_flow,
        request.username,
        request.password,
        request.url,
        request.duration_seconds,
        request.window_title
    )
    
    return {"message": "El proceso de login y navegación ha comenzado en segundo plano."}


@router.get("/health")
def health_check():
    """Endpoint de verificación para saber si el servicio está activo."""
    return {"status": "ok"}