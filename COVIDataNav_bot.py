"""
Bot de Telegram de COVIDataNav

Está basado en el ejemplo de Python-Telegram-Bot de 
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py

Acepta 6 comandos:
/start - Muestra la información general del bot y da una explicación del funcionamiento
/ver <localdiad> - Envía los casos positivos en el último día, los últimos 15 días y los
                   casos desde el inicio de la pandemia junto con una gráfica de evolución para la localidad elegida.
/configurar <localidad> <hora entre 0 y 23> - Permite configurar un envío diario de los datos que devuelve /ver a una hora elegida (entre 0 y 23)
/desconfigurar - Elimina el envío diario
/info - Muestra información sobre el Bot
/help - Muestra la lista de comandos

Para identificar un municipio desde la entrada de un usuario se usa la métrica edit_distance
de nltk. En las primeras pruebas ha sido capaz de identificar todos los municipios siempre
que sea una entrada decente.

Versión 1.0

Daniel Enériz Orta
"""

import logging
from nltk import edit_distance
from os import listdir
import numpy as np
import json
from datetime import time
import pytz
from random import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Cargamos la lista de municipios
municipios = np.array(listdir('./Datos_municipios/'))
orig_municipios = municipios

# Los procesamos para poder identificarlos tanto en Castellano como en Euskera
for mun in municipios:
    if '_' in mun:
        municipios = np.append(municipios, mun.split('_'))

# Nos permite identificar los 4 municipio de la lista más 'similares' al de la entrada
def Identifica_municipio(mun_in):

    distancia = np.empty_like(municipios) # Array de valores asociados a los municipios, cuanto más bajo mas cercano a la entrada original

    for i in range(len(municipios)): # La calculamos con la función de nltk
        distancia[i] = edit_distance(mun_in.upper(), municipios[i])

    mun_cercanos = municipios[distancia.argsort()[:4]] # Escogemos los 4 primeros, para dar 4 opciones

    mun_orig_cercanos = []
    
    for i in range(len(mun_cercanos)): # Llevamos la opciones a la lista de munuicipio originales
        for mun in orig_municipios:
            if (mun_cercanos[i] in mun) and (mun not in mun_orig_cercanos):
                mun_orig_cercanos.append(mun)
    
    return(mun_orig_cercanos)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hola\! \nEste bot esta hecho para consultar los datos sobre *PCRs"
                              " positivas* en cada localidad de Navarra en base a los *datos pub"
                              "ilicados por el Gobierno de Navarra* en este [link](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distruidos-por-municipio)\.\n\n"
                              "*NO ES UN CANAL OFICIAL*\n\n"
                              "Puedes usar el comando /ver `<localidad>` para que te muestre una gráfica con la *evolución"
                              " del número de casos* en esa localidad y  los *casos confirmados en el último día y en los últimos"
                              " 15 días*\.\n"
                              "Si quieres recibir esa información cada vez que el Gobierno de Navarra la acualice puedes usar el"
                              " comando /configurar `<localidad>` `<hora entre 0 y 23>` y te lo mandaré diariamente a la hora que elijas\.\n\n"
                              "Para mas información sobre los datos y sobre el bot usa el comando /info\. Usando /help te mandaré la lista de comandos disponibles\.", parse_mode='MarkdownV2')


def info(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Este bot esta hecho para consultar los datos sobre *PCRs"
                              " positivas* en cada localidad de Navarra en base a los *datos pub"
                              "ilicados por el Gobierno de Navarra* en este [link](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distruidos-por-municipio)\.\n\n"
                              "Si consultas la página verás que tienen colgado un documento `\.csv`"
                              " que actualizan diariamente con información sobre las PCRs positivas"
                              " en las localdiades navarras junto con los casos acumulados desde el"
                              " inicio la de pandemia\.\nEl objetivo principal de este bot es acercar los datos"
                              " a la ciudadanía\. Para ello he desarrollado un pequeño programa que se encarga"
                              " de preprar los datos para que sean consultables através de este canal\."
                              "\nPara más infromación sobre el código y la forma de tratar los datos puedes acceder"
                              " a este [enlace](http://bit.ly/COVIDataNav-GitHub)\.\n\n"
                              "Si tienes experiencia con el tratamiento de datos o con la comunicaión de estos"
                              " através de este u otros canales y quieres colaborar no dudes en ponerte en contacto"
                              " con mi através de este [enlace](https://bit.ly/3iSWyUg)\.\n\n"
                              "El autor no garantiza ni asume ninguna responsabilidad legal o de cualquier otro tipo"
                              " por la exactitud, carácter integral o la utilidad de cualquier información, mecanismo,"
                              " producto, o proceso divulgado\.", parse_mode='MarkdownV2')


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Los comandos que puedes usar son:\n"
                               "/ver `<localidad>` - Muestra los datos de una localidad en concreto\n"
                               "/configurar `<localidad>` `<hora entre 0 y 23>` - Permite configurar una localidad para recibir las actualizaciones en los datos cada vez que el Gobierno de Navarra las actualiza\n"
                               "/desconfigurar - Permite eliminar el aviso diario de la localidad configurada previamente\n"
                               "/info - Mustra información sobre los datos y sobre el bot\n"
                               "/help - Muestra la lista de comandos disponibles", parse_mode='MarkdownV2')


def ver(update, context):

    # args[0] should contain the time for the timer in seconds
    municipio = Identifica_municipio(context.args[0])[0]

    with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio)) as json_file:
        data = json.load(json_file)

        update.message.reply_text('Datos de {} del {}:\n'
                                    'Casos en el último día: {}\n'
                                    'Casos en los últimos 15 días: {}\n'
                                    'Casos acumulados desde el incio: {}'.format(data['Municipio'], data['Fecha'], data['Datos']['CasosUltimoDia'], data['Datos']['Casos15dias'], data['Datos']['CasosAcum']))

    update.message.reply_photo(open('./Datos_municipios/{}/{}_plot.png'.format(municipio,municipio),'rb'))


def configurar(update, context):

    """Add a job to the queue."""
    chat_id = update.message.chat_id
    
    # args[0] should contain the time for the timer in seconds
    municipio = Identifica_municipio(context.args[0])[0]

    if not(0<=int(context.args[1])<24):
        update.message.reply_text('Tienes que mandar una hora entre 0 y 23')
        return

    hora = time(hour=int(context.args[1]), minute=int(random()*5), tzinfo=pytz.timezone("Europe/Madrid"))

    # Add job to queue and stop current one if there is a timer already
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    new_job = context.job_queue.run_daily(mandar_configurado, hora, context={"chat_id": chat_id, "municipio": municipio})
    context.chat_data['job'] = new_job

    update.message.reply_text('Te mandaré los datos de {} todos los días sobre las {}'.format(municipio, hora.strftime('%H:00')))

def desconfigurar(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('No tienes ningún municipio configurado')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Municipio desconfigurado correctamente')

def mandar_configurado(context):
    job = context.job
    municipio = job.context['municipio']
    chat_id = job.context['chat_id']

    with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio)) as json_file:
        data = json.load(json_file)

        context.bot.send_message(chat_id, 'Datos de {} del {}:\n'
                                          'Casos en el último día: {}\n'
                                          'Casos en los últimos 15 días: {}\n'
                                          'Casos acumulados desde el incio: {}'.format(data['Municipio'], data['Fecha'], data['Datos']['CasosUltimoDia'], data['Datos']['Casos15dias'], data['Datos']['CasosAcum']))

    context.bot.send_photo(chat_id, open('./Datos_municipios/{}/{}_plot.png'.format(municipio,municipio),'rb'))


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("TOKEN", use_context=True)

    

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(
        CommandHandler("ver", ver, pass_args=True)
    )
    dp.add_handler(
        CommandHandler("configurar", configurar, pass_args=True, pass_chat_data=True)
    )
    dp.add_handler(CommandHandler("desconfigurar", desconfigurar, pass_chat_data=True))

    # on noncommand i.e message - echo the message on Telegram
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()