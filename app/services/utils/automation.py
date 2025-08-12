# app/services/reddit/auth.py
import subprocess
import time
import secrets
import string
import os

import pyautogui
import pyperclip
import pygetwindow as gw
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.utils.movement import (_move_mouse_humanly, _perform_random_human_action, browse_with_scroll,
    find_and_click_humanly, get_and_focus_window, type_text_humanly)


# ==============================================================================
# --- Modelos de Datos (Pydantic) ---
# ==============================================================================

class AutomationRequest(BaseModel):
    """Modelo para la solicitud de inicio de la automatización de registro."""
    url: str = Field(..., description="URL a la que se abrirá el navegador.", example="https://www.reddit.com/register/")
    email: str = Field(..., description="Correo electrónico para el registro.", example="tu.correo@ejemplo.com")


class LoginAndBrowseRequest(BaseModel):
    """Modelo para la solicitud de login y navegación."""
    url: str = Field(..., description="URL de login.", example="https://www.reddit.com/login")
    username: str = Field(..., description="Nombre de usuario para el login.")
    password: str = Field(..., description="Contraseña para el login.")
    duration_seconds: int = Field(3600, description="Duración total de la sesión de navegación en segundos.")
    window_title: str = Field("Reddit", description="Título de la ventana del navegador a buscar.")


class ElementLocator(BaseModel):
    """Define las propiedades para localizar un elemento en la pantalla."""
    images: List[str] = Field(..., description="Lista de nombres de archivo de imagen para buscar.")
    confidence: float = Field(0.85, description="Nivel de confianza para la coincidencia de imágenes.")
    wait_time: int = Field(0, description="Tiempo de espera en segundos antes de buscar.")
    attempts: int = Field(1, description="Número de intentos para encontrar el elemento.")


# ==============================================================================
# --- Clase de Servicio de Automatización (Lógica de Negocio) ---
# ==============================================================================

class AutomationService:
    """
    Servicio para manejar las tareas de automatización de la GUI para Reddit.
    Contiene métodos para registro, login y navegación.
    """

    def __init__(self, chrome_path: str = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"):
        """Inicializa el servicio con la ruta a Chrome."""
        self.chrome_path = chrome_path

    # --- Métodos Generales de Automatización ---

    def open_chrome_incognito(self, url: str):
        """Abre una nueva ventana de Chrome en modo incógnito en la URL especificada."""
        try:
            subprocess.Popen([self.chrome_path, "--incognito", url])
            print(f"🌐 Chrome abierto en modo incógnito: {url}")
        except FileNotFoundError:
            print(f"❌ No se encontró Chrome en la ruta: {self.chrome_path}")
            raise HTTPException(status_code=500, detail="No se encontró el ejecutable de Chrome.")

    def find_element_on_screen(self, locator: ElementLocator) -> Optional[tuple]:
        """Busca un elemento en la pantalla usando una o más imágenes."""
        for attempt in range(locator.attempts):
            if locator.wait_time > 0:
                time.sleep(locator.wait_time)
            
            for image in locator.images:
                try:
                    image_name = os.path.basename(image)
                    print(f"🔍 (Intento {attempt + 1}/{locator.attempts}) Buscando con: {image_name}")
                    location = pyautogui.locateOnScreen(image, confidence=locator.confidence)
                    if location:
                        print(f"✅ Elemento encontrado con {image_name} en: {location}")
                        return location
                except Exception as e:
                    print(f"⚠️ No se encontró la imagen {image} en este intento. Error: {e}")
            
            if locator.attempts > 1:
                pyautogui.scroll(-200)
                time.sleep(1)

        print(f"❌ Elemento no encontrado con ninguna de las imágenes: {locator.images}")
        return None

    def click_on_location(self, location: tuple):
        """Mueve el cursor al centro de una ubicación y hace clic."""
        center = pyautogui.center(location)
        pyautogui.moveTo(center, duration=0.25)
        pyautogui.click()
        print(f"🖱️ Clic realizado en: {center}")

    def find_and_click(self, locator: ElementLocator) -> bool:
        """Busca un elemento y hace clic en él si lo encuentra."""
        location = self.find_element_on_screen(locator)
        if location:
            self.click_on_location(location)
            return True
        return False

    def type_text(self, text: str, interval: float = 0.05):
        """Escribe texto usando el portapapeles para eficiencia."""
        try:
            original_clipboard = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            pyperclip.copy(original_clipboard)
            print(f"⌨️ Texto pegado: '{text}'")
        except Exception as e:
            print(f"⚠️ Error al pegar texto, usando escritura manual: {e}")
            pyautogui.write(text, interval=interval)

    def find_and_type(self, locator: ElementLocator, text: str):
        """Busca un campo, hace clic y escribe texto en él."""
        if self.find_and_click(locator):
            self.type_text(text)
        else:
            print(f"❌ No se encontró el campo para escribir: {locator.images}")
            raise RuntimeError(f"Fallo al buscar el campo para escribir.")

    # --- Métodos Específicos para Registro ---

    def generate_password(self, length: int = 12) -> str:
        """Genera una contraseña segura."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        print(f"🔒 Contraseña generada: {'*' * length}")
        return password

    def get_username_from_field(self, locator: ElementLocator) -> Optional[str]:
        """Obtiene el texto de un campo de nombre de usuario."""
        location = self.find_element_on_screen(locator)
        if location:
            self.click_on_location(location)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.3)
            username = pyperclip.paste()
            print(f"📋 Nombre de usuario obtenido: '{username}'")
            return username
        print("❌ No se encontró el campo de usuario.")
        return None

    # --- Métodos para Navegación "Humana" ---

    def _move_mouse_humanly(self, x_dest, y_dest):
        """Mueve el ratón a un destino usando una trayectoria curva (Bézier)."""
        return _move_mouse_humanly(x_dest, y_dest)

    def find_and_click_humanly(self, locator: ElementLocator) -> bool:
        """Busca un elemento, mueve el ratón de forma humana y hace clic."""
        return find_and_click_humanly(locator)
        
    def type_text_humanly(self, text: str):
        """Escribe texto carácter por carácter para simular un humano."""
        return type_text_humanly(text)

    def get_and_focus_window(self, title: str) -> Optional[gw.Win32Window]:
        """Busca, activa y maximiza una ventana por su título."""
        return get_and_focus_window(title)

    def _perform_random_human_action(self, window: gw.Win32Window):
        """Realiza una acción aleatoria para romper la monotonía."""
        return _perform_random_human_action(window)

    def browse_with_scroll(self, window: gw.Win32Window, duration_seconds: int, human_action_prob: float = 0.05):
        """Orquesta la navegación con scroll fluido y acciones humanas."""
        return browse_with_scroll(window, duration_seconds, human_action_prob)


