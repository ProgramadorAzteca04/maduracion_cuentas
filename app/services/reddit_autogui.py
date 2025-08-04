import pyautogui
import time

class RedditAutoGUIService:
    def __init__(self):
        # Configuración de seguridad
        pyautogui.PAUSE = 1.5
        pyautogui.FAILSAFE = True

    def register_account(
        self,
        email: str,
        username: str,
        password: str,
        screenshot_dir: str = "screenshots/reddit"
    ) -> bool:
        """
        Registra una cuenta en Reddit usando PyAutoGUI.
        Retorna True si el flujo se completó (aunque haya CAPTCHA).
        """
        try:
            # Abrir navegador (ej: Chrome)
            pyautogui.hotkey("ctrl", "t")
            pyautogui.write("https://www.reddit.com/register")
            pyautogui.press("enter")
            time.sleep(5)

            # Paso 1: Rellenar formulario
            pyautogui.click(x=800, y=400)  # Ajusta coordenadas
            pyautogui.write(email)
            pyautogui.press("tab")
            pyautogui.write(username)
            pyautogui.press("tab")
            pyautogui.write(password)

            # Paso 2: Capturar pantalla para verificar (opcional)
            screenshot_path = f"{screenshot_dir}/register_{int(time.time())}.png"
            pyautogui.screenshot(screenshot_path)

            # Paso 3: Enviar formulario
            pyautogui.press("tab")
            pyautogui.press("enter")

            return True

        except Exception as e:
            print(f"Error en PyAutoGUI: {e}")
            return False