import os
from glob import glob
import pandas as pd
from mne import create_info, concatenate_raws
from mne.channels import read_custom_montage, make_standard_montage
from mne.io import RawArray
from collections import OrderedDict
import mne

import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
import re
import csv
import sys
from scipy.io import loadmat

sns.set_context('talk')
sns.set_style('white')


def load_mat(filename):
    # Ejemplo de carga de fichero MAT para procesarlo: http://bnci-horizon-2020.eu/database/data-sets
    chnames = ['Fp1',
               'Fp2',
               'F5',
               'AFz',
               'F6',
               'T7',
               'Cz',
               'T8',
               'P7',
               'P3',
               'Pz',
               'P4',
               'P8',
               'O1',
               'Oz',
               'O2',
               'STI 014']
    chtypes = ['eeg'] * 16 + ['stim']

    X = loadmat(filename)['s3']['test']
    info = mne.create_info(ch_names=chnames, sfreq=256,
                           ch_types=chtypes, montage='standard_1020',
                           verbose=False)
    raw = mne.io.RawArray(data=X, info=info, verbose=False)

    return raw


def load_raw(filename, sfreq=256., ch_ind=[0, 1, 2, 3],
             stim_ind=5, replace_ch_names=None):
    '''
        [!] FUNCIÓN de creación del objeto Raw a partir del fichero con los datos del experimento.
    '''
    n_channel = len(ch_ind)
    data = pd.read_csv(filename)

    if "Timestamp" in data.columns:
        del data['Timestamp']
    if "Time" in data.columns:
        del data['Time']

    ch_names = list(data.columns)[0:n_channel] + ['Stim']

    if replace_ch_names is not None:
        ch_names = [c if c not in replace_ch_names.keys()
                    else replace_ch_names[c] for c in ch_names]

    ch_types = ['eeg'] * n_channel + ['stim']
    # montage = read_custom_montage('openbcipos.sfp')
    montage = 'standard_1020'
    data = data.values[:, ch_ind + [stim_ind]].T
    data[:-1] *= 1e-6

    info = create_info(ch_names=ch_names, ch_types=ch_types,
                       sfreq=sfreq)
    raw = RawArray(data=data, info=info)
    raw.set_montage(montage)

    return raw

def create_raw_with_noise(raw_without_noise, gaussian_distribution=None):

    data = raw_without_noise.get_data()

    '''
    Se crean muestras parametrizadas de una distribución normal (gaussiana) para generar ruido en la señal
    '''
    if len(data) == len(gaussian_distribution):
        print("Aplicando ruido en la señal...")
        data = data + gaussian_distribution
    else:
        print("Error en la aplicación de ruido. Estructuras de datos con tamaños distintos.")
        return

    # info = create_info(ch_names=ch_names, ch_types=ch_types,
    #                    sfreq=sfreq)
    raw = RawArray(data=data, info=raw_without_noise.info)
    montage = 'standard_1020'
    raw.set_montage(montage)

    return raw


def convert_openbci(path_dataset):
    '''
    [!] FUNCIÓN para transformar RawData OPENBCI < V5 -> a estructura definida en el TFG
        Se emplea únicamente si queremos procesar un RAW DATA que ha sido capturado con OpenBCI anteriormente (sin sync)
    '''

    # PATHS

    output_path = 'data'

    dataset = os.path.basename(path_dataset)

    output_fn = "converted_" + dataset
    path_output = os.path.join(output_path, output_fn)

    # OpenBCI AJUSTES

    input_sample_rate = 250

    if (os.path.exists(path_output)):
        print("Fichero " + path_output + " ya convertido")
        print("Recuperando fichero...")
        return path_output

    input_headers = ['id', 'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'accel1', 'accel2',
                     'accel3']
    # Modificarlo como convert_new_openbci, para que se encuentre Timestamp
    output_headers = ['Time', 'FP1', 'FP2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'Estimulo']

    if not path_dataset:
        print("ERROR: No se encontró el fichero! \n")
        raw_input()

    print("Procesando fichero: " + dataset + " ... ")

    output_data = []

    time_counter = 0
    time_increment = float(1) / float(input_sample_rate)

    print("Frecuencia de muestreo: " + str(input_sample_rate))
    print("Incremento de tiempo de: " + str(time_increment) + " segundos")

    with open(os.path.join(path_dataset), 'r') as csvfile:

        for i, line in enumerate(csvfile):
            if i == 2:
                sr_line = line
                break

        csv_input = csv.DictReader(csvfile, fieldnames=input_headers, dialect='excel')
        row_count = 0

        for row in csv_input:

            row_count = row_count + 1

            if (row_count > 3):

                output = {}

                time_counter = time_counter + time_increment

                output['Time'] = "{:.3f}".format(time_counter)

                for i in range(1, 9):
                    # channel_key = 'chan' + str(i)
                    channelid = input_headers[i]
                    output[channelid] = row[channelid]

                # Añadimos Estimulo stream para preprocesamiento de la señal
                output['Estimulo'] = 0

                output_data.append(output)

    output_csv_file = open(path_output, 'w')

    csv_output = csv.DictWriter(output_csv_file, fieldnames=output_headers, lineterminator='\n', delimiter=',',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)

    headers_text = {}

    for val in output_headers:
        headers_text[val] = val

    csv_output.writerow(headers_text)

    for row in output_data:
        csv_output.writerow(row)

    print("Ruta del fichero csv convertido: " + path_output)
    return path_output


def convert_new_openbci(path_dataset):
    '''
    [!] FUNCIÓN para transformar RawData OPENBCI V5 -> a estructura definida en el TFG
        Se emplea únicamente si queremos procesar un RAW DATA que ha sido capturado con OpenBCI anteriormente (sin sync)
    '''

    # PATHS

    output_path = 'data'

    dataset = os.path.basename(path_dataset)

    output_fn = "converted_" + dataset
    path_output = os.path.join(output_path, output_fn)

    # OpenBCI AJUSTES

    input_sample_rate = 255

    if (os.path.exists(path_output)):
        print("Fichero " + path_output + " ya convertido")
        print("Recuperando fichero...")
        return path_output

    input_headers = ['id', 'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'accel1', 'accel2',
                     'accel3', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other',
                     'analog1', 'analog2', 'analog3', 'ts', 'ts_formatted']
    output_headers = ['Time', 'Timestamp', 'FP1', 'FP2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'Estimulo']

    if not path_dataset:
        print("ERROR: No se encontró el fichero! \n")
        raw_input()

    print("Procesando fichero: " + dataset + " ... ")

    output_data = []

    time_counter = 0
    time_increment = float(1) / float(input_sample_rate)

    print("Frecuencia de muestreo: " + str(input_sample_rate))
    print("Incremento de tiempo de: " + str(time_increment) + " segundos")

    with open(os.path.join(path_dataset), 'r') as csvfile:

        csv_input = csv.DictReader(csvfile, fieldnames=input_headers, dialect='excel')
        row_count = 0

        for row in csv_input:

            row_count = row_count + 1

            if (row_count > 5):

                output = {}

                time_counter = time_counter + time_increment

                output['Time'] = "{:.3f}".format(time_counter)
                timestamp = float(row['ts'])
                output['Timestamp'] = timestamp

                for i in range(1, 9):
                    channelid = input_headers[i]
                    output[channelid] = row[channelid]

                # Añadimos Estimulo Stream para preprocesamiento de la señal
                output['Estimulo'] = 0

                output_data.append(output)

    output_csv_file = open(path_output, 'w')

    csv_output = csv.DictWriter(output_csv_file, fieldnames=output_headers, lineterminator='\n', delimiter=',',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)

    headers_text = {}

    for val in output_headers:
        headers_text[val] = val

    csv_output.writerow(headers_text)

    for row in output_data:
        csv_output.writerow(row)

    print("Ruta del fichero csv convertido: " + path_output)
    return path_output



def apply_nontarget(name_file):
    '''
    [!] FUNCIÓN EXPERIMENTAL

    Sabiendo 0.004 cada entrada del fichero (con 250Hz en el muestreo):
        Se escribe un 2 (NonTarget) al final de la línea cada 500ms(cada vídeo) / 0.004 = 125 entradas
        A tener en cuenta:
            Inicio del exp (ts capturado)
            Si hay un 1 al final de línea (Target) -> se salta
    '''

    output_path = 'data'

    path = os.path.join(output_path, name_file)

    input_headers = ['Time', 'Timestamp', 'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'Estimulo']

    start_exp = 1594894778.286
    fin_exp = 1594894831.223
    time_image = 0.5
    time_ts = 0.004

    output_data = []

    with open(os.path.join(path), 'r') as csvfile:

        csv_input = csv.DictReader(csvfile, fieldnames=input_headers, dialect='excel')
        row_count = 0

        headers = True
        for row in csv_input:
            output = {}
            if headers:
                headers = False
                continue
            output['Time'] = row['Time']
            output['Timestamp'] = row['Timestamp']
            output['Fp1'] = row['Fp1']
            output['Fp2'] = row['Fp2']
            output['C3'] = row['C3']
            output['C4'] = row['C4']
            output['P7'] = row['P7']
            output['P8'] = row['P8']
            output['O1'] = row['O1']
            output['O2'] = row['O2']
            if float(row['Timestamp']) >= start_exp and float(row['Timestamp']) <= fin_exp:
                print(float(row['Timestamp']))
                row_count = row_count + 1

            if row_count == time_image / time_ts and row['Estimulo'] != 2:
                output['Estimulo'] = '1'
                row_count = 0
            else:
                output['Estimulo'] = row['Estimulo']

            output_data.append(output)

    output_csv_file = open(os.path.join(output_path, 'full_' + name_file), 'w')

    csv_output = csv.DictWriter(output_csv_file, fieldnames=input_headers, lineterminator='\n', delimiter=',',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)

    headers_text = {}

    for val in input_headers:
        headers_text[val] = val

    csv_output.writerow(headers_text)

    for row in output_data:
        csv_output.writerow(row)

    return output_csv_file
