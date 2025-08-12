import pyautogui
import random
import math
import time
import os
import pygetwindow as gw
from typing import Optional

def _move_mouse_humanly(x_dest, y_dest):
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

def find_and_click_humanly(locator, confidence=0.85, attempts=1, wait_time=0):
    """Busca un elemento, mueve el ratón de forma humana y hace clic."""
    for attempt in range(attempts):
        for image in locator.images:
            try:
                pos = pyautogui.locateCenterOnScreen(image, confidence=confidence)
                if pos:
                    print(f"✅ Elemento encontrado con {os.path.basename(image)}.")
                    _move_mouse_humanly(pos.x, pos.y)
                    pyautogui.click()
                    time.sleep(1)
                    return True
            except pyautogui.ImageNotFoundException:
                continue
        if wait_time > 0:
            print(f"Retraso de {wait_time}s antes del siguiente intento.")
            time.sleep(wait_time)
    print(f"❌ No se encontró el elemento con ninguna de las imágenes: {locator.images}")
    return False

def type_text_humanly(text: str):
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

def browse_with_scroll(window, duration_seconds: int, human_action_prob: float = 0.05):
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
            _perform_random_human_action(window)

    print("\n🏁 Tiempo de simulación finalizado.")

def _perform_random_human_action(window):
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
        _move_mouse_humanly(target_x, target_y)
    elif action == 'scroll_corrective':
        print("Interrupción: Scroll hacia arriba.")
        pyautogui.scroll(random.randint(200, 400))
        time.sleep(random.uniform(2, 4))
    else:  # Pausa corta
        duration = random.uniform(3, 6)
        print(f"🧘 Interrupción: Pausa corta de {duration:.1f}s.")
        time.sleep(duration)

def get_and_focus_window(title: str) -> Optional[gw.Win32Window]:
        """Busca, activa y maximiza una ventana por su título."""
        print(f"🔍 Buscando ventana con el título '{title}'...")
        try:
            windows = gw.getWindowsWithTitle(title)
            print(f"Ventanas encontradas: {windows}")
            if windows:
                window = windows[0]
                print('✅ Ventana encontrada:', window.title)
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
        


def movimiento_circular(x, y, radio=50, pasos=100):
    """Función que mueve el mouse en un patrón circular."""
    for i in range(pasos):
        # Ángulo de movimiento
        angulo = 2 * math.pi * i / pasos
        # Calculamos las coordenadas del círculo
        x_offset = int(radio * math.cos(angulo))
        y_offset = int(radio * math.sin(angulo))
        pyautogui.moveTo(x + x_offset, y + y_offset, duration=0.01)

def mover_a_posicion_aleatoria():
    """Función que mueve el mouse a una posición aleatoria, realiza un movimiento circular
    y lo posiciona al final en la barra de scroll."""
    
    # Tamaño de la pantalla (para generar una posición aleatoria)
    pantalla_ancho, pantalla_alto = pyautogui.size()
    
    # Generar una posición aleatoria en la pantalla
    x = random.randint(0, pantalla_ancho)
    y = random.randint(0, pantalla_alto)
    
    # Mover el ratón a la posición aleatoria
    _move_mouse_humanly(x, y)
    time.sleep(1)
    
    # Realizar un movimiento circular en torno a la posición (x, y)
    movimiento_circular(x, y, radio=50, pasos=50)
    
    # Posicionar el ratón en la barra de desplazamiento (asumimos que está en la parte inferior)
    _move_mouse_humanly(pantalla_ancho - 20, pantalla_alto - 20)
    print("Movimiento aleatorio completo.")