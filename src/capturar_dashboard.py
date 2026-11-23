from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
SALIDA = BASE / "outputs" / "figures"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
URL = "http://localhost:8501"


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    paginas = [
        ("", "dashboard_home.png"),
        ("/Analisis_general", "dashboard_pagina1.png"),
        ("/Segmentacion_KMeans", "dashboard_pagina2.png"),
    ]
    with sync_playwright() as p:
        navegador = p.chromium.launch(executable_path=CHROME, headless=True, args=["--no-sandbox"])
        pagina = navegador.new_page(viewport={"width": 1500, "height": 1000})
        for ruta, nombre in paginas:
            pagina.goto(URL + ruta, wait_until="networkidle", timeout=90000)
            pagina.wait_for_timeout(5000)
            pagina.screenshot(path=str(SALIDA / nombre), full_page=True)
            print(f"Guardada: {nombre}")
        navegador.close()


if __name__ == "__main__":
    main()
