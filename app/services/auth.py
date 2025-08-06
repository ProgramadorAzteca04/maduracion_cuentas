# app/services/reddit/auth.py
import subprocess
import time
import secrets
import string
import os
import random
import math

import pyautogui
import pyperclip
import pygetwindow as gw
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional


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
        x_ini, y_ini = pyautogui.position()
        dist = math.hypot(x_dest - x_ini, y_dest - y_ini)
        duration = max(0.3, min(1.5, dist / 1000))
        offset = random.randint(-100, 100)
        ctrl_x = (x_ini + x_dest) / 2 + offset
        ctrl_y = (y_ini + y_dest) / 2 - offset
        steps = max(10, int(dist / 25))

        for i in range(steps + 1):
            t = i / steps
            x = (1 - t)**2 * x_ini + 2 * (1 - t) * t * ctrl_x + t**2 * x_dest
            y = (1 - t)**2 * y_ini + 2 * (1 - t) * t * ctrl_y + t**2 * y_dest
            pyautogui.moveTo(x, y, duration=duration / steps)

    def find_and_click_humanly(self, locator: ElementLocator) -> bool:
        """Busca un elemento, mueve el ratón de forma humana y hace clic."""
        for attempt in range(locator.attempts):
            for image in locator.images:
                try:
                    pos = pyautogui.locateCenterOnScreen(image, confidence=locator.confidence)
                    if pos:
                        print(f"✅ Elemento encontrado con {os.path.basename(image)}.")
                        self._move_mouse_humanly(pos.x, pos.y)
                        pyautogui.click()
                        time.sleep(1)
                        return True
                except pyautogui.ImageNotFoundException:
                    continue
            if locator.wait_time > 0:
                print(f"Retraso de {locator.wait_time}s antes del siguiente intento.")
                time.sleep(locator.wait_time)
        print(f"❌ No se encontró el elemento con ninguna de las imágenes: {locator.images}")
        return False
        
    def type_text_humanly(self, text: str):
        """Escribe texto carácter por carácter para simular un humano."""
        print(f"⌨️ Escribiendo texto de forma humana: '{text}'")
        for char in text:
            if char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?':
                pyautogui.keyDown('shift')
                pyautogui.press(char.lower())
                pyautogui.keyUp('shift')
            else:
                pyautogui.press(char)
            time.sleep(random.uniform(0.05, 0.2))

    def get_and_focus_window(self, title: str) -> Optional[gw.Win32Window]:
        """Busca, activa y maximiza una ventana por su título."""
        print(f"🔍 Buscando ventana con el título '{title}'...")
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                window = windows[0]
                if window.isMinimized:
                    window.restore()
                window.maximize()
                window.activate()
                time.sleep(1)
                print("✅ Ventana encontrada y enfocada.")
                return window
            else:
                print("❌ No se encontró la ventana del navegador.")
                return None
        except Exception as e:
            print(f"❌ Error al buscar la ventana: {e}")
            return None

    def _perform_random_human_action(self, window: gw.Win32Window):
        """Realiza una acción aleatoria para romper la monotonía."""
        action = random.choice(['pause_long', 'move_subtle', 'scroll_corrective', 'pause_short'])
        
        if action == 'pause_long':
            duration = random.uniform(8, 15)
            print(f"🧘‍♂️ Interrupción: Pausa larga de {duration:.1f}s.")
            time.sleep(duration)
        elif action == 'move_subtle':
            print("🖱️ Interrupción: Movimiento sutil del ratón.")
            x, y = pyautogui.position()
            dx = random.randint(-150, 150)
            dy = random.randint(-150, 150)
            target_x = max(window.left, min(x + dx, window.left + window.width))
            target_y = max(window.top, min(y + dy, window.top + window.height))
            self._move_mouse_humanly(target_x, target_y)
        elif action == 'scroll_corrective':
            print("Interrupción: Scroll hacia arriba.")
            pyautogui.scroll(random.randint(200, 400))
            time.sleep(random.uniform(2, 4))
        else: # Pausa corta
            duration = random.uniform(3, 6)
            print(f"🧘 Interrupción: Pausa corta de {duration:.1f}s.")
            time.sleep(duration)

    def browse_with_scroll(self, window: gw.Win32Window, duration_seconds: int, human_action_prob: float = 0.05):
        """Orquesta la navegación con scroll fluido y acciones humanas."""
        print("\n--- 🚀 Iniciando Proceso de Navegación Humana ---")
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            if not gw.getWindowsWithTitle(window.title):
                print("❌ La ventana del navegador se cerró. Finalizando.")
                break
            window.activate()

            pyautogui.scroll(-random.randint(40, 70))
            time.sleep(random.uniform(0.4, 1.2))

            if random.random() < human_action_prob:
                self._perform_random_human_action(window)

        print("\n🏁 Tiempo de simulación finalizado.")


# ==============================================================================
# --- Orquestadores de Flujo ---
# ==============================================================================

def run_registration_flow(email: str, url: str):
    """Ejecuta el flujo completo de registro de Reddit."""
    service = AutomationService()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
    img_folder = os.path.join(project_root, 'img')
    print(f"✅ Usando carpeta de imágenes: {img_folder}")
    
    try:
        service.open_chrome_incognito(url)
        time.sleep(15)

        email_locator = ElementLocator(images=[os.path.join(img_folder, "correo_dark.png"), os.path.join(img_folder, "correo_light.png")], attempts=5)
        service.find_and_type(email_locator, email)

        continue_locator = ElementLocator(images=[os.path.join(img_folder, "continuar1.png"), os.path.join(img_folder, "continuar1_ligh.png")], attempts=10, wait_time=1)
        if not service.find_and_click(continue_locator):
            raise RuntimeError("No se pudo hacer clic en el primer 'Continuar'.")

        skip_locator = ElementLocator(images=[os.path.join(img_folder, "saltar.png"), os.path.join(img_folder, "saltar_ligh.png")], attempts=5, wait_time=2)
        service.find_and_click(skip_locator) # Es opcional, no aborta si falla

        user_locator = ElementLocator(images=[os.path.join(img_folder, "usuario.png"), os.path.join(img_folder, "usuario_ligh.png")], attempts=5, wait_time=2)
        username = service.get_username_from_field(user_locator)
        if not username:
            raise RuntimeError("No se pudo obtener el nombre de usuario.")

        password_locator = ElementLocator(images=[os.path.join(img_folder, "password_dark.png")], attempts=5, wait_time=2)
        password = service.generate_password()
        service.find_and_type(password_locator, password)

        if not service.find_and_click(continue_locator):
            raise RuntimeError("No se pudo hacer clic en el segundo 'Continuar'.")
        
        service.find_and_click(skip_locator)

        interest_locator = ElementLocator(images=[os.path.join(img_folder, "interes14.png")], attempts=10, wait_time=5)
        service.find_and_click(interest_locator)

        if not service.find_and_click(continue_locator):
            print("⚠️ No se pudo hacer clic en el 'Continuar' final, pero el proceso principal pudo haber funcionado.")
        
        print("\n✅ Proceso de registro finalizado.")
        print(f"📄 Datos guardados: Usuario='{username}', Contraseña='{password}'")

    except Exception as e:
        print(f"\n🚨 ERROR en el flujo de registro: {e}. Proceso abortado.")


def run_login_and_browse_flow(username: str, password: str, url: str, duration: int, window_title: str):
    """Ejecuta el flujo completo de login y navegación."""
    service = AutomationService()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
    img_folder = os.path.join(project_root, 'img')
    print(f"✅ Usando carpeta de imágenes: {img_folder}")

    try:
        service.open_chrome_incognito(url)
        time.sleep(5)

        active_window = service.get_and_focus_window(window_title)
        if not active_window:
            raise RuntimeError("No se pudo encontrar la ventana del navegador.")

        print("\n--- Iniciando Proceso de Login ---")
        
        email_locator = ElementLocator(images=[os.path.join(img_folder, "correo_dark.png"), os.path.join(img_folder, "correo_light.png")])
        if not service.find_and_click_humanly(email_locator):
            raise RuntimeError("No se encontró el campo de usuario.")
        service.type_text_humanly(username)

        password_locator = ElementLocator(images=[os.path.join(img_folder, "password_dark.png"), os.path.join(img_folder, "password_light.png")])
        if not service.find_and_click_humanly(password_locator):
            raise RuntimeError("No se encontró el campo de contraseña.")
        service.type_text_humanly(password)

        login_locator = ElementLocator(images=[os.path.join(img_folder, "start_dark.png"), os.path.join(img_folder, "start_light.png")])
        if not service.find_and_click_humanly(login_locator):
            raise RuntimeError("No se encontró el botón de login.")
        
        print("✅ Login completado. La navegación comenzará en 5 segundos.")
        time.sleep(5)
        
        service.browse_with_scroll(active_window, duration)

        print("\n✅ Proceso de login y navegación finalizado.")

    except Exception as e:
        print(f"\n🚨 ERROR en el flujo de login y navegación: {e}. Proceso abortado.")