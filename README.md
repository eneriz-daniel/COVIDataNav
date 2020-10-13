# Introducción

El objetivo que tengo con COVIDataNav es acercar los datos que publica el Gobierno de Navarra en su página de [Gobierno Abierto de Navarra](https://gobiernoabierto.navarra.es/) sobre las [PCRs postivas distribuidas por municipios](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distruidos-por-municipio).

Para ello he escrito tres programas:

- `data_downloader.py`, que se encarga de descargar los datos de la web.
- `data_updater.py`, que lee los datos descargados y los procesa para obtener los datos de cada municipio (casos en el último día, en los últimos 15 días y casos acumulados desde el inicio de la pandemia)
- `COVIDataNav_bot.py`, bot de Telegram usando `python-telegram_bot` permite visualizar los datos y configurar un envío diario de datos

# Colaboración

Si tienes experiencia en el tratamiento de datos o en la comunicación de estos y deseas utilizar el código o colaborar, ¡perfecto! Puedes contactar con mi por [Telegram](https://bit.ly/3iSWyUg) mismo.

Lo único: es la primera vez que uso `pandas` y `python-telegram-bot` supongo que habrá mil cosas mal o mejorables, pero parece que funciona.

# Nota sobre el tratamiento de los datos
 
He omitido los datos Nulos/Sin registrar y de Fuera de Navarra porque no tenía claro la asociación de estos a los municipios.


# Nota de responsabilidad

El canal no es oficial y el autor no garantiza ni asume ninguna responsabilidad legal o de cualquier otro tipo por la exactitud, carácter integral o la utilidad de cualquier información, mecanismo. producto o proceso divulgado.
