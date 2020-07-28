'''
Herramientas necesarias para el experimento:

    - OpenBCI
    - Script en Python:
        - Lanzar imágenes
        - Capturar señales mediante LSL

Procedimiento a seguir:
    - Iniciamos OpenBCI (para capturar del BCI)
        - Empezamos a capturar con LSL ON

    - Iniciamos script "main.py"
        - Se lanzará un hilo de captura de señal
        - Una vez demos a [ENTER] empezará el experimento.

    NOTAS:
        - Es necesario introducir cada uno de los parámetros al iniciar la aplicación.
        - Los valores default de los parámetros de entrada pueden no ser apropiados para el experimento a realizar.
'''

import logging

from psychopy import logging as psycholog
from termcolor import colored

psycholog.console.setLevel(logging.CRITICAL)
import numpy as np
from random import randint
from pandas import DataFrame
from psychopy import visual, core, event, monitors
from time import time
from pylsl import StreamInfo, StreamOutlet, local_clock
from glob import glob
from random import choice
import os

os.system('color')
from datetime import datetime
import argparse

import requests
import json
import shutil

from record import record_experiment
from threading import Thread

VERSION = '1.0beta'
API = 'WzOc1qxm5F5RRnGik4f6A2qQ3sogZyH8W5yFiNOURKw'


def printInfo(string):
    print(colored('[!] ' + string, 'yellow'))


def printError(string):
    print(colored('[!] ' + string, 'red'))


def printSuccess(string):
    print(colored('[!] ' + string, 'green'))


def main():
    '''
    [!] FUNCIÓN principal del Trabajo Fin de Grado
        Es lanzado junto a los parámetros adecuados y se encargará de llevar a cabo el experimento.
        Manejará la construcción del hilo de captura de señal EEG, así como de mostrar las imágenes en pantalla.
    '''

    banner = """
            ██████╗  ██████╗██╗   ████████╗███████╗ ██████╗ 
            ██╔══██╗██╔════╝██║   ╚══██╔══╝██╔════╝██╔════╝ 
            ██████╔╝██║     ██║█████╗██║   █████╗  ██║  ███╗
            ██╔══██╗██║     ██║╚════╝██║   ██╔══╝  ██║   ██║
            ██████╔╝╚██████╗██║      ██║   ██║     ╚██████╔╝
            ╚═════╝  ╚═════╝╚═╝      ╚═╝   ╚═╝      ╚═════╝ 
                                Enrique Tomás Martínez Beltrán
    """
    print(colored(banner, 'yellow'))

    parser = argparse.ArgumentParser(description='Obtención de señal EEG. Ejecución del experimento.', add_help=False)

    parser.add_argument('-n', '--name', dest='name',
                        default="exp_{}".format(datetime.now().strftime("%d-%m-%Y-%H-%M-%S")),
                        help='Nombre del experimento')
    parser.add_argument('-dim', '--dim', dest='size_monitor', default=[1920, 1080],
                        help='Dimensiones de la pantalla (default [1920,1080])')
    parser.add_argument('-dm', '--distmon', dest='distance_monitor', default=67,
                        help='Distancia al monitor -en centímetros- (default 67)')
    parser.add_argument('-m', '--mode', dest='mode', default=2,
                        help='Modo de ejecución del programa (default 2)')
    # parser.add_argument('-t', '--time', dest='time', default=20,
    #                     help='Tiempo de duración de la grabación')
    parser.add_argument('-i', '--images', dest='images', default=30,
                        help='Número de imágenes distintas utilizadas en el experimento (default 30)')
    parser.add_argument('-p', '--prob', dest='prob_target', default=0.1,
                        help='Probabilidad de aparición del Target en el experimento -tanto por 1- (default 0.1)')
    parser.add_argument('-tt', dest='target_time', default=5,
                        help='Tiempo de visualización del target -en segundos- (default 5)')
    parser.add_argument('-in', dest='image_interval', default=0.250,
                        help='Tiempo transcurrido entre imágenes -en segundos- (default 0.250)')
    parser.add_argument('-io', dest='image_offset', default=0.150,
                        help='Tiempo offset de cada imagen -en segundos- (default 0.150)')
    parser.add_argument('-j', dest='jitter', default=0.2,
                        help='Tiempo jitter variable al mostrar imagen -en segundos- (default 0.2)')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + VERSION, help="Versión del programa.")
    parser.add_argument('-a', '--about', action='version',
                        version='Creado por Enrique Tomás Martínez Beltrán',
                        help="Información sobre el creador del programa.")
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Ayuda sobre la utilización del programa.')

    args = parser.parse_args()

    experiment = args.name
    experiment = 'exp_23-07-2020-00-28-33'
    # experiment_time = float(args.time)
    mode = args.mode
    total_img = int(args.images)
    size_monitor = args.size_monitor
    prob_target = float(args.prob_target)
    distance_monitor = int(args.distance_monitor)

    try:

        if not os.path.isdir('experiments/' + experiment):
            os.makedirs("experiments/{}/target".format(experiment))
            os.makedirs("experiments/{}/no_target".format(experiment))
            os.makedirs("experiments/{}/records".format(experiment))

        if not os.listdir('experiments/{}/target'.format(experiment)) or not os.listdir(
                'experiments/{}/no_target'.format(experiment)):
            if (mode == 1):
                printInfo("Modo 1 seleccionado (Modo manual)")
                # Las imágenes son añadidas manualmente, únicamente se obtienen con la aplicación

            elif (mode == 2):
                printInfo("Modo 2 seleccionado (Modo automático)")
                printInfo("Descargando recursos...")

                url_all = "https://api.unsplash.com/photos/random?count={}".format(total_img)

                headers = {
                    'Authorization': 'Client-ID {}'.format(API)
                }

                response = requests.get(url_all, headers=headers, stream=True)

                response_json = json.loads(response.text)
                is_target = False
                count = 0
                for image in response_json:
                    url = image['urls']['raw']

                    response = requests.get(url + '&fm=jpg&fit=crop&w=1920&h=1080&q=80&fit=max', headers=headers,
                                            stream=True)
                    if not is_target:
                        with open('experiments/{}/target/target.jpeg'.format(experiment), 'wb') as out_file:
                            shutil.copyfileobj(response.raw, out_file)
                        is_target = True
                        continue

                    with open('experiments/{}/no_target/no_target_{}.jpeg'.format(experiment, count),
                              'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                    del response

                    count = count + 1

        image_interval = float(args.image_interval)
        image_offset = float(args.image_offset)
        jitter = float(args.jitter)
        target_time = int(args.target_time)

        # Lanzamos el hilo
        # Esperará hasta que pulsamos <enter> para empezar la captura sincronizada.

        # Tiempo aproximado del experimento.
        # Será utilizado por el hilo para grabar X segundos (serán siempre más para evitar cortes en el experimento)
        experiment_time = total_img * image_interval * image_offset + total_img / 2
        process = Thread(target=record_experiment, args=[experiment, experiment_time])
        process.start()
        print()

        printInfo("Nombre del experimento: " + experiment)
        printInfo("Dimensiones de la pantalla: ancho={} | alto={}".format(size_monitor[0], size_monitor[1]))
        printInfo("Ruta del experimento: experiments/{}".format(experiment))
        printInfo("Duración aproximada del experimento: " + str(experiment_time) + " s")
        printInfo("Tiempo devisualización de Target pre-experimento: " + str(target_time * 1000) + " ms")
        printInfo("Intervalo entre imágenes: " + str(image_interval * 1000) + " ms")
        printInfo("Probabilidad de aparición Target: " + str(prob_target * 100) + " %")

        if jitter:
            printInfo("Jitter: " + str(jitter * 1000) + " ms")
        '''
        1 -> TARGET
        0 -> NO TARGET
        '''
        # Array con total_images de [0,1] con 0.1 de probabilidad el 1 -> TARGET
        img_types = np.random.binomial(1, prob_target, total_img)
        # Ajuste para evitar 2 o más Target seguidos
        def check(lst):
            caux = 0
            last = lst[0]
            for i, num in enumerate(lst[1:]):
                if num == 1 and last == 1:
                    caux = caux + 1
                    lst[i] = 0
                last = num
            return caux

        n = check(img_types)
        for i in range(n):
            while (True):
                r = randint(0, len(img_types))
                if img_types[r] != 1:
                    img_types[r] = 1
                if (check(img_types)):
                    continue
                else:
                    break

        images = DataFrame(dict(img_type=img_types,
                                  timestamp=np.zeros(total_img)))
        images.to_csv('experiments/{}/metadata.txt'.format(experiment), index=False)

        print()
        printInfo("DataFrame generado: ")
        print()
        print(images)
        print()

        mon = monitors.Monitor('asusmon')
        mon.setDistance(distance_monitor)
        window = visual.Window(size_monitor, monitor=mon, units="pix",
                              fullscr=False, color=[-1, -1, -1])

        def cargarImagen(file):
            nonlocal window
            return visual.ImageStim(win=window, image=file, size=size_monitor)

        targets = []
        no_targets = []

        t_argets = glob('experiments/{}/target/*.jpeg'.format(experiment))
        for i in t_argets:
            targets.append(cargarImagen(i))

        not_argets = glob('experiments/{}/no_target/*.jpeg'.format(experiment))
        for i in not_argets:
            no_targets.append(cargarImagen(i))

        text1 = visual.TextBox(window=window,
                               text='[Trabajo Fin de Grado - Enrique Tomás Martínez Beltrán]',
                               font_size=20,
                               font_color=[1, 1, 1],
                               textgrid_shape=[55, 2],
                               pos=(0.0, 0.6),
                               # border_color=[-1, -1, 1, 1],
                               # border_stroke_width=4,
                               # grid_color=[1, -1, -1, 0.5],
                               # grid_stroke_width=1
                               )

        text2 = visual.TextBox(window=window,
                               text='Presiona <enter> para comenzar el experimento...',
                               font_size=20,
                               font_color=[1, 1, 1],
                               textgrid_shape=[48, 2],
                               pos=(0.0, 0.3),
                               # border_color=[-1, -1, 1, 1],
                               # border_stroke_width=4,
                               # grid_color=[1, -1, -1, 0.5],
                               # grid_stroke_width=1
                               )

        text3 = visual.TextBox(window=window,
                               text='Fin del experimento...',
                               font_size=20,
                               font_color=[1, 1, 1],
                               textgrid_shape=[55, 2],
                               pos=(0.0, 0.6),
                               # border_color=[-1, -1, 1, 1],
                               # border_stroke_width=4,
                               # grid_color=[1, -1, -1, 0.5],
                               # grid_stroke_width=1
                               )

        text4 = visual.TextBox(window=window,
                               text='¡Gracias por participar!',
                               font_size=20,
                               font_color=[1, 1, 1],
                               textgrid_shape=[48, 2],
                               pos=(0.0, 0.3),
                               # border_color=[-1, -1, 1, 1],
                               # border_stroke_width=4,
                               # grid_color=[1, -1, -1, 0.5],
                               # grid_stroke_width=1
                               )
        logo_umu = visual.ImageStim(win=window, image="experiments/umu.jpg", units='pix')
        logo_umu.pos += -0.3
        logo_umu.size = [610, 140]

        text1.draw()
        text2.draw()
        logo_umu.draw()

        window.flip()

        '''
        Si presionamos [ENTER] -> Iniciamos el experimento
            Creamos Estimulo Stream para que sea detectado por el hilo
        '''
        key = event.waitKeys()
        while ('return' not in key):
            key = event.waitKeys()

        core.wait(3)

        '''
        Mostramos Target, el experimento comenzará después de mostrar X segundos la imagen Target
        '''
        target = choice(targets)
        target.draw()
        window.flip()
        core.wait(target_time)
        window.flip()

        info = StreamInfo('Estimulo', 'Estimulo', 1, 0, 'int32', 'estimulo12310')

        outlet = StreamOutlet(info)

        nImage = 0
        nTarget = 0
        nNoTarget = 0
        for i, trial in images.iterrows():

            # Intervalo entre imágenes
            core.wait(image_interval + np.random.rand() * jitter)

            img_type = images['img_type'].iloc[i]
            image = choice(targets if img_type == 1 else no_targets)
            nImage = nImage + 1
            if img_type == 1:
                nTarget = nTarget + 1
            else:
                nNoTarget = nNoTarget + 1

            image.draw()
            timestamp = local_clock()
            images.at[i, 'timestamp'] = timestamp

            '''
            Si img_type = 1 -> Target -> Out=1
            Si img_type = 0 -> NoTarget -> Out=2
            # El Out implica escritura en csv final por el hilo
            '''
            outlet.push_sample([2 if img_type == 0 else 1], timestamp)
            window.flip()
            # window.update()

            # offset
            core.wait(image_offset)
            # window.flip()
            # if len(event.getKeys()) > 0 or (time() - start) > experiment_time:
            #     break
            if event.getKeys() == 'Esc':
                printError('Cancelando experimento...')
                break
            event.clearEvents()

        core.wait(1.5)
        text3.draw()
        text4.draw()
        window.flip()
        core.wait(5)

        window.close()
        process.join()

        print()
        printSuccess('---------------------------------------------')
        printSuccess("Datos del experimento en: experiments/{}".format(experiment))
        printSuccess('---------------------------------------------')
        printSuccess('Experimento finalizado')
        printSuccess("Número de imágenes mostradas: " + str(nImage))
        printSuccess("Número de imágenes Target mostradas: " + str(nTarget))
        printSuccess("Número de imágenes Non-Target mostradas: " + str(nNoTarget))
        printSuccess('---------------------------------------------')
        print()
        printInfo("DataFrame final: ")
        print()
        print(images)

        core.quit()

    except KeyboardInterrupt:
        printError('Cancelando experimento...')
        window.close()
        core.quit()


if __name__ == '__main__':
    main()
