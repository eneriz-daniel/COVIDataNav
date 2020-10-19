"""
Bot de Telegram de COVIDataNav

Está basado en el ejemplo de Python-Telegram-Bot de 
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py

Acepta 6 comandos:
/start - Muestra la información general del bot y da una explicación del funcionamiento
/ver <localdiad> - Envía los casos positivos en el último día, los últimos 15 días y los
                   casos desde el inicio de la pandemia junto con una gráfica de evolución para la localidad elegida.
Deshabilitado -- /configurar <localidad> <hora entre 0 y 23> - Permite configurar un envío diario de los datos que devuelve /ver a una hora elegida (entre 0 y 23)
Deshabilitado -- /desconfigurar - Elimina el envío diario
/info - Muestra información sobre el Bot
/help - Muestra la lista de comandos

Para identificar un municipio desde la entrada de un usuario se usa get_close_matches
de difflib.

Versión 1.1.1

Daniel Enériz Orta
"""

import logging
from difflib import get_close_matches
from os import listdir
from parse import *
import numpy as np
import json
import datetime as dt
import time
import pytz
from random import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, JobQueue

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

    mun_cercanos = get_close_matches(mun_in.upper(), municipios)

    mun_orig_cercanos=[]
    
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
                              "Si quieres recibir esa información cada vez que el Gobierno de Navarra la actualice puedes usar el"
                              " comando /configurar `<localidad>` `<hora entre 0 y 23>` y te lo mandaré diariamente a la hora que elijas\.\n\n"
                              "Para mas información sobre los datos y sobre el bot usa el comando /info\. Usando /help te mandaré la lista de comandos disponibles\.", parse_mode='MarkdownV2')


def info(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Este bot esta hecho para consultar los datos sobre *PCRs"
                              " positivas* en cada localidad de Navarra en base a los *datos pub"
                              "ilicados por el Gobierno de Navarra* en este [link](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distruidos-por-municipio)\.\n\n"
                              "Si consultas la página verás que tienen colgado un documento `\.csv`"
                              " que actualizan diariamente con información sobre las PCRs positivas"
                              " en las localidades navarras junto con los casos acumulados desde el"
                              " inicio la de pandemia\.\nEl objetivo principal de este bot es acercar los datos"
                              " a la ciudadanía\. Para ello he desarrollado un pequeño programa que se encarga"
                              " de preparar los datos para que sean consultables a través de este canal\."
                              "\nPara más información sobre el código y la forma de tratar los datos puedes acceder"
                              " a este [enlace](http://bit.ly/COVIDataNav-GitHub)\.\n\n"
                              "Si tienes experiencia con el tratamiento de datos o con la comunicación de estos"
                              " a través de este u otros canales y quieres colaborar no dudes en ponerte en contacto"
                              " con mí a través de este [enlace](https://bit.ly/3iSWyUg)\.\n\n"
                              "El autor no garantiza ni asume ninguna responsabilidad legal o de cualquier otro tipo"
                              " por la exactitud, carácter integral o la utilidad de cualquier información, mecanismo,"
                              " producto, o proceso divulgado\.", parse_mode='MarkdownV2')


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Los comandos que puedes usar son:\n"
                               "/ver `<localidad>` - Muestra los datos de una localidad en concreto\n"
                               "/configurar `<localidad>` `<hora entre 0 y 23>` - Permite configurar una localidad para recibir las actualizaciones en los datos cada vez que el Gobierno de Navarra las actualiza\n"
                               "/desconfigurar - Permite eliminar el aviso diario de la localidad configurada previamente\n"
                               "/info - Muestra información sobre los datos y sobre el bot\n"
                               "/help - Muestra la lista de comandos disponibles", parse_mode='MarkdownV2')


def ver(update, context):

    if len(context.args) == 0:
        update.message.reply_text('Uso: /ver <localidad>\nPor ejemplo: /ver Pamplona')
        return

    for arg in context.args:
        if '<' or '>' in arg:
            update.message.reply_text('Uso: /ver <localidad>\nPor ejemplo: /ver Pamplona')
        return

    with open('./ver_history.txt', 'a') as file: # Guardamos las peticiones
        file.write('{} {}\n'.format(time.strftime('%Y-%m-%dT%H:%M:%S'), ' '.join(context.args)))


    # args[0] should contain the time for the timer in seconds
    municipios = Identifica_municipio(' '.join(context.args))

    if len(municipios) == 0:
        update.message.reply_text('Uso: /ver <localidad>\nPor ejemplo: /ver Pamplona\n\n Si no aparecen opciones para tu localidad es que no se ha registrado ningún caso.')
        return

    if len(municipios) > 1:
        if len(municipios) == 2:

            keyboard = [
                [
                    InlineKeyboardButton(municipios[0], callback_data=municipios[0]),
                    InlineKeyboardButton(municipios[1], callback_data=municipios[1]),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text('*Elige entre estas opciones*\.\nSi tu localidad no aparece y has escrito bien el nombre es que aún no se ha registrado ningún caso\.', reply_markup=reply_markup, parse_mode='MarkdownV2')

        elif len(municipios) == 3:

            keyboard = [
                [
                    InlineKeyboardButton(municipios[0], callback_data=municipios[0]),
                    InlineKeyboardButton(municipios[1], callback_data=municipios[1]),
                ],
                [ InlineKeyboardButton(municipios[2], callback_data=municipios[2]),]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text('*Elige entre estas opciones*\.\nSi tu localidad no aparece y has escrito bien el nombre es que aún no se ha registrado ningún caso\.', reply_markup=reply_markup, parse_mode='MarkdownV2')
        
        else:

            keyboard = [
                [
                    InlineKeyboardButton(municipios[0], callback_data=municipios[0]),
                    InlineKeyboardButton(municipios[1], callback_data=municipios[1]),
                ],
                [
                    InlineKeyboardButton(municipios[2], callback_data=municipios[2]),
                    InlineKeyboardButton(municipios[3], callback_data=municipios[3]),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text('*Elige entre estas opciones*\.\nSi tu localidad no aparece y has escrito bien el nombre es que aún no se ha registrado ningún caso\.', reply_markup=reply_markup, parse_mode='MarkdownV2')

    else:
        municipio = municipios[0]
        with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio)) as json_file:
            data = json.load(json_file)

            update.message.reply_text('Datos de {} del {}:\n'
                                        'Casos en el último día: {}\n'
                                        'Casos en los últimos 15 días: {}\n'
                                        'Casos acumulados desde el inicio: {}'.format(data['Municipio'], data['Fecha'], data['Datos']['CasosUltimoDia'], data['Datos']['Casos15dias'], data['Datos']['CasosAcum']))

        update.message.reply_photo(open('./Datos_municipios/{}/{}_plot.png'.format(municipio,municipio),'rb'))


def button(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    municipio = query.data

    with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio)) as json_file:
        data = json.load(json_file)

        query.edit_message_text(text = 'Datos de {} del {}:\n'
                                    'Casos en el último día: {}\n'
                                    'Casos en los últimos 15 días: {}\n'
                                    'Casos acumulados desde el inicio: {}'.format(data['Municipio'], data['Fecha'], data['Datos']['CasosUltimoDia'], data['Datos']['Casos15dias'], data['Datos']['CasosAcum']))
    
    query.message.reply_photo(open('./Datos_municipios/{}/{}_plot.png'.format(municipio,municipio),'rb'))



def configurar(update, context):

    update.message.reply_text('He encontrado problemas en esta función y he decidido desactivarla temporalmente.')
    
    """

    if len(context.args) != 2:
        update.message.reply_text('Uso: /configurar <localidad> <hora (entre 0 y 23)>\nPor ejemplo: /configurar Pamplona 10')
        return

    #Add a job to the queue
    chat_id = update.message.chat_id
    
    # args[0] should contain the time for the timer in seconds
    municipio = Identifica_municipio(context.args[0])[0]

    if not(0<=int(context.args[1])<24):
        update.message.reply_text('Tienes que mandar una hora entre 0 y 23')
        return

    with open('./configurar_history.txt', 'a') as file: # Guardamos las peticiones
        file.write('{} {} {} {}\n'.format(time.strftime('%Y-%m-%dT%H:%M:%S'), municipio, context.args[0], context.args[1]))

    with open('./active_jobs.txt', 'a') as file: # Guardamos las peticiones
        file.write('{} {} {}\n'.format(chat_id, municipio, context.args[1]))

    hora = dt.time(hour=int(context.args[1]), minute=int(random()*5), tzinfo=pytz.timezone("Europe/Madrid"))

    # Add job to queue and stop current one if there is a timer already
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    new_job = context.job_queue.run_daily(mandar_configurado, hora, context={"chat_id": chat_id, "municipio": municipio})
    context.chat_data['job'] = new_job

    update.message.reply_text('Te mandaré los datos de {} todos los días sobre las {}'.format(municipio, hora.strftime('%H:00')))

    """

def desconfigurar(update, context):
    """Remove the job if the user changed their mind."""

    update.message.reply_text('He encontrado problemas en esta función y he decidido desactivarla temporalmente.')

    """
    
    if 'job' not in context.chat_data:
        update.message.reply_text('No tienes ningún municipio configurado')
        return

    with open('./active_jobs.txt', 'r') as file: # Guardamos las peticiones
        lines = file.readlines()
        for i in range(len(lines)):
            if str(update.message.chat_id) in lines[i]:
                del(lines[i])
                break
    
    with open('./active_jobs.txt', 'w+') as file: # Guardamos las peticiones
        for line in lines:
            file.write(line)

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Municipio desconfigurado correctamente')
    """

def mandar_configurado(context):
    job = context.job
    municipio = job.context['municipio']
    chat_id = job.context['chat_id']

    with open('./Datos_municipios/{}/{}_data.json'.format(municipio, municipio)) as json_file:
        data = json.load(json_file)

        context.bot.send_message(chat_id, 'Datos de {} del {}:\n'
                                          'Casos en el último día: {}\n'
                                          'Casos en los últimos 15 días: {}\n'
                                          'Casos acumulados desde el inicio: {}'.format(data['Municipio'], data['Fecha'], data['Datos']['CasosUltimoDia'], data['Datos']['Casos15dias'], data['Datos']['CasosAcum']))

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
    dp.add_handler(CallbackQueryHandler(button))
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