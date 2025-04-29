#**************************************************
#----------- CORREO GEOGRAFICO del IGN-------------
#**************************************************

# Requisitos previos a la ejecución:
#*  - Seteo de Alertas de Google en cuenta de GMAIL
#     con noticias que se desea identificar
#   - Extraer link RSS de cada alerta y almacenarlo
#     en una hoja de calculo en Google Sheets
#*  - La hoja debe incluir las siguientes columnas:
#       *"Grupo": Grupo al que pertenece la alerta,
#                 Define la organizacion del correo
#       *"Alerta": Nombre de la alerta,
#                  Agrupa todas las noticias que se
#                  encuentren en un mismo RSS
#       *"Consulta": Expresión de filtro que se
#                    utilizó para generar el RSS
#       *"link": Enlace de acceso al RSS de cada
#                alerta configurada
#   - Identificar ID de la hoja de calculo
#     y nombre de la hoja con los datos
#       Buscar ID en enlace web de la hoja, 
#       en medio de las siguientes partes:
#       -"https://docs.google.com/spreadsheets/d/"
#       -"/edit?gid=0#gid=0"
#   - Configurar la hoja de calculo para que 
#     Cualquier usuario con le enlace tenga 
#     Acceso como Lector
#*  - Habilitar la API de google sheets y
#     generar clave de API desde 
#     "https://console.cloud.google.com/apis/"
#*  - Generar contraseña de aplicaciones desde
#     myaccount.google.com/apppasswords
#        Requiere 2FA
#   - Guardar nombre y contraseña de aplicaciones 
#     en credenciales.txt
#     ej:
#       cuentaNoticias@gmail.com (reemplazar por nombre de cuenta)
#       abcd efgh ijkl mnop (reemplazar por clave de aplicaciones)
#   - Ejecutar este codigo una primera vez para generar archivo noticias.xlsx
#     Crear una copia de dicho archivo con nombre historico.xlsx
#     Agregar y completarle campo fecha  

# * Una vez configurado todo lo anterior, el codigo se ejecuta llamando al archivo envio_mail_grupo.py
# * Se recomienda automatizar esta ejecucion desde crontab o task scheduler en la frecuencia que necesite

# Subido a GitHub en https://github.com/C-Holguin/noticias

# Librerias para recoleccion de datos
import requests
import pandas as pd
import feedparser
from datetime import datetime
import re

# Librerias para envio de mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from babel.dates import format_date
import sys
import os

# Cargar datos de Google Sheets
## Modificar clave API a planilla correspondiente
def get_google_sheet_data(spreadsheet_id, sheet_name, range, api_key):
    # URL CON DATOS
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}!{range}?alt=json&key={api_key}'

    # Obtener datos de planilla  (excepto error)
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Devolver como JSON
        return  response.json()

    except requests.exceptions.RequestException as e:
        # Mostrar error ocurrido
        print(f"Ocurrio un error: {e}")
        return None

# Definicion de la FUNCION PROCESAR_ALERTA
def procesar_alerta(row, df_list):
    # Extraer datos de alerta
    grupo_alerta =  row["Grupo"] # Super Categoria de Alerta
    id_alerta = row["Alerta"] # Alerta
    feed_url = row["link"] # Link a feed RSS correspondiente a cada alerta
    

    entries = [] # Lista de noticias encontradas por cada fila del DF

    # Recolectar noticias de cada alerta
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        entry_data = {
            'grupo' : grupo_alerta,
            'alerta' : id_alerta,
            'title': entry.title.replace("<b>","").replace("</b>",""), # Quitar negrita
            'published': entry.published,
            'link': entry.link,
            'content': entry.content[0].value.replace("<b>","").replace("</b>",""),#Quitar negrita
            'link_noticia': re.split(r'[?&]', entry.link[42:])[0],
            'link_extent': entry.link.find("/", 50),
            'fecha_procesamiento' : datetime.now(),
            'link_sitio': entry.link[42:entry.link.find("/", 50)].lstrip(),
        }
        # Cargar noticias en lista de noticias
        entries.append(entry_data)

    # Convertir en DF
    df = pd.DataFrame(entries)

    # Cargar DF de noticias en lista indicada en parametro df_list
    df_list.append(df)

# Funcion principal de recoleccion de noticias
## Cambiar valores por defecto a acceso a hoja con noticias
def recolectar_noticias(path, spreadsheet_id, sheet_name):
    print("Recolectando Noticias de Alertas de Google...")

    # Extraer datos de Google Sheets
    api_key = "tu_clave_API"
    sheet_data = get_google_sheet_data(spreadsheet_id, sheet_name, "A1:D", api_key)

    # Convertir a DF (tomar columnas de primera fila de tabla, datos del resto)
    df_alertas = pd.DataFrame(sheet_data['values'][1:], columns = sheet_data['values'][0])

    #Lista de DF con resultado noticias
    dl_acum = []

    print("Analizando feed de Noticias...")
    # Extraer DF con noticias de cada fila de df_alertas -> dl_acum
    df_alertas.apply(lambda row: procesar_alerta(row, dl_acum), axis = 1)

    # Unificar noticias encontradas en unico DF
    noticias_unif = pd.concat(dl_acum).reset_index(drop = True)

    #Eliminar noticias duplicadas (queda la primera que se encontro)
    largo_pre = len(noticias_unif)
    noticias_unif.drop_duplicates(subset = ['title', 'link_sitio'], keep = 'first', inplace=True)
    print(f"{largo_pre - len(noticias_unif)} registros duplicados eliminados")

    # Exportar DF a Excel - Guardar en carpeta especificada (path) al llamar la funcion
    file =  "noticias.xlsx"
    noticias_unif.to_excel(path + file, index = False)
    print(f"Noticias Diarias guardas en {path + file}")

# Ejecutar codigo
if __name__ == "__main__":
    ##Cambiar ruta a ubicacion de los archivos
    path = "C://RUTA/A/CARPETA/NOTICIAS/"
    recolectar_noticias(path) 