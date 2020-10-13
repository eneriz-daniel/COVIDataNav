"""
Este programa descarga los datos de
http://www.navarra.es/appsext/DescargarFichero/default.aspx?codigoAcceso=OpenData&fichero=coronavirus\CasosMunicipios_ZR_Covid.csv
y combrueba si están actualizados con
respecto a los descargados previamente.
Si son nuevos renombra el archivo y
llama a data_updater.py, si no lo elimina.

Version 1.0
Daniel Enériz Orta

"""


import urllib.request
import os

url = 'http://www.navarra.es/appsext/DescargarFichero/default.aspx?codigoAcceso=OpenData&fichero=coronavirus\CasosMunicipios_ZR_Covid.csv'
urllib.request.urlretrieve(url, 'CasosMunicipios_ZR_Covid_new.csv')

comparador = os.system('FC /A CasosMunicipios_ZR_Covid_new.csv CasosMunicipios_ZR_Covid.csv')

if comparador: #Abrá que adaptarlo a la consola en linux
    print('Actualización de datos, borrando viejo y renombrando archivo csv')
    os.remove('CasosMunicipios_ZR_Covid.csv')
    os.rename('CasosMunicipios_ZR_Covid_new.csv', 'CasosMunicipios_ZR_Covid.csv')

    os.system('python data_updater.py')
else:
    os.remove('CasosMunicipios_ZR_Covid_new.csv')