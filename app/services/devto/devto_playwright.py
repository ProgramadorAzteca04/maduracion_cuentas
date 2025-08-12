import asyncio
import logging
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

LOG_FILE = "devto_register.log"
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename=f"logs/{LOG_FILE}",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def register_on_devto(name: str,username: str, email: str, password: str) -> dict:
    result = {
        "name": name,
        "username": username,
        "email": email,
        "timestamp": datetime.utcnow().isoformat(),
        "success": False,
        "error": None,
        "captcha_detected": False
    }
    

    try:
        async with async_playwright() as p:
            logging.info('register NEW')
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            time_wait = random.randint(25, 30)

            logging.info("Navegando a dev.to...")
            await page.goto("https://dev.to/", timeout = time_wait * 1000 )
            logging.info(f"esperando la carga {time_wait * 1000}")

            logging.info("Haciendo clic en 'Create account'")
            await page.click('a[href="/enter?state=new-user"]', timeout=time_wait * 200)
  
            logging.info("Esperando carga pagina'enter'")
            await page.wait_for_url("https://dev.to/enter?state=new-user") 

            logging.info("Haciendo clic en 'crear con mail'")
            await page.click('a[href="/users/sign_up?state=email_signup"]', timeout=time_wait * 200)

            logging.info("Llenando formulario")
            await page.wait_for_timeout(5000)  # Esperar u5 seg para que la página cargue completamente
            await page.fill("input#user_name", name)
            await page.fill("input#user_username", username)
            await page.fill("input#user_email", email)
            await page.fill("input#user_password", password)
            await page.fill("input#user_password_confirmation", password)

            # Intentar resolver reCAPTCHA tipo checkbox
            try:
                logging.info("Buscando iframe de reCAPTCHA...")
                # Esperar al iframe que contiene el checkbox
                frame_element = await page.wait_for_selector("iframe[title*='reCAPTCHA']", timeout=5000)
                frame = await frame_element.content_frame()
                logging.warning("CAPTCHA detectado.")

                if frame:
                    logging.info("Haciendo clic en el checkbox del CAPTCHA...")
                    await frame.click("#recaptcha-anchor", timeout=time_wait * 200)
                    await asyncio.sleep(5)  # Esperar por si se lanza el desafío visual

                    logging.info("Checkbox del CAPTCHA clickeado.")
                    result["captcha_detected"] = True
                else:
                    logging.warning("No se pudo acceder al frame del CAPTCHA.")

            except PlaywrightTimeoutError:
                logging.info("No se detectó reCAPTCHA visible.")

            logging.info("Enviando formulario")
            await page.click("input[name='commit']")

            await asyncio.sleep(5)

            result["success"] = True
            logging.info(f"Registro simulado para {email} completado (aunque CAPTCHA podría bloquearlo).")

            await browser.close()

    except Exception as e:
        logging.error(f"Error al registrar: {e}")
        result["error"] = str(e)
        result["success"] = False

    return result
