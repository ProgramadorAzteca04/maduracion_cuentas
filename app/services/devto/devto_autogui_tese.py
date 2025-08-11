# =========================
#         IMPORTS
# =========================
import os
import time
import random
import subprocess
import difflib
from typing import Optional, Tuple, List

import numpy as np
import cv2
import pyautogui
import pytesseract


# =========================
#       CONFIGURACIÓN
# =========================
# --- Credenciales y navegador ---
EMAIL_USUARIO: str = "tu_email@gmail.com"
PASSWORD_USUARIO: str = "password123"
RUTA_CHROME: str = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL_LOGIN: str = "https://dev.to"

# --- Tesseract (Windows) ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- OCR ---
OCR_IDIOMA: str = "eng"
OCR_CONFIG: str = f"-l {OCR_IDIOMA} --oem 3 --psm 6"  # psm 6: texto en una sola columna
OCR_CONFIANZA_MIN: int = 60  # descartar lecturas poco confiables (0-100)

# --- Captura de pantalla ---
USAR_MSS: bool = True                  # si True, intenta mss (más rápido); si falla, usa ImageGrab
ESCALA_CAPTURA: float = 1.0            # 1.0 tamaño nativo; 0.75 o 0.5 acelera OCR con menor precisión

# --- Interacciones “humanas” ---
MOVER_DUR_MIN: float = 0.25
MOVER_DUR_MAX: float = 0.80
TIPEO_DUR_MIN: float = 0.05
TIPEO_DUR_MAX: float = 0.12
SCROLL_MIN: int = 200
SCROLL_MAX: int = 450
ESPERA_MIN: float = 0.50
ESPERA_MAX: float = 1.20

# --- Búsqueda de texto ---
BUSQUEDA_TIMEOUT: float = 12.0
BUSQUEDA_INTERVALO: float = 0.45
SIMILITUD_MIN_DIFUSA: float = 0.82  # “Log in” vs “Login”, etc.

# --- Rangos de color (HSV) ---
H_PADDING: int = 14   # +/- grados de tono [0..179]
S_PADDING: int = 60   # +/- saturación [0..255]
V_PADDING: int = 60   # +/- valor [0..255]
PERMITIR_ENVOLTURA_H: bool = True  # si cruza 0/179, divide el rango y une máscaras


# =========================
#  CAPTURA DE PANTALLA
# =========================
try:
    if USAR_MSS:
        import mss  # type: ignore
        _MSS_DISPONIBLE = True
    else:
        _MSS_DISPONIBLE = False
except Exception:
    _MSS_DISPONIBLE = False


def capturar_pantalla(region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
    """
    Captura pantalla (o región) y retorna imagen BGR (OpenCV).
    region=(left, top, width, height)
    """
    if _MSS_DISPONIBLE:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # pantalla principal
            if region:
                left, top, width, height = region
                bbox = {"left": left, "top": top, "width": width, "height": height}
            else:
                bbox = {
                    "left": monitor["left"],
                    "top": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"],
                }
            img = np.array(sct.grab(bbox))
            frame = img[:, :, :3]  # BGRA -> BGR
    else:
        from PIL import ImageGrab  # lazy import
        if region:
            l, t, w, h = region
            img = ImageGrab.grab(bbox=(l, t, l + w, t + h))
        else:
            img = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    if 0 < ESCALA_CAPTURA < 1.0:
        frame = cv2.resize(frame, None, fx=ESCALA_CAPTURA, fy=ESCALA_CAPTURA, interpolation=cv2.INTER_AREA)
    return frame


# =========================
#     UTILIDADES COLOR
# =========================
def _asegurar_bgr_uint8(img: np.ndarray) -> np.ndarray:
    """Asegura imagen BGR uint8 (elimina alfa si hay 4 canales)."""
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def hex_a_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convierte '#RRGGBB' a (R, G, B)."""
    hex_color = hex_color.lstrip("#")
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def _rango_hsv_desde_rgb(
    r: int,
    g: int,
    b: int,
    h_pad: int = H_PADDING,
    s_pad: int = S_PADDING,
    v_pad: int = V_PADDING,
    envolver_h: bool = PERMITIR_ENVOLTURA_H,
) -> Tuple[np.ndarray, np.ndarray, Optional[Tuple[np.ndarray, np.ndarray]]]:
    """
    Calcula (low1, high1, extra_range) en HSV alrededor del color RGB indicado.
    - Evita overflow/underflow usando enteros con signo y luego clip.
    - Si el rango de H cruza 0 o 179 y envolver_h=True, devuelve segundo rango (low2, high2).
    """
    hsv_pixel = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0, 0]
    h, s, v = map(int, hsv_pixel)

    low_raw = np.array([h - h_pad, s - s_pad, v - v_pad], dtype=np.int16)
    high_raw = np.array([h + h_pad, s + s_pad, v + v_pad], dtype=np.int16)

    low_sv = np.clip(low_raw[1:], 0, [255, 255])
    high_sv = np.clip(high_raw[1:], 0, [255, 255])

    low_h, high_h = int(low_raw[0]), int(high_raw[0])
    rango_extra: Optional[Tuple[np.ndarray, np.ndarray]] = None

    if envolver_h and (low_h < 0 or high_h > 179):
        if low_h < 0 and high_h <= 179:
            # Ej: h=5, pad=14 -> [-9,19] = [0,19] U [170,179]
            low1 = np.array([0, low_sv[0], low_sv[1]], dtype=np.uint8)
            high1 = np.array([min(high_h, 179), high_sv[0], high_sv[1]], dtype=np.uint8)

            low2_h = 179 + low_h + 1  # 170 en el ejemplo
            low2 = np.array([low2_h, low_sv[0], low_sv[1]], dtype=np.int16)
            low2 = np.clip(low2, [0, 0, 0], [179, 255, 255]).astype(np.uint8)
            high2 = np.array([179, high_sv[0], high_sv[1]], dtype=np.uint8)
            rango_extra = (low2, high2)

        elif low_h >= 0 and high_h > 179:
            # Ej: h=175, pad=14 -> [161,189] = [161,179] U [0,10]
            low1 = np.array([max(low_h, 0), low_sv[0], low_sv[1]], dtype=np.uint8)
            high1 = np.array([179, high_sv[0], high_sv[1]], dtype=np.uint8)

            high2_h = high_h - 179  # 10 en el ejemplo
            low2 = np.array([0, low_sv[0], low_sv[1]], dtype=np.uint8)
            high2 = np.array([high2_h, high_sv[0], high_sv[1]], dtype=np.int16)
            high2 = np.clip(high2, [0, 0, 0], [179, 255, 255]).astype(np.uint8)
            rango_extra = (low2, high2)
        else:
            # Rango excesivo: cubrir todo H
            low1 = np.array([0, low_sv[0], low_sv[1]], dtype=np.uint8)
            high1 = np.array([179, high_sv[0], high_sv[1]], dtype=np.uint8)
    else:
        low1 = np.array([np.clip(low_h, 0, 179), low_sv[0], low_sv[1]], dtype=np.uint8)
        high1 = np.array([np.clip(high_h, 0, 179), high_sv[0], high_sv[1]], dtype=np.uint8)

    return low1, high1, rango_extra


def filtrar_imagen_por_color(img_bgr: np.ndarray, color_hex: str) -> np.ndarray:
    """
    Devuelve imagen filtrada por color (HSV), uniendo rangos si H envuelve.
    """
    img_bgr = _asegurar_bgr_uint8(img_bgr)
    r, g, b = hex_a_rgb(color_hex)
    low1, high1, extra = _rango_hsv_desde_rgb(r, g, b)

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, low1, high1)

    if extra is not None:
        low2, high2 = extra
        mask2 = cv2.inRange(hsv, low2, high2)
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        mask = mask1

    return cv2.bitwise_and(img_bgr, img_bgr, mask=mask)


# =========================
#  PREPROCESADO PARA OCR
# =========================
def preprocesar_para_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """Contraste + binarización adaptativa para mejorar OCR."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 9
    )
    return th


def ocr_a_data(img_bin: np.ndarray) -> dict:
    """Ejecuta tesseract y devuelve dict con campos (text, left, top, width, height, conf)."""
    return pytesseract.image_to_data(img_bin, output_type=pytesseract.Output.DICT, config=OCR_CONFIG)


# =========================
#   BÚSQUEDA DE TEXTO
# =========================
def _mejor_coincidencia_difusa(consulta: str, candidatos: List[str]) -> Optional[int]:
    """Devuelve índice del mejor match difuso o None si no supera umbral."""
    if not candidatos:
        return None
    q = " ".join(consulta.split()).strip().lower()
    puntajes = []
    for i, c in enumerate(candidatos):
        c2 = " ".join(c.split()).strip().lower()
        ratio = difflib.SequenceMatcher(None, q, c2).ratio()
        puntajes.append((ratio, i))
    ratio, idx = max(puntajes, key=lambda x: x[0])
    return idx if ratio >= SIMILITUD_MIN_DIFUSA else None


def buscar_centro_texto(
    texto: str,
    timeout: float = BUSQUEDA_TIMEOUT,
    intervalo: float = BUSQUEDA_INTERVALO,
    region: Optional[Tuple[int, int, int, int]] = None,
    color_hex: Optional[str] = None,
) -> Optional[Tuple[int, int]]:
    """
    Busca 'texto' en pantalla (difuso) y retorna (x, y) del centro si lo encuentra.
    Si color_hex está definido, enmascara por color antes de OCR.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        frame = capturar_pantalla(region)
        if color_hex:
            frame = filtrar_imagen_por_color(frame, color_hex)
        img_bin = preprocesar_para_ocr(frame)
        data = ocr_a_data(img_bin)

        textos: List[str] = []
        coords: List[Tuple[int, int]] = []
        confs = data.get("conf", [])
        for i in range(len(data.get("text", []))):
            try:
                conf_val = int(float(confs[i]))
            except Exception:
                continue
            if conf_val < OCR_CONFIANZA_MIN:
                continue
            palabra = data["text"][i].strip()
            if not palabra:
                continue
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            textos.append(palabra)
            coords.append((x, y))

        idx = _mejor_coincidencia_difusa(texto, textos)
        if idx is not None:
            x, y = coords[idx]
            # reescala si se capturó con downscale (solo para captura global)
            if 0 < ESCALA_CAPTURA < 1.0 and region is None:
                inv = 1.0 / ESCALA_CAPTURA
                x, y = int(x * inv), int(y * inv)
            return x, y

        time.sleep(intervalo)

    return None


# =========================
#  INTERACCIÓN “HUMANA”
# =========================
def mover_humano_a(x: int, y: int) -> None:
    pyautogui.moveTo(x, y, duration=random.uniform(MOVER_DUR_MIN, MOVER_DUR_MAX))


def _press_combo(*keys: str) -> None:
    """Presiona una combinación de teclas en orden (manteniendo modificadores)."""
    for k in keys:
        pyautogui.keyDown(k)
    # la última suele ser la tecla 'base'
    for k in reversed(keys):
        pyautogui.keyUp(k)

def _press_shifted(base_key: str) -> None:
    """Presiona Shift + tecla base (para caracteres con Shift)."""
    _press_combo('shift', base_key)

def escribir_humano(texto: str) -> None:
    """
    Escribe texto simulando a un humano en teclado ES-ES.
    - Soporta alfanumérico, '@' (AltGr+2), '.', '-', '_' (Shift+-) y mayúsculas con Shift.
    - Si aparece '@' (p.ej. en EMAIL), usa la combinación correcta para ES-ES.
    """
    # Mapa de algunas teclas que necesitan combinación en ES-ES
    # (ampliable si luego necesitas ¿, ¡, /, :, etc.)
    especiales = {
        '@': lambda: _press_combo('ctrl', 'alt', '2'),      # AltGr+2 en ES-ES (Windows)
        '.': lambda: pyautogui.press('period'),
        '-': lambda: pyautogui.press('minus'),
        '_': lambda: _press_shifted('minus'),               # Shift + -
    }

    for ch in texto:
        time.sleep(random.uniform(TIPEO_DUR_MIN, TIPEO_DUR_MAX))

        # 1) Arroba y otros especiales
        if ch in especiales:
            especiales[ch]()
            continue

        # 2) Letras
        if ch.isalpha():
            # pyautogui usa layout del SO; para mayúsculas, forzamos Shift
            key = ch.lower()
            if ch.isupper():
                _press_shifted(key)
            else:
                pyautogui.press(key)
            continue

        # 3) Dígitos
        if ch.isdigit():
            pyautogui.press(ch)
            continue

        # 4) Espacio
        if ch == ' ':
            pyautogui.press('space')
            continue

        # 5) Punto y coma comunes del email (fallback por si el layout funciona directo)
        #    Si tu layout ya escribe correctamente el carácter tal cual, esto también funcionará.
        try:
            pyautogui.typewrite(ch)  # intento directo (por si el SO lo resuelve bien)
        except Exception:
            # Si algo no se pudo teclear, lo ignoramos para no romper el flujo
            pass

def desplazamiento_humano() -> None:
    for _ in range(random.randint(2, 5)):
        pyautogui.scroll(-random.randint(SCROLL_MIN, SCROLL_MAX))
        time.sleep(random.uniform(0.8, 1.5))
        ancho, alto = pyautogui.size()
        mx = random.randint(80, ancho - 80)
        my = random.randint(80, alto - 80)
        mover_humano_a(mx, my)


def hacer_click_en_texto(
    texto: str,
    timeout: float = BUSQUEDA_TIMEOUT,
    color_hex: Optional[str] = None,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> bool:
    punto = buscar_centro_texto(texto, timeout=timeout, region=region, color_hex=color_hex)
    if punto:
        mover_humano_a(*punto)
        pyautogui.click()
        return True
    return False


# =========================
#       FLUJO APP
# =========================
def abrir_navegador() -> None:
    try:
        subprocess.Popen([RUTA_CHROME, "--new-window", URL_LOGIN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        subprocess.Popen(["chrome", "--new-window", URL_LOGIN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)


def iniciar_sesion_devto() -> None:
    abrir_navegador()

    # Botón “Log in” (sin color; si falla, probar con color claro)
    if not hacer_click_en_texto("Log in", timeout=10):
        hacer_click_en_texto("Log in", timeout=6, color_hex="#FFFFFF")

    # Campo usuario: “Username” o “Email”
    if hacer_click_en_texto("Username", timeout=5) or hacer_click_en_texto("Email", timeout=5):
        escribir_humano(EMAIL_USUARIO)

    time.sleep(random.uniform(ESPERA_MIN, ESPERA_MAX))

    # Campo password
    if hacer_click_en_texto("Password", timeout=6):
        escribir_humano(PASSWORD_USUARIO)

    time.sleep(random.uniform(ESPERA_MIN, ESPERA_MAX))

    # Botón de envío: probar variantes
    for etiqueta in ("Log in"):
        if hacer_click_en_texto(etiqueta, timeout=4, color_hex="#FFFFFF"):
            break

    time.sleep(5)


def abrir_articulo_cualquiera() -> bool:
    """Abre un artículo buscando pistas típicas (“ago”, “min read”, etc.)."""
    for pista in ("ago", "min read", "reading"):
        punto = buscar_centro_texto(pista, timeout=6)
        if punto:
            mover_humano_a(*punto)
            pyautogui.click()
            time.sleep(4)
            return True
    return False


def dar_me_gusta() -> bool:
    """Intenta dar “Like”; si no, prueba con “Reactions”."""
    return hacer_click_en_texto("Like", timeout=4, color_hex="#FFFFFF") or hacer_click_en_texto("Reactions", timeout=4)


def main() -> None:
    iniciar_sesion_devto()
    desplazamiento_humano()
    abrir_articulo_cualquiera()
    desplazamiento_humano()
    dar_me_gusta()
    print("✅ Script completado")


if __name__ == "__main__":
    main()
