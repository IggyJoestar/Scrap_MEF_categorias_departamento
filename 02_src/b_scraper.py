"""
=====================
Project     : WS CAMEF
File        : b_scraper.py
Description : Web data extraction using Selenium.
Date        : 2025-02-07
Version     : 1.0
Author      : Alex Evanan

Revision History:
    - [2025-02-07]  v1.0: Initial version.
    - [2025-02-10]  v1.1: function implementation.
    - [2025-02-24]  v1.2: Added generalized functions for navigation and data extraction.
    - [2025-02-25]  v1.3: Tested escalability new ROUTES and FILE_CONFIGS.

Notes:
    - Developed with Python 3.11.9.
    - Compatible with JupyterLab, Notebook, and Google Colab.
    - Dependencies are listed in 'requirements.txt'.

Usage:
    Run this script from the terminal or interactive environment:
        $ python 02_src/b_scraper.py
=====================
"""

# =====================
# Importación de librerías
# =====================
import sys
import os

import time
import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Configuración desde 02_src/0_config.py
sys.path.append(os.path.join(os.getcwd(), "02_src"))
import a_config


# =====================
# Funciones de Utilidad
# =====================


def initialize_driver():
    """
    Inicializa el driver de Selenium.
    """
    try:
        # Configurar el servicio del WebDriver
        service = Service(executable_path=a_config.PATH_DRIVER)
        options = webdriver.ChromeOptions()

        # Opciones adicionales para estabilidad
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option(
            "excludeSwitches", ["enable-logging"]
        )  # Oculta notificaciones

        # Inicializar el driver
        driver = webdriver.Chrome(service=service, options=options)

        # Log para confirmar que se inició correctamente
        print("Driver iniciado.")

        return driver  # Devuelve la instancia del driver

    except Exception as e:
        print(f"Error al iniciar el driver de Selenium: {e}")
        raise


def navigate_to_url(driver, url):
    """
    Navega a la URL especificada utilizando el driver proporcionado.
    """
    try:
        driver.get(url)
        print(f"Navegando a: {url}")

        # cambio de frame
        switch_to_frame(driver, "frame0")

    except Exception as e:
        print(f"Error al navegar a {url}: {e}")
        raise


def switch_to_frame(driver, nombre_frame, tiempo=10):
    """
    Cambia al frame especificado y verifica que el <body> esté presente
    """
    try:
        # primero cambiar contenido por defecto
        driver.switch_to.default_content()

        # Camviar de frame
        WebDriverWait(driver, tiempo).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, nombre_frame))
        )
        print(f"Cambiado a '{nombre_frame}'.")

        # Verificar que el <body> del frame esté presente
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Body cargado y verificado.")

    except Exception as e:
        print(f"Error: No se pudo cargar el <body> del'{nombre_frame}'. {e}")


# def click_on_element(driver, element_id):
#     """
#     Hace clic en un elemento de la página utilizando su ID.
#     """
#     try:
#         element = WebDriverWait(driver, 20).until(
#             EC.element_to_be_clickable((By.ID, element_id))
#         )
#         element.click()
#     except StaleElementReferenceException:
#         click_on_element(driver, element_id)

def click_on_element(driver, element_id, max_retries=3):
    """
    Hace clic en un elemento de la página (por ID) y reintenta 
    automáticamente si ocurre un StaleElementReferenceException.
    """
    if max_retries <= 0:
        # Si no quedan intentos, lanza un error para detener la ejecución.
        print(f"ERROR: Fallo al hacer clic en el elemento con ID '{element_id}' después de 3 reintentos.")
        raise Exception("Se agotó el límite de reintentos por Stale Element.")

    try:
        # 1. Espera explícita para asegurar que el elemento esté presente y se pueda hacer clic.
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, element_id))
        )
        
        # 2. Haz clic
        element.click()
        print(f"Éxito al hacer clic en el elemento con ID: {element_id}")
        
    except StaleElementReferenceException:
        print(f"Advertencia: Elemento '{element_id}' obsoleto. Reintentando... (Quedan {max_retries - 1} intentos)")
        
        # 3. Llama a la función de nuevo con un intento menos (Recursión).
        # Esto re-localizará el elemento.
        click_on_element(driver, element_id, max_retries - 1)
        
    except TimeoutException:
        print(f"Error: El elemento con ID '{element_id}' no se pudo hacer clic en el tiempo esperado.")


def select_dropdown_option(driver, element_id, option_text):
    """
    Selecciona una opción de un elemento <select> utilizando el texto de la opción
    """
    try:
        # Esperar a que el elemento <select> sea clickeable
        select_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, element_id))
        )

        # Crear instancia de Select
        select = Select(select_element)
        select.select_by_value(str(option_text))

    except StaleElementReferenceException:
        select_dropdown_option(driver, element_id, option_text)


def extract_table_data(driver):
    """
    Extrae los datos de una tabla con clase 'Data' y retorna una lista de listas
    """
    # Lista para almacenar los datos extraídos
    datos_tabla = []

    # Seleccionar todas las filas de la tabla con clase 'Data'
    filas = driver.find_elements(By.CSS_SELECTOR, "table.Data tr[id^='tr']")
    print(f"Se encontraron {len(filas)} filas.")

    # Extraer los datos de cada fila
    for i, fila in enumerate(filas):
        # Extraer desde la segunda celda para omitir el botón (primer <td>)
        datos = [td.text.strip() for td in fila.find_elements(By.TAG_NAME, "td")[1:]]

        print(f"Fila {i + 1}: {datos}")

        # Agregar datos solo si la fila tiene contenido
        if datos:
            datos_tabla.append(datos)

    return datos_tabla


def get_final_headers(driver, tabla_id):
    """
    Extrae encabezados manteniendo el orden de la tabla,
    omitiendo la primera columna vacía (botón) y obteniendo
    los niveles inferiores cuando hay agrupación.
    """
    try:
        tabla = driver.find_element(By.ID, tabla_id)
        fila_superior = tabla.find_elements(By.XPATH, ".//tr[1]/td | .//tr[1]/th")
        fila_inferior = tabla.find_elements(By.XPATH, ".//tr[2]/td | .//tr[2]/th")

        encabezados = []
        idx_inferior = 0  # Índice para recorrer fila_inferior cuando haya agrupación

        for i, celda in enumerate(fila_superior):
            # Omitir la primera celda si está vacía (botón)
            if i == 0 and not celda.text.strip():
                continue

            colspan = celda.get_attribute("colspan")

            if colspan:  # Si hay agrupación, tomar encabezados del nivel inferior
                for _ in range(int(colspan)):
                    encabezados.append(fila_inferior[idx_inferior].text.strip())
                    idx_inferior += 1
            else:  # Si no hay agrupación, tomar el texto directamente
                encabezados.append(celda.text.strip())

        print(f"Encabezados extraídos: {encabezados}")
        return encabezados

    except Exception as e:
        print(f"Error al obtener encabezados: {e}")
        return []


def navigate_levels(driver, route_config, current_level, table_headers, context=None):
    """
    Navega a través de los niveles definidos en la configuración.
    (Versión corregida para manejar StaleElementReferenceException)
    """

    extracted_data = []

    if context is None:
        context = {}

    print(f"\n📌 Entrando a nivel: {current_level}")

    level_config = route_config["levels"][current_level]
    button = level_config.get("button")
    list_xpath = level_config.get("list_xpath")
    name_xpath = level_config.get("name_xpath")
    next_level = level_config.get("next_level")
    table_id = level_config.get("table_id")

    if button:
        print(f"🔘 Haciendo clic en botón: {button}")
        click_on_element(driver, button)
        switch_to_frame(driver, a_config.GLOBAL_SELECTORS["main_frame"])

    if list_xpath:
        # --- CAMBIO 1: Obtener el número de elementos ANTES de iterar ---
        # Esto nos da un número fijo de iteraciones y evita problemas si la lista cambia.
        try:
            initial_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, list_xpath))
            )
            num_elements = len(initial_elements)
            print(f"📋 Se encontraron {num_elements} elementos en {current_level}")
        except TimeoutException:
            print(f"⚠️ No se encontraron elementos con el XPath: {list_xpath}. Saliendo del nivel.")
            num_elements = 0


        for i in range(num_elements):
            # --- CAMBIO 2: Re-localizar la lista completa DENTRO de cada iteración ---
            # Esto es crucial. Después de `driver.back()`, la lista anterior es inválida.
            # Necesitamos obtener la lista "fresca" cada vez.
            elements = driver.find_elements(By.XPATH, list_xpath)
            
            # --- CAMBIO 3: Asegurarse de que el índice todavía sea válido ---
            if i >= len(elements):
                print(f"Advertencia: La lista de elementos cambió. Omitiendo la iteración {i}.")
                continue

            element = elements[i]
            
            # --- CAMBIO 4: Interactuar con el elemento inmediatamente después de encontrarlo ---
            try:
                element_name = element.find_element(By.XPATH, name_xpath).text.strip()
                context[current_level] = element_name
                print(f"➡️ Entrando en: {element_name} (Elemento {i+1}/{num_elements})")

                # Tu función `click_on_element` ya busca el ID, lo cual es robusto.
                # El ID 'tr' + índice 'i' parece ser el patrón de la página.
                click_on_element(driver, f"tr{i}")
                switch_to_frame(driver, a_config.GLOBAL_SELECTORS["main_frame"])

                if next_level:
                    print(f"🔽 Navegando al siguiente nivel: {next_level}")
                    extracted_data.extend(
                        navigate_levels(
                            driver, route_config, next_level, table_headers, context
                        )
                    )

                print(f"⬅️ Regresando a {current_level}")
                driver.back()
                # Pequeña pausa opcional para dar tiempo a que el DOM se estabilice
                time.sleep(0.5) 
                switch_to_frame(driver, a_config.GLOBAL_SELECTORS["main_frame"])

            except StaleElementReferenceException:
                print(f"⚠️ Ocurrió un StaleElementReferenceException en la iteración {i}. Reintentando una vez...")
                # Agregamos un reintento simple para esta iteración específica.
                continue # Esto hará que el bucle 'for' continúe con el siguiente 'i'.
                         # Si el problema persiste, podrías implementar una lógica de reintento más compleja.


    else:
        # Lógica para cuando no hay una lista para iterar (sin cambios)
        if next_level:
            print(f"⏭️ Saltando a siguiente nivel: {next_level}")
            extracted_data.extend(
                navigate_levels(
                    driver, route_config, next_level, table_headers, context
                )
            )
        else:
            if table_id:
                if not table_headers:
                    print("📌 Extrayendo encabezados de la tabla...")
                    table_headers.extend(get_final_headers(driver, table_id))

                print(f"📊 Extrayendo datos de la tabla: {table_id}")
                table_data = extract_table_data(driver)

                for row in table_data:
                    formatted_row = [context[level] for level in context.keys()] + row
                    extracted_data.append(formatted_row)

    print(f"✅ Saliendo de nivel: {current_level}")
    return extracted_data

def extract_data_by_year(driver, year, route_name, table_headers):
    """
    Extrae los datos de la página para un año específico basado en la ruta configurada.

    :param driver: Instancia de Selenium WebDriver.
    :param year: Año para el cual se extraen los datos.
    :param route_name: Nombre de la ruta en ROUTES.
    :param table_headers: Lista compartida para almacenar los encabezados una sola vez.
    :return: Datos extraídos.
    """
    print(f"\n🗓️ Iniciando extracción para el año {year}, ruta: {route_name}")
    datos_anio = []

    # Seleccionar el año en el dropdown
    select_dropdown_option(driver, a_config.GLOBAL_SELECTORS["year_dropdown"], year)
    switch_to_frame(driver, a_config.GLOBAL_SELECTORS["main_frame"])

    # Obtener la configuración de la ruta
    route_config = a_config.ROUTES[route_name]

    # Determinar el primer nivel dinámicamente
    first_level = min(
        route_config["levels"].keys(), key=lambda lvl: int(lvl.split("_")[1])
    )

    # Navegar a través de los niveles desde el primer nivel
    datos_extraidos = navigate_levels(driver, route_config, first_level, table_headers)

    # Agregar metadatos: Año...
    for fila in datos_extraidos:
        fila_con_meta = [year] + fila
        datos_anio.append(fila_con_meta)

    print("✅ Extracción completada")
    return datos_anio


def save_data(nombre_archivo, datos, encabezados):
    """
    Guarda los datos extraídos en un archivo Excel.
    """
    try:
        df = pd.DataFrame(datos, columns=encabezados)
        df.to_excel(nombre_archivo, index=False)
        print(f"Datos guardados correctamente en {nombre_archivo}")
    except Exception as e:
        print(f"Error al guardar en Excel: {e}")


def select_route():
    """
    Muestra las rutas disponibles y permite al usuario seleccionar una.
    """
    print("\n--- Rutas disponibles ---")
    rutas_disponibles = list(a_config.ROUTES.keys())

    for i, ruta in enumerate(rutas_disponibles, start=1):
        print(f"{i}: {ruta}")

    while True:
        try:
            opcion = int(input("\nElige una ruta (número): "))
            if 1 <= opcion <= len(rutas_disponibles):
                return rutas_disponibles[opcion - 1]
            else:
                print("⚠️ Opción inválida, ingresa un número de la lista.")
        except ValueError:
            print("⚠️ Entrada inválida, ingresa un número.")


def main():
    """
    Función principal para iniciar el proceso de scraping con selección de ruta.
    Guarda los datos recolectados incluso si ocurre un error.
    """
    driver = initialize_driver()
    todos_los_datos = []
    table_headers = []

    try:
        navigate_to_url(driver, a_config.URL)

        ruta_seleccionada = select_route()
        print(f"\n🔍 Iniciando scraping para la ruta: {ruta_seleccionada}")

        # Obtener configuración de la ruta seleccionada
        file_conf = a_config.FILE_CONFIGS.get(ruta_seleccionada, {})
        encabezados_base = file_conf.get("ENCABEZADOS_BASE", [])
        archivo_scraping = file_conf.get("ARCHIVO_SCRAPING", [])

        # Iterar sobre los años y extraer datos
        for year in a_config.YEARS:
            datos_anio = extract_data_by_year(
                driver, year, ruta_seleccionada, table_headers
            )

            todos_los_datos.extend(datos_anio)

    except Exception as e:
        print(f"Se produjo un error inesperado: {e}")

        # Guardar datos parciales si hubo un error
        if todos_los_datos:
            print("💾 Guardando datos parciales antes de cerrar...")
            encabezados_completos = encabezados_base + table_headers
            save_data(
                os.path.join(a_config.PATH_DATA_RAW, "parcial_" + archivo_scraping),
                todos_los_datos,
                encabezados_completos,
            )

    finally:
        # Guardar los datos finales si se obtuvieron datos completos
        if todos_los_datos:
            print("💾 Guardando datos finales...")
            encabezados_completos = encabezados_base + table_headers
            save_data(
                os.path.join(a_config.PATH_DATA_RAW, archivo_scraping),
                todos_los_datos,
                encabezados_completos,
            )

        driver.quit()
        print("✅ Proceso finalizado, driver cerrado.")


if __name__ == "__main__":
    """
    Verifica si el script se ejecuta directamente.
    Si es así, llama a la función main().
    """
    main()
