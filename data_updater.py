"""
En este programa se leen los datos del archivo CasosMunicipios_ZR_Covid.csv
y se genera un directorio para cada municipio en el que hay un json con los
casos positivos en el último día, en los últimos 15 días y los acumulados desde
el incio de la pandemia para esa localidad. Además se genera una gráfica con
la evolución de la pandemia en esa localidad.

Se descartan todos los casos nulos (sin información de localdiad) y los de Fuera de Navarra.

Version 1.0
Daniel Enériz Orta
"""


import pandas as pd
import matplotlib.pyplot as plt
import time
import datetime
import json
import os
import locale

locale.setlocale(locale.LC_TIME, 'es_ES')

df = pd.read_csv('CasosMunicipios_ZR_Covid.csv',encoding='latin-1', delimiter=';', parse_dates=[0]) # Cargamos datos

df = df[df.CodZR != -1] #Eliminamos los datos Nulos/Sin informar
df = df[df.CodMun != 0] #Eliminamos los datos de positivos de otras Comunidades Autónomas
df = df[df.CodZR != 99]

df = df.replace([' / ', '-'], '_', regex=True) # Renombremos los nombres en formato CASTELLANO / EUSKERA y CASTELLANO-EUSKERA para poder usarlos para crear directorios

                                       # Creamos un directorio donde guardar los datos resumidos en caso de que no exista
for municipio in df.DesMun.unique():
    try:
        os.mkdir('./Datos_municipios/{}'.format(municipio))
    except(FileExistsError):
        pass

df.Fecha = pd.to_datetime(df.Fecha) # Asignamos formato fecha a la fecha
df = df.set_index('Fecha')          # y lo usamos como ínidce para usar el atributo .last

for municipio in df.DesMun.unique():   # Recorremos todos los municipios para recopilar los datos de cada uno
    dfmun = df[df.DesMun == municipio]

    dfmun_tot = pd.DataFrame(0, index=pd.date_range(start=df.first('D').index[0]-datetime.timedelta(days=1), end=df.last('D').index[0], freq='D'), columns=['NuevosCasos', 'AcumuladoCasosHastaLaFecha'])

    for fecha in dfmun_tot.index.array:
        if fecha in dfmun.index.array:
            dfmun_tot.loc[fecha].NuevosCasos +=  dfmun.loc[fecha].NuevosCasos.sum()
            dfmun_tot.loc[fecha].AcumuladoCasosHastaLaFecha =  dfmun_tot.loc[fecha-datetime.timedelta(days=1)].AcumuladoCasosHastaLaFecha + dfmun.loc[fecha].NuevosCasos.sum()
        elif fecha != df.first('D').index[0]-datetime.timedelta(days=1):
            dfmun_tot.loc[fecha].AcumuladoCasosHastaLaFecha = dfmun_tot.loc[fecha-datetime.timedelta(days=1)].AcumuladoCasosHastaLaFecha

    #Calculammos los confirmados en los últimos 15 días, el relativo de estos cada 100000 habs, los casos en el último día y los acumulados hasta hoy
    casos_15dias = int(dfmun.last('1D').AcumuladoCasosHastaLaFecha.array.sum() - dfmun.last('15D')[dfmun.last('15D').index==dfmun.last('15D').index.array.min()].AcumuladoCasosHastaLaFecha.sum()  + dfmun.last('15D')[dfmun.last('15D').index==dfmun.last('15D').index.array.min()].NuevosCasos.sum())

    casos_ultimodia = int(dfmun.last('1D').NuevosCasos.array.sum())

    acumulados_hasta_hoy = int(dfmun.last('1D').AcumuladoCasosHastaLaFecha.array.sum())

    datos_municipio = {'Municipio': municipio, 'Fecha': df.last('1D').index[0].strftime('%d de %B de %Y'), 'Datos':{'Casos15dias': casos_15dias, 'CasosUltimoDia': casos_ultimodia, 'CasosAcum': acumulados_hasta_hoy}}

    with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio), 'w') as json_fout:
        json.dump(datos_municipio, json_fout)

    print('{}:\n\tÚltimo día: {}\n\t15 días: {}\n\tAcumulados: {}'.format(municipio, casos_ultimodia, casos_15dias, acumulados_hasta_hoy))


    fig, ax2 = plt.subplots()

    ax1 = ax2.twinx();  # instantiate a second axes that shares the same x-axis

    ax2.set_ylabel('Nuevos casos diarios')  # we already handled the x-label with ax1
    ax2.fill_between(dfmun_tot.index, dfmun_tot.NuevosCasos, color='C1', alpha=0.4, label='Casos nuevos')

    ax2.set_xlabel('Fecha')
    ax1.set_ylabel('Casos acumulados')
    ax1.plot(dfmun_tot.index, dfmun_tot.AcumuladoCasosHastaLaFecha, 'C0', label='Casos acumulados')

    marcas_x = pd.date_range(start=df.first('D').index[0], end=df.last('D').index[0], freq='MS')
    plt.xticks(marcas_x, marcas_x.strftime('%B'))

    fig.autofmt_xdate()

    fig.legend(loc="upper right", bbox_to_anchor=(0.4,1), bbox_transform=ax1.transAxes)

    plt.title(municipio+' '+df.last('1D').index[0].strftime('%d-%m-%y'))

    #fig.tight_layout()  # otherwise the right y-label is slightly clipped

    plt.savefig('./Datos_municipios/{}/{}_plot.png'.format(municipio, municipio), dpi=300)

    #plt.show()

    plt.close(fig)