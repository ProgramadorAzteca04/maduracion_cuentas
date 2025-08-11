
import logging
import dotenv
import pyautogui
import time
import webbrowser
import pyperclip
import requests
import difflib
import pygetwindow as gw  
from pathlib import Path
from bs4 import BeautifulSoup
from twocaptcha import TwoCaptcha
from app.services.utils.movement import _move_mouse_humanly
from app.services.utils.automation import AutomationService
from app.images.images_catalog import IMAGE_MAP
from app.services.utils.dictionary_images import resolve_in_project


# Configuración
dotenv.load_dotenv()

# Instanciamos el cliente de 2Captcha
captcha_api_key = dotenv.get_key(".env", "CAPTCHA_API_KEY")
logging.info(f"Clave API de 2Captcha: {captcha_api_key}")
solver = TwoCaptcha(captcha_api_key)

# Configuración de pyautogui
pyautogui.PAUSE = 0.15
pyautogui.FAILSAFE = True  # mueve el mouse a la esquina sup-izq para abortar

# Configuración de logging
logging.basicConfig(level=logging.INFO)

# constantes
TEMPO_ESPERA = 2
CONFIDENCE = 0.8
BROWSER_URL = 'https://dev.to'

# funciones

# Función para abrir el navegador
def open_browser( url = BROWSER_URL):
    logging.info("Abriendo navegador...")
    webbrowser.open(url)
    time.sleep(TEMPO_ESPERA * 3)

# Función para localizar la imagen en la pantalla con reintentos
def locate_on_screen_with_retry(image_path: str, retries: int = 3, confidence: float = CONFIDENCE):
    for attempt in range(retries):
        try:
            button = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if button:
                return pyautogui.center(button)
            else:
                logging.warning(f"Intento {attempt + 1}/{retries}: No se encontró la imagen {image_path}.")
        except Exception as e:
            logging.error(f"Error al intentar localizar la imagen {image_path}: {e}")
        time.sleep(TEMPO_ESPERA)
    logging.error(f"No se pudo localizar la imagen {image_path} tras {retries} intentos.")
    return None

# Función para hacer clic en el botón
def click_button(button_image: str):
    logging.info(f"Buscando botón con imagen {button_image}...")
    center = locate_on_screen_with_retry(button_image)
    if center:
        # pyautogui.moveTo(center, duration=0.5)
        _move_mouse_humanly(center.x, center.y)
        pyautogui.click(center)
        logging.info(f"Hiciste clic en el botón {button_image}.")
        return True
    return False

# Función para escribir el correo
def escribir_correo(correo: str):
    try:
        if '@' not in correo:
            logging.error(f"Correo inválido: {correo}")
            return False
        usuario, dominio = correo.split('@')
        pyautogui.write(usuario, interval=0.1)
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('alt')
        pyautogui.press('q')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('ctrl')
        pyautogui.write(dominio, interval=0.1)
        return True
    except Exception as e:
        logging.error(f"Error escribiendo el correo: {e}")
        return False

# Función para escribir en los campos de entrada
def buscar_y_escribir(imagen: str, texto: str):
    logging.info(f"🔍 Buscando imagen '{imagen}' y escribiendo en el campo...")
    input_field = locate_on_screen_with_retry(imagen)
    if input_field:
        _move_mouse_humanly(input_field.x, input_field.y)
        pyautogui.click(input_field)
        if '@' in texto:
            escribir_correo(texto)
        else:
            pyautogui.write(texto, interval=0.1)
        return True
    return False

def open_and_focus_window(title: str, path_url: str, service: AutomationService = AutomationService()):
    """    Abre una nueva ventana del navegador y la enfoca.    """
    service.open_chrome_incognito(path_url)
    time.sleep(5)
    pyautogui.hotkey('alt', 'tab')
    active_window = service.get_and_focus_window(title)
    # logging.info(f"👋 Bienvenido a {title}")
    if not active_window:
        raise RuntimeError("No se pudo encontrar la ventana del navegador.")

    return active_window

# Manejo de CAPTCHA
def handle_captcha_manual():
    try:
        captcha_images = [
            r"app/img/devto/captcha_img.png",
            r"app/img/devto/captcha_verify.png"
        ]
        for image in captcha_images:
            captcha = locate_on_screen_with_retry(image)
            if captcha:
                logging.info(f"Captcha '{image}' encontrado, por favor resuélvelo manualmente.")
                time.sleep(TEMPO_ESPERA * 5) 
                # pyautogui.hotkey('ctrl', 'w')
                return
        logging.info("No se encontró captcha, procesando...")
    except Exception as e:
        logging.error(f"Error al manejar el CAPTCHA: {e}")


## funciones para el manejo del captcha por twocaptcha

# Manejo de CAPTCHA twocaptcha
def handle_captcha_twocaptcha():
    try:
        captcha_images = [
            r"app/img/devto/captcha_img.png",
            r"app/img/devto/captcha_verify.png"
        ]
        for image in captcha_images:
            captcha = locate_on_screen_with_retry(image)
            if captcha:
                try:
                    logging.info(f"Captcha '{image}' encontrado")
                    # Si el CAPTCHA es un reCAPTCHA v2, usamos el método `reCaptchaV2`
                    captcha_url = get_current_url()
                    html = fetch_html(captcha_url)
                    keys = get_sitekeys_from_div_grecaptcha(html)
                    site_key = keys[0] if keys else None
                    result = solver.recaptcha(
                        url=captcha_url, 
                        sitekey=site_key
                    )

                    logging.info(f"Resultado del CAPTCHA: {result}")
                except Exception as e:
                    logging.error(f"Error al resolver el CAPTCHA: {e}")
                return
        logging.info("No se encontró captcha, procesando...")
    except Exception as e:
        logging.error(f"Error al manejar el CAPTCHA: {e}")

# Función para activar una ventana por su título
def _activate_window_by_title(partial_title: str, wait=0.5) -> bool:
    """Activa la primera ventana cuyo título contenga partial_title (case-insensitive)."""
    if gw is None:
        return False
    try:
        matches = [w for w in gw.getAllTitles() if partial_title.lower() in w.lower()]
        if not matches:
            return False
        win = gw.getWindowsWithTitle(matches[0])[0]
        win.activate()
        time.sleep(wait)
        return True
    except Exception:
        return False

# Función para obtener la URL actual del navegador
def get_current_url(preserve_clipboard: bool = True, focus_hint: str | None = None, wait: float = 0.25) -> str:
    """
    Obtiene la URL de la pestaña activa del navegador actual.
    - preserve_clipboard: si True, restaura el portapapeles original.
    - focus_hint: texto para identificar y activar la ventana del navegador (p.ej. 'Chrome', 'Edge', 'Firefox').
    """
    # (Opcional) trae al frente la ventana objetivo por título
    original_clip = pyperclip.paste() if preserve_clipboard else None
    if focus_hint:
        _activate_window_by_title(focus_hint)

    # Enfoca omnibox y copia su contenido
    pyautogui.hotkey("ctrl", "l")  # también sirve Alt+D
    time.sleep(wait)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(wait)

    url = (pyperclip.paste() or "").strip()

    # Limpieza y restauración del portapapeles si se pidió
    if preserve_clipboard and original_clip is not None:
        # Devuelve el texto original al portapapeles sin perder el valor retornado
        pyperclip.copy(original_clip)

    return url

# funcion para obtener el HTML de una página
def fetch_html(url: str, timeout=15) -> str:
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    r = requests.get(url, headers={"User-Agent": ua}, timeout=timeout)
    r.raise_for_status()
    return r.text

# funcion para obtener los sitekeys de un div de reCAPTCHA
def get_sitekeys_from_div_grecaptcha(html: str) -> list[str]:
    """
    Devuelve una lista (sin duplicados) de valores 'data-sitekey'SOLO para nodos <div class="g-recaptcha"
    """
    soup = BeautifulSoup(html, "html.parser")
    keys = []
    for node in soup.select("div.g-recaptcha[data-sitekey]"):
        k = node.get("data-sitekey")
        if k and k not in keys:
            keys.append(k)
    return keys


# funcion que importa imagen segun la key en un diccionario
def get_image_abs_path(key: str, suggest: bool = True) -> Path:
    """
    Devuelve la ruta ABSOLUTA OS a partir de la key del catálogo.
    Si no encuentra la key, lanza KeyError con sugerencias cercanas.
    """
    rel = IMAGE_MAP.get(key)
    if rel is None:
        if suggest:
            keys = list(IMAGE_MAP.keys())
            cerca = difflib.get_close_matches(key, keys, n=5, cutoff=0.6)
            hint = f"  ¿Quisiste decir?: {', '.join(cerca)}" if cerca else "  No hay sugerencias."
        else:
            hint = ""
        raise KeyError(f"Key no encontrada: '{key}'.{hint}")
    return rel


















# Función para presionar Tab y navegar entre los campos de la página
def navigate_tabs_on_page(num_range=7):
    logging.info("Iniciando navegación por los tabs de la página usando 'Tab'...")

    for i in range(num_range):
        pyautogui.press('tab')
        logging.info(f"Navegando al campo {i+1}")
        time.sleep(TEMPO_ESPERA * 0.2)
    logging.info("Navegación entre tabs completada.")

# Función para navegar hacia atrás usando Shift + Tab
def navigate_back_tabs_on_page(num_range):

    logging.info("Regresando entre los tabs de la página usando 'Shift+Tab'...")

    for i in range(num_range): 
        pyautogui.hotkey('shift', 'tab')  
        logging.info(f"Regresando al campo {num_range - i}")
        time.sleep(TEMPO_ESPERA * 0.2)  

    logging.info("Navegación hacia atrás entre tabs completada.")

# Función para cerrar el popup de traducción
def close_translate_popup(image_popup):

    try:
        image_location = locate_on_screen_with_retry(image_popup)

        if image_location:
            # Si encontramos la imagen, calculamos la posición de la "X"
            image_width, image_height = image_location[0], image_location[1]
            
            # Posición de la esquina superior derecha (donde estaría la "X")
            x_pos = image_location[0] + image_width - 10 
            y_pos = image_location[1] + 10 
            pyautogui.click(x_pos, y_pos)

        else:
            print("❌ No se encontró la imagen en la pantalla.")
    
    except pyautogui.ImageNotFoundException:
        print("⚠️ Error: No se encontró la imagen en la pantalla.")

# Función para esperar a que el elemento esté listo (con retry)
def wait_for_elements(image_paths, retries=5):
    
    if not isinstance(image_paths, list):
        image_paths = [image_paths]
    
    for _ in range(retries):
        for image_path in image_paths:
            found = locate_on_screen_with_retry(image_path, confidence=CONFIDENCE)
            if found:
                return found
        time.sleep(TEMPO_ESPERA)
    
    return None