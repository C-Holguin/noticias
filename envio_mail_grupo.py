from Noticias_colab_automatico import *

# Comparacion con registro histórico para prevenir redundancia
def chequeo_historico(diario, historico, path, omitir_duplicados = True):
    #Asignar campo de fecha para organizar historico
    fecha = diario.loc[0, "fecha_procesamiento"].date() # Leer fecha del primer registro diario
    diario["fecha_correo"] = fecha
    historico["fecha_correo"] = pd.to_datetime(historico["fecha_correo"]).dt.date #Ajustar fecha para igualar a excel

    # Solo actualizar historico si no coinciden ultimos registros (evitar repetir dias)
    if diario.iloc[-1]["fecha_correo"] != historico.iloc[-1]["fecha_correo"]:
        print("Actualizando Registros...")
        historico = pd.concat([historico, diario],  ignore_index = True)
        #Eliminar registros repetidos entre dias
        historico.drop_duplicates(subset = ['title', 'link_sitio'], keep = 'first', inplace = False)
        historico.to_excel(path + "historico_noticias.xlsx", index = False)

    else:
        print("El registro ya esta actualizado")
        # En caso de registros repetidos salir para no enviar el mail repetido
        if omitir_duplicados:
            sys.exit("El Correo Geográfico del día ya ha sido enviado.")

# Extraer titulo, contenido y link de DF de noticias para formatear mail
def extraer_noticias(noticias_df, grupo_col, alerta_col):
  # Iniciar Formato de HTML
  # Crear dicconario de Super Categorias (grupo)
  noticias_dict = {}
  # Iterar por DF
  for grupo_name, grupo_df in noticias_df.groupby(grupo_col):
      # Crear diccionario de alertas dentro de cada grupo
      alertas_dict = {}

      # Por cada alerta en el grupo
      for alerta, grupo in grupo_df.groupby(alerta_col):
          # Lista de diccionarios {'titulo' + 'contenido' + link} para cada alerta
          noticias = []

          # Cargar Noticia
          for _, row in grupo.iterrows():
              dict_n = {
                  'title': row['title'],
                  'content': row['content'],
                  'link': row['link']}
              noticias.append(dict_n)

          # Agregar noticias a diccionario de alertas
          alertas_dict[alerta] = noticias

      # Agregar alerta a clave de grupo
      noticias_dict[grupo_name] = alertas_dict
  # Devuelve diccionario de grupos -> diccionario alertas -> lista de noticias
  return noticias_dict

# Da formato HTML al conjunto de noticias (dict) recolectadas
def mail_html(fuente):
    #Obtener fecha actual para encabezado
    fecha = format_date(datetime.now(),"dd 'de' LLLL 'del' Y", locale = 'es')
    # Iniciar Formato de HTML
    ## Modificar formato segun se necesite
    html_content = f'''<html>
    <head>
        <div style = "border: 1px solid #ccc; width: 85%; padding: 10px; border-top: 10px solid #2475b2; background-color: #f0f0f0;  overflow: hidden">
          <div style= "display: flex; align-items: top;">
            <div style = "float: left; width: 70%;">
              <p>{fecha}</p>
          '''
    html_content += """
              <h1 style = 'margin-top: 0; margin-bottom: 0px; font-family: Arial,sans-serif; font-size: 34px; line-height: 32px; font-weight: bold; color: #303030'>El Correo Geográfico del IGN</h1>
            </div>
            <div style = "float: right; margin-left: auto; margin-right: 0; width: 30%;">
              <img src="https://drive.google.com/uc?export=view&id=18TdInkinZk1_5acRCpZDYmqu5PMlvm7a" alt="Logo MINDEF" width="50" style="margin-right: 10px; float: right">
              <img src="https://drive.google.com/uc?export=view&id=1PH3MN_cm9vkvpRRf7PJYyx6h3ExHMixu" alt="Logo IGN" width="90" style="margin-right: 10px; float: right">
            </div>
          </div>
          <p> Resumen de las noticias más relevantes del ámbito geográfico en Argentina y en el mundo</p>
          <p> El Correo Geográfico del IGN es un desarrollo de la Dirección de Información Geoespacial, Dirección Nacional de Servicios Geográficos del Instituto Geográfico Nacional, República Argentina</p>
        </div>
        <style>
          @media screen and (max-width: 600px) {
            .content {
                width: 100% !important;
                display: block !important;
                padding: 10px !important;
            }
            .header, .body, .footer {
                padding: 20px !important;
            }
          }
        </style>
    </head>
    <body style = 'font-family: sans-serif'>"""

    # Agrupar cada categoría en un div
    for category, alerts in fuente.items():
        html_content += f"<div style = 'border: 1px solid #ccc; padding: 10px; margin: 10px 0; width: 85%; border-top: 4px solid #27678a'><h2 style = 'font-family: Verdana; font-size: 24px; color: #303030; font-weight: bold;'>{category.upper()}</h2>"
        #A grupar cada Alerta en un div
        for alert in alerts:
            html_content += f"<div style = 'border: 1px solid #ccc; border-radius: 8px; padding: 10px; margin: 10px 0; background-color: #f9f9f9; box-shadow: 0px 2px 5px rgba(0,0,0,0.1);'><b style = 'font-size: 21px; line-height: 1.8; color: #000000'>{alert.upper()}</b>"
            # Agregar cada noticia como TITULO con Hipervinculo + Contenido
            for noticia in fuente[category][alert]:
              html_content += f"""
        <div>
              <a href = \'{noticia["link"]}\' target = \'_blank\' style = 'text-decoration: none'><h3 style = 'font-size: 18px; color: 0; font-weight: bold; line-height: 1.3; margin-bottom :5px'> ■ {noticia["title"]}</h3></a>
              <em style = 'margin: 0'>{noticia["content"]}</em><br>
        </div>
          """
            html_content += "</div>"
        html_content += "</div>"
    html_content += '''<p style = 'font-family: Helvetica; font-size: 18px; text-align: left'>Dirección Nacional de Servicios Geográficos (DNSG) - Dirección Información Geoespacial (DIG)</p>
    </body>
    <footer>
        <div>
            <a class = "facebook" href="https://www.facebook.com/institutogeograficonacional" target="_blank" style='text-decoration: none'>
                <img src="https://drive.google.com/uc?export=view&id=1KIeklHRqz5vlomyk62ZBXL8N_yjv0bwh" alt="Facebook IGN" width="30" style="margin-right: 10px;">
            </a>
            <a class = "instagram" href="https://www.instagram.com/argentinaignoficial/" target="_blank" style='text-decoration: none'>
                <img src="https://drive.google.com/uc?export=view&id=18IeSzTgga13jDv4lwPdA5nJMcE7fVvX6" alt="Instagram IGN" width="31" style="margin-right: 10px;">
            </a>
            <a class = "twitter" href="https://x.com/ARGENTINAIGN" target="_blank" style='text-decoration: none'>
                <img src="https://drive.google.com/uc?export=view&id=1nR7pkePCeKdQF0HoDuL24oxGLkHQxWLE" alt="Twitter IGN" width="30" style="margin-right: 10px;">
            </a>
            <a class = "youtube" href="https://www.youtube.com/IgnArgentina" target="_blank" style='text-decoration: none'>
                <img src="https://drive.google.com/uc?export=view&id=1p-ivTy9kW4m4yhkYftNZbpyyoWA2kA0d" alt="YouTube IGN" width="30" style="margin-right: 10px;">
            </a>
            <p>Avda. Cabildo 381 - C1426AAD - C.A.B.A.<br>República Argentina</p>
        </div>
    </footer>
</html>'''
    # Devuelve html formateado como string
    return html_content

# Enviar Correo Geográfico a dirección indicada
def enviar_mail(mail_de, pswd_de, mail_a, contenido_html):
    #Dar formato a mail
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = "CORREO GEOGRÁFICO"
    mensaje["From"] = mail_de
    mensaje["To"] = mail_a

    # Cargar texto HTML de noticias
    html_part = MIMEText(contenido_html, "html")
    mensaje.attach(html_part)

    #Enviar mail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(mail_de, pswd_de) #Ingresar a cuenta noticias
        smtp.sendmail(from_addr = mail_de, to_addrs = mail_a, msg = mensaje.as_string()) #Enviar mail
        print(f"Mail enviado con exito desde {mail} a {mail_a}")


# Recoleccion de noticias en excel diario (noticias.xlsx) - Ejecuta código de Noticias_colab_automatico
path = "C://RUTA/A/CARPETA/NOTICIAS/"
recolectar_noticias(path) 

# Cargar noticias encontradas
noticias_unif = pd.read_excel(path + "noticias.xlsx")
reg_historico = pd.read_excel(path + "historico_noticias.xlsx")

# Actualizar historico si fecha diaria no coincide con fecha de ultimo registro
chequeo_historico(diario = noticias_unif, historico = reg_historico, path = path, omitir_duplicados = False) #True cancela mail si el registro esta actualizado

# Extraer Datos de cada noticia
noticias_dict = extraer_noticias(noticias_unif, "grupo", "alerta")

# Cargar datos de noticias a funcion HTML
print("Formateando mail...")
html_content = mail_html(noticias_dict)

# Parametros del mail a enviar
#Extraer informacion de cuenta de archivo credenciales.txt
with open(path + "credenciales.txt") as file:
    credenciales = [line.rstrip() for line in file]
    mail = credenciales[0]
    password = credenciales[1]

## Completar nombre de grupo donde se comparten las noticias
grupo_mail = ["grupo_noticias@googlegroups.com"]#Reemplazar por nombre real

# Enviar Correo Geografico
for destino in grupo_mail:
    enviar_mail(mail, password, destino, html_content)