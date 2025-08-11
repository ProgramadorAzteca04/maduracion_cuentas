import pyautogui
import time
import logging

from app.services.utils.actions import (buscar_y_escribir, click_button, close_translate_popup,
    get_image_abs_path, handle_captcha_twocaptcha, locate_on_screen_with_retry,
    navigate_tabs_on_page, open_and_focus_window, wait_for_elements)
from app.services.utils.automation import AutomationService, ElementLocator
from app.services.utils.movement import mover_a_posicion_aleatoria

# Configuración de logging
logging.basicConfig(level=logging.INFO)

# Constantes
TEMPO_ESPERA = 1 
CONFIDENCE = 0.8
BROWSER_URL = 'https://dev.to'

# Función principal para registrar el usuario en dev.to
async def register_devto(name: str, username: str, email: str, password: str):

    
    IMAGES = [
        {"input": get_image_abs_path("input_named"), "text": name},
        {"input": get_image_abs_path("input_username2"), "text": username},
        {"input": get_image_abs_path("input_email2"), "text": email},
        {"input": get_image_abs_path("input_pass2"), "text": password},
        {"input": get_image_abs_path("input_conf_pass"), "text": password},
    ]

    open_and_focus_window("DEV Community", BROWSER_URL)

    if not click_button(get_image_abs_path("button_create_acount2")):
        return {"success": False, "error": "No se pudo hacer clic en el botón 'Create Account'"}

    if not click_button(get_image_abs_path("sing_up_email5")):
        return {"success": False, "error": "No se encontró el botón 'Sign Up Email'"}

    # Completar los campos del formulario
    for image in IMAGES:
        if not buscar_y_escribir(image['input'], image['text']):
            return {"success": False, "error": f"No se pudo completar el campo {image['input']}"}
        time.sleep(TEMPO_ESPERA)

    if not click_button(get_image_abs_path("captcha")):
        return {"success": False, "error": "No se pudo hacer clic en el botón CAPTCHA"}

    # handle_captcha_twocaptcha() maneja el captcha si es que aparece
    handle_captcha_twocaptcha()
    time.sleep(TEMPO_ESPERA)

    if not click_button(get_image_abs_path("button_commit")):
        return {"success": False, "error": "No se pudo hacer clic en el botón de registro"}

    success = wait_for_elements(get_image_abs_path("success_register"))
    if success:
        logging.info("Registro completado exitosamente.")
        pyautogui.hotkey('ctrl', 'w')

    return {"success": True, "captcha_detected": False}

# Función principal para loguearse en dev.to
async def login_devto(email: str, password: str):

    service = AutomationService()
    
    IMAGES = [
        {"input": "app/img/devto/input_mail_login.png", "text": email},
        {"input": "app/img/devto/input_pass_login2.png", "text": password},
    ]
    
    locator_login = ElementLocator(
        images=['app/img/devto/log_in_account.png', 'app/img/devto/log_in_account2.png']
    )
    logging.info("Buscando botón de login...")
    service.find_and_click_humanly(locator_login)

    logging.info("Haciendo scroll hacia abajo en la página...")
    pyautogui.scroll(-200)  # Valor negativo para desplazar hacia abajo
    time.sleep(TEMPO_ESPERA)

    for image in IMAGES:
        if not buscar_y_escribir(image['input'], image['text']):
            return {"success": False, "error": f"No se pudo completar el campo {image['input']}"}
        time.sleep(TEMPO_ESPERA)

    if not click_button("app/img/devto/button_login.png"):
        return {"success": False, "error": "No se pudo hacer clic en el botón de inicio de sesión"}

    return {"success": True}

# Función principal para desloguearse en dev.to
async def logout_devto(tabs_num):
    navigate_tabs_on_page(tabs_num)
    pyautogui.press('enter')
    time.sleep(TEMPO_ESPERA)

    if not click_button("app/img/devto/button_sign_out.png"):
        return {"success": False, "error": "No se pudo hacer clic en el botón 'Log Out'"}
    
    time.sleep(TEMPO_ESPERA)
    
    if not click_button("app/img/devto/button_sign_out_confirm.png"):
        return {"success": False, "error": "No se pudo hacer clic en el botón 'Confirmar Log Out'"}

    logging.info("Cierre de sesión completado exitosamente.")
    pyautogui.hotkey('alt', 'f4')
    time.sleep(TEMPO_ESPERA)

    return {"success": True}

# Función interactuar despues de loguear en dev.to
async def interaction_devto(email: str, password: str, path_url: str):
    service = AutomationService()
    try:
        active_window = open_and_focus_window("DEV Community", path_url)

        close_translate_popup('app/img/devto/translate_google2.png')

        if not click_button("app/img/devto/close_adversiting.png"):
            return {"success": False, "error": "No se encontró el botón 'Cerrar Publicidad'"}

        await login_devto(email, password)

        time.sleep(TEMPO_ESPERA)

        locator_notify = ElementLocator(
            images=['app/img/devto/button_notify.png', 'app/img/devto/button_notify2.png']
        )
        logging.info("Buscando botón de notificaciones...")
        service.find_and_click_humanly(locator_notify)

        time.sleep(TEMPO_ESPERA)
    
        service.browse_with_scroll(active_window, 30)

        mover_a_posicion_aleatoria()

        logging.info("Navegando a la sección de desafíos...")
        locator_Initial = ElementLocator(
            images=['app/img/devto/button_ini.png']
        )
        service.find_and_click_humanly(locator_Initial)

        locator_challenge = ElementLocator(
            images=['app/img/devto/button_dev_challenge.png']
        )
        service.find_and_click_humanly(locator_challenge)

        service.browse_with_scroll(active_window, 15)  # Reduce el tiempo de scroll
        time.sleep(TEMPO_ESPERA)

        logging.info("Navegando de vuelta a la sección de publicaciones...")
        pyautogui.hotkey('alt', 'left')

        mover_a_posicion_aleatoria()

        face_icon = wait_for_elements("app/img/devto/link_facebook.png")
        logging.info(f'👤 Icono de Facebook encontrado: {face_icon}')
        service._move_mouse_humanly(face_icon.x, face_icon.y)

        act_discussion = wait_for_elements(["app/img/devto/active_discussions.png", "app/img/devto/discuss.png"])
        logging.info(f'💬 Icono de discusiones activas encontrado: {act_discussion}')
        service._move_mouse_humanly(act_discussion.x, act_discussion.y)

        logging.info("\n✅ Proceso de navegación finalizado.")
        await logout_devto(8)

        return {"success": True}

    except Exception as e:
        logging.error(f"\n🚨 ERROR en el flujo de navegación: {e}. Proceso abortado.")
