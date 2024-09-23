import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time
import re
import os
import sys
import pynmea2
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.dates import SecondLocator

nameFile = sys.argv[1]  # for example 'test.ubx'
#systemName = sys.argv[2]  # for example 'GPS'
#IDsystem = sys.argv[3]  # for example 'L1'
#print(nameFile, systemName, IDsystem)
nameFile_int, nameFile_ext = os.path.splitext(nameFile)  # name for example test, and extension name for example '.ubx'


def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except FileExistsError:
            print('error folder' + directory)
            pass


create_dir_if_not_exists('Result_SNR')
create_dir_if_not_exists('Result_CSV')



all_sat = {}
all_satElevation = {}
dictGGA = {}
dictRMC = {}
dictTXT = {}
dictIdSystems = {}


inUse_sat = {
    "GPS": [],
    "Glonass": [],
    "BeiDou": [],
    "Galileo": [],
    "SBAS": [],
    "QZSS": [],
    "IRNSS": []
}

PossibleSatInSystem = []
listTimeGGA = []

flags = {
    "GSA": False,
    "RMC": False,
    "GGA": False,
    "GSV": False,
    "TXT": False
}

countGGA = 0
normstring = 0
countErrorChk = 0
countMess = 0
countChk = 0
averageSNR = 0
countSNR1 = 0
numsecEr = 0

SYSTEMS = {
    'GPS': {
        'satellite_system': '$GPGSV',
        'gsa_id_system': '1',
        'gsa_id_signal': {
            '1': 'SIGID_GPS_L1CA',  # L1 1575.42 MHz
            '2': 'SIGID_GPS_L1P',   # L1
            '3': 'SIGID_GPS_L1M',   # L1
            '9': 'SIGID_GPS_L1C',   # L1
            '5': 'SIGID_GPS_L2CM',  # L2 1227.60 MHz
            '6': 'SIGID_GPS_L2CL',  # L2
            '7': 'SIGID_GPS_L5I',   # L5 1176.45 MHz
            '8': 'SIGID_GPS_L5Q',   # L5
            '11': 'SIGID_GPS_L6'    # L6
        },
        'possible_sat_in_system': list(range(1, 33)),
    },
    'Glonass': {
        'satellite_system': '$GLGSV',
        'gsa_id_system': '2',
        'gsa_id_signal': {
            '1': 'SIGID_GLN_G1CA',  # L1 1602.0–1615.5 MHz
            '3': 'SIGID_GLN_G2CA'  # L2 1246.0–1256.5 MHz
        },
        'possible_sat_in_system': list(range(65, 97)) + list(range(1, 29)),
    },
    'BeiDou': {
        'satellite_system': ['$GBGSV', '$BDGSV'],
        'gsa_id_system': '4',
        'gsa_id_signal': {
            '1': 'SIGID_BDS_B1I',   # L1
            '9': 'SIGID_BDS_B1C',    # L1 1575.42 MHz
            '2': 'SIGID_BDS_B2I',   # L2 1268.52 MHz
            'B': 'SIGID_BDS_HZ',    # L2
            '4': 'SIGID_BDS_B2A',   # L5 1176.45 MHz
            '5': 'SIGID_BDS_hz',     # L5
            '3': 'SIGID_BDS_B3I'    # L3
        },
        'possible_sat_in_system': list(range(1, 64)) + list(range(201, 264)),
    },
    'Galileo': {
        'satellite_system': '$GAGSV',
        'gsa_id_system': '3',
        'gsa_id_signal': {
            '6': 'SIGID_GAL_L1A',   # L1 1575.42 MHz
            '7': 'SIGID_GAL_L1BC',   # L1
            '2': 'SIGID_GAL_E5B',   # L2 1278.75 MHz
            '1': 'SIGID_GAL_E5A'    #  L5 1176.45 MHz
        },
        'possible_sat_in_system': list(range(101, 137)) + list(range(1, 37)) + list(range(301, 337)),
    },
    'SBAS': {
        'satellite_system': '$GPGSV',
        'gsa_id_system': '0',
        'gsa_id_signal': {
            '1': 'signal_id_L1',    # L1 1574.42 MHz
            '7': 'signal_id_L2'     # L2
        },
        'possible_sat_in_system': list(range(33, 65)) + list(range(152, 159)),
    },
    'QZSS': {
        'satellite_system': '$GQGSV',
        'gsa_id_system': '5',
        'gsa_id_signal': {
            '1': 'signal_id_L1',     # L1 1574.42 MHz
            '6': 'signal_id_L2'     # L2 1227.6 MHz
        },
        'possible_sat_in_system': list(range(93, 100)) + list(range(193, 198)),
    },
    'IRNSS': {
        'satellite_system': '$GPGSV',
        'gsa_id_system': '6',
        'gsa_id_signal': {
            '1': 'signal_id_L1',     # L1
            '7': 'signal_id_L2'     # L2
        },
        'possible_sat_in_system': list(range(1, 19)),
    }
}

possibleNMEA = ['$GPGGA', '$GPGSA', '$GPGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$BDGSV', '$GBGSV', '$GAGSV', '$GNRMC',
                '$GNGGA', '$GNTXT']
system_mapping = {details['gsa_id_system']: system_name for system_name, details in SYSTEMS.items()}
gsv_mapping = {'$GPGSV':'GPS', '$GLGSV':'Glonass', '$BDGSV':'BeiDou', '$GBGSV':'BeiDou', '$GAGSV':'Galileo'}
# значение elevation, значения ниже этого в рассчете не участует
MinElevation = 10
# значение SNR, значения ниже этого в рассчете не участуют
minSNR = 20

# Проверка входных аргументов. Пример "ally_2J_channel_gnss_126.dat Glonass L2"
'''
def checkSystem(systemName):
    try:
        system = SYSTEMS.get(systemName)
        if IDsystem == 'L1':
            GSA_idSignal = system['gsa_id_signal_L1']
        if IDsystem == 'L2':
            GSA_idSignal = system['gsa_id_signal_L2']
        if IDsystem == 'L5':
            GSA_idSignal = system['gsa_id_signal_L5']

        if not system or IDsystem not in ['L1', 'L2', 'L5']:
            raise KeyError

        satelliteSystem = system['satellite_system']
        GSA_idSystem = system['gsa_id_system']
        inUse_sat_sys = inUse_sat[systemName]
        PossibleSatInSystem = system['possible_sat_in_system']
        signal_keys = [key for key in system.keys() if key.startswith('gsa_id_signal_')]
        for signal_key in signal_keys:
            GSA_idSignal_1 = system[signal_key]
            for signal_id, signal_name in GSA_idSignal_1.items():
                signal_mapping[signal_id] = signal_name
    except KeyError:
        print('Naming error!')
        print('Please choose from among the following:')
        print('GPS, Glonass, BeiDou, Galileo')
        print('L1, L2 or L5')
    return GSA_idSignal, satelliteSystem, GSA_idSystem, inUse_sat_sys, PossibleSatInSystem
'''

# ф-я заполнение словаря all_sat, включающее L1, L2 и др
def SatSnr(system, systemID, snr_dict, lineSat, lineSnr):
    satN = int(newLine[lineSat].strip())
    snrN = newLine[lineSnr].strip()
    if snrN == '':
        value = None
    else:
        value = int(snrN)
    if system not in snr_dict:
        snr_dict[system] = {}
    if systemID not in snr_dict[system]:
        snr_dict[system][systemID] = {}
    if satN not in snr_dict[system][systemID]:
        snr_dict[system][systemID][satN] = {}
    snr_dict[system][systemID][satN][time] = value
    return satN, value


# ф-я заполнение словаря satElevation, включающее L1, L2 и др
def SatElevation(system, systemID, elevation_dict, lineSat, lineElev):
    satN = int(newLine[lineSat].strip())
    elevN = newLine[lineElev].strip()
    if elevN == '':
        value = None
    else:
        value = int(elevN)
    if system not in elevation_dict:
        elevation_dict[system] = {}
    if systemID not in elevation_dict[system]:
        elevation_dict[system][systemID] = {}
    if satN not in elevation_dict[system][systemID]:
        elevation_dict[system][systemID][satN] = {}
    elevation_dict[system][systemID][satN][time] = value
    return satN, value


# функция парсера сообщений GSV вывод SNR с учетом сообщений GSA (только используемые спутники)
def parserGSV_inUse(line_from_file, inuse_sat, flags):
    line_sysID = line_from_file[-3]
    for gsv in gsv_mapping:
        if line_from_file[0] == gsv:
            system = gsv_mapping[gsv]
            if line_sysID in SYSTEMS[system]['gsa_id_signal']:
                systemID = SYSTEMS[system]['gsa_id_signal'][line_sysID]
                satElevation = all_satElevation
                satSnr = all_sat
                if line_from_file[5] != "*" :
                    for i in range(4, 20, 4):
                        if line_from_file.index('*') > i + 3:
                            if len(str(line_from_file[i])) < 3 and int(line_from_file[i]) in inuse_sat[system]:
                                print(line_from_file)
                                SatElevation(system, systemID, satElevation, i, i + 1)
                                SatSnr(system, systemID, satSnr, i, i + 3)
                            else:
                                print(line_from_file)
                                print(int(line_from_file[i]))

    return

'''
# функция парсера сообщений GSV вывод SNR (все видимые спутники)
def parserGSV(line_from_file):
    if line_from_file[-3].isdigit() and line_from_file[-3] in GSA_idSignal:
        satElevation = all_satElevation
        satSnr = all_sat
        if line_from_file[5] != "*":
            for i in range(4, 20, 4):
                if line_from_file.index('*') > i + 3:
                    if line_from_file[i] != '' and len(str(line_from_file[i])) < 3 and int(
                            line_from_file[i]) in PossibleSatInSystem:
                        SatElevation(satElevation, i, i + 1)
                        SatSnr(satSnr, i, i + 3)
    return
'''

def parserRMC(line_from_file, msg):
    time1 = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
    formatted_output1 = time1.strftime('%H:%M:%S.%f')
    velocity = round(1.852 / 3.6 * float(check_argument(msg.spd_over_grnd)), 2)
    dictRMC[formatted_output1] = msg.status, msg.mode_indicator, msg.nav_status, velocity
    return


def parserGGA(line_from_file, msg):
    time = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
    listTimeGGA.append(line_from_file[1])
    formatted_output = time.strftime('%H:%M:%S.%f')
    dictGGA[formatted_output] = float(check_argument(msg.altitude)), float(
        check_argument(msg.age_gps_data)), int(msg.gps_qual)
    return time


def parserGSA(line_from_file):
    for i in system_mapping:
        if int(line_from_file[-3]) == int(i):
            systemName = system_mapping[i]
    for i in range(3, len(line_from_file) - 6):
        if line_from_file[i] != '':
            inUse_sat[systemName].append(int(line_from_file[i]))
    return


def parserTXT(line_from_file, time_from_line):
    check_argument(str(line_from_file))
    dictTXT[time_from_line.strftime('%H:%M:%S.%f')] = line_from_file[1:-2]  # без контрольной суммы и маски сообщения
    return


# функция проверка чексуммы сообщений NMEA
def chksum_nmea(sentence):
    # This is a string, will need to convert it to hex for
    # proper comparsion below
    global countErrorChk, countChk
    normstring = ",".join(sentence)
    if sentence[-2] != '*':
        countErrorChk += 1
        return False

    cksum = sentence[-1]
    if len(cksum) != 3:
        countErrorChk += 1
        return False
    # String slicing: Grabs all the characters
    # between '$' and '*' and nukes any lingering
    # newline or CRLF
    chksumdata = re.sub("(\n|\r\n)", "", normstring[normstring.find("$") + 1:normstring.find("*") - 1])
    # Initializing our first XOR value
    csum = 0

    # For each char in chksumdata, XOR against the previous
    # XOR'd char.  The final XOR of the last char will be our
    # checksum to verify against the checksum we sliced off
    # the NMEA sentence

    for c in chksumdata:
        # XOR'ing value of csum against the next char in line
        # and storing the new XOR value in csum
        csum ^= ord(c)
    try:
        hex(int(cksum.lower(), 16))
    except:
        countErrorChk += 1
        return False

    # Do we have a validated sentence?
    if hex(csum) == hex(int(cksum.lower(), 16)):
        countChk += 1
        return True
    countErrorChk += 1
    return False


# функция вывода данных в список для записи в файл
def average(dataDict):
    list_Average = []
    list_count_Average = []
    list_Sat = []

    for numerOfSat, values in dataDict.items():
        clean_values = [int(v) for v in values.values() if v is not None and v != '']
        if clean_values:
            avg = float(round(sum(clean_values) / len(clean_values), 1))
            list_Average.append(avg)
            list_count_Average.append(len(clean_values))
            list_Sat.append(numerOfSat)

    return list_Average, list_count_Average, list_Sat


def check_argument(arg):
    global numsecEr
    default_value = -1  # или любое другое значение по умолчанию
    if not arg:
        numsecEr += 1
        return default_value
    try:
        return float(arg)
    except ValueError:
        numsecEr += 1
        return default_value


# Base перебор сообщений из файла
with open(nameFile, encoding="CP866") as inf2:
    for line in inf2:
        for prefix in possibleNMEA:
            start_index = line.find(prefix)
            if start_index != -1:
                split_line = line[start_index:].split(',')
                if len(split_line) < 2 or split_line[1] == '':
                    countErrorChk += 1
                    break
                try:
                    asterisk_index = line.find('*')
                    newLine = line[start_index::].replace('*', ',*,').split(',')

                    msg = pynmea2.parse(line[start_index:].strip())
                    if '$GNGGA' in newLine and newLine[1] != '' and chksum_nmea(newLine):
                        flags["GGA"] = True
                        countGGA += 1
                        for i in inUse_sat:
                            inUse_sat[i]= []
                        time = parserGGA(newLine, msg)
                        break
                    elif '$GNGSA' in newLine and countGGA >= 1 and newLine[2] == '3' and chksum_nmea(newLine):
                        idSystem = newLine[-3]
                        if not idSystem in dictIdSystems and len(newLine) > 20:
                            idSystem = newLine[-3]
                            dictIdSystems[idSystem] = [system_mapping[idSystem]]
                        if newLine[-3] in system_mapping:
                            flags["GSA"] = True
                            parserGSA(newLine)
                            break
                    elif newLine[0] in gsv_mapping and countGGA >= 1 and chksum_nmea(newLine):
                        idSignal = newLine[-3]
                        if flags["GSA"]:
                            parserGSV_inUse(newLine, inUse_sat, flags)
                        else:
                            flags["GSV"] = True
                            parserGSV(newLine)
                        break
                    elif '$GNRMC' in newLine and countGGA >= 1 and len(newLine) > 4:
                        flags["RMC"] = True
                        parserRMC(newLine, msg)
                        break
                    elif '$GNTXT' in newLine and countGGA >= 1:
                        flags["TXT"] = True
                        parserTXT(newLine, time)

                except pynmea2.ParseError:
                    countErrorChk += 1
                    continue

if flags["GGA"]:
    # подсчет времени по сообщениям GGA
    last = datetime.strptime(listTimeGGA[-1], '%H''%M''%S.%f')
    first = datetime.strptime(listTimeGGA[0], '%H''%M''%S.%f')
    time_of_flight: int = int((last - first).total_seconds())
    # print('DifTime from first and last GGA:', end=' ')
    # print(time_of_flight, 'sec')
    file_name = os.path.join('Result_CSV', f'{nameFile_int}_GGA.csv')
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write("GPS_Time,Altitude,rtkAGE,Status\n")
        for time, values in dictGGA.items():
            line = f"{time},{values[0]},{values[1]},{values[2]}\n"
            file.write(line)

if flags["RMC"]:
    file_name = os.path.join('Result_CSV', f'{nameFile_int}_RMC.csv')
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write("GPS_Time,status,mode_indicator,nav_status,Speed\n")
        for time, values in dictRMC.items():
            line = f"{time},{values[0]},{values[1]},{values[2]},{values[3]}\n"
            file.write(line)

if flags["TXT"]:
    file_name = os.path.join('Result_CSV', f'{nameFile_int}_TXT.csv')
    max_len = max(len(values) for values in dictTXT.values())
    with open(file_name, 'w', encoding='utf-8') as file:
        header = "GPS_Time," + ",".join([f"Value_{i + 1}" for i in range(max_len)]) + "\n"
        file.write(header)
        for time, values in dictTXT.items():
            values_str = ",".join(map(str, values + [None] * (max_len - len(values))))  # Заполнение недостающих значений
            line = f"{time},{values_str}\n"
            file.write(line)

    #df3 = pd.DataFrame(list(dictTXT.items()), columns=["GPS_Time", "Values"])
    #values_df = pd.DataFrame(df3['Values'].tolist())
    #df3.drop(columns=['Values'], inplace=True)
    #df3 = df3.join(values_df)
    #df3.to_csv(f'Result_CSV/{nameFile_int}_TXT.csv', index=False, escapechar="\\")

if flags["GSA"] or flags["GSV"]:
    for sysName in all_sat:
        for sysID in all_sat[sysName]:
            p = average(all_sat[sysName][sysID])
            m = average(all_satElevation[sysName][sysID])
    for i in range(len(p[0])):
        if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > minSNR:
            averageSNR += p[0][i]
            countSNR1 += 1
        else:
            continue
    print('average SNR: ', end='')
    if countSNR1 != 0:
        print(round((averageSNR / countSNR1), 1))
        print('number of sat average SNR: ', end='')
        print(countSNR1)
    print()
    Average = 0
    schet = 0
    gh = 0
    if countSNR1 == 0 and averageSNR == 0:
    # дозапись осреденных в файл test.txt - для скрипта
        with open('Result_SNR/test.txt', 'a') as f1:
            f1.write(nameFile_int)
            f1.write('_')
            #f1.write(systemName)
            f1.write('_')
            #f1.write(IDsystem)
            f1.write(' ')
            #f1.write(str(round((averageSNR / countSNR1), 1)))
            f1.write(' ')
            f1.write(str(gh))
            f1.write(' ')
            f1.write(str(countGGA))  # number of GGA messages
            f1.write(' ')
            f1.write(str(countErrorChk))  # ErrMes
            f1.write(' ')
            f1.write(str(round((last - first).total_seconds())))  # DifTime from first and last GGA
            f1.write('\n')

        df3 = pd.DataFrame(all_sat['GPS']['SIGID_GPS_L1CA'])
        #df3 = df3.fillna(0).astype(int)
        df3.index = df3.index.to_series().apply(lambda x: x.to_pydatetime().time())
        df3.to_csv('Result_CSV/' + nameFile_int + '_' + 'systemName' + '_' + 'IDsystem' + '_SNR.csv', index=True)

        # вывод графика и сохранение в jpeg
        result = all_sat['GPS']['SIGID_GPS_L1CA'].values()
        # вывод и сохранение графика в формате jpeg
        fig, ax = plt.subplots(figsize=(12, 8))

        for k in result:
            k = {key: value for (key, value) in k.items() if value}
            myList = sorted(k.items())
            if myList:
                x, y = zip(*myList)
                ax.plot(x, y, marker='o', markersize=2)
        print()
        interval_time_of_flight = time_of_flight // 8
        # Formatter для отображения времени
        time_format = mdates.DateFormatter('%H:%M:%S')
        # Locator для определения интервала
        locator = SecondLocator(interval=interval_time_of_flight)
        #ax.xaxis.set_major_locator(locator)  # Задаем интервал
        ax.xaxis.set_major_formatter(time_format)

        ax.set_xlabel('Time', fontsize=14)
        ax.set_ylabel('SNR, dBHz', fontsize=14)
        ax.text(0.01, 0.98, 'average SNR:', fontsize=14, transform=ax.transAxes, verticalalignment='top')
        #ax.text(0.01, 0.94, f'{round((averageSNR / countSNR1), 1)} dBHz', fontsize=14, transform=ax.transAxes,
         #       verticalalignment='top')
        ax.set_title(nameFile + ", " + 'systemName' + '_' + 'IDsystem', fontsize=14)
        ax.set_ylim(10, 60)
        ax.grid(color='black', linestyle='--', linewidth=0.2)
        ax.legend([], [], loc="upper left", frameon=False)
        ax.legend(all_sat.keys(), loc='upper right')

        nameFileSaved = nameFile_int + '_' + 'systemName' + '_' + 'IDsystem' + '.png'
        plt.savefig('Result_SNR/' + nameFileSaved, dpi=100)
        #print('systems in log:')
        #print(dictIdSystems)
        #print('signal in system:', systemName)
        #print(dictIdSignal)
        plt.show()
        plt.close()
    else:
        print('No Valid data. Pls check system, MinElevation and minSNR')
