import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time
import re
import os
import sys
import matplotlib.dates as mdates
from matplotlib.dates import SecondLocator
import logging
from typing import Dict, List, Tuple, Optional, Any, Set

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NMEAParser:
    """Класс для парсинга NMEA сообщений"""

    def __init__(self, name_file: str, system_gsv: Optional[str] = None):
        self.name_file = name_file
        self.name_file_int, self.name_file_ext = os.path.splitext(name_file)
        self.system_gsv = system_gsv

        # Инициализация структур данных
        self.all_sat_snr: Dict = {}
        self.not_inuse_sat_snr: Dict = {}
        self.all_sat_elevation: Dict = {}
        self.not_inuse_sat_elevation: Dict = {}
        self.dict_gga: Dict = {}
        self.dict_rmc: Dict = {}
        self.dict_txt: Dict = {}
        self.dict_id_systems: Dict = {}

        self.in_use_sat = {
            "GPS": [],
            "Glonass": [],
            "BeiDou": [],
            "Galileo": [],
            "SBAS": [],
            "QZSS": [],
            "IRNSS": []
        }

        self.list_time_gga: List = []

        self.flags = {
            "GSA": False,
            "RMC": False,
            "GGA": False,
            "GSV": False,
            "TXT": False,
            "HD9311": False
        }

        if system_gsv == "GSV":
            self.flags["GSV"] = True

        # Счетчики
        self.count_gga = 0
        self.normstring = 0
        self.count_error_chk = 0
        self.count_mess = 0
        self.count_chk = 0
        self.average_snr = 0
        self.count_snr1 = 0
        self.numsec_er = 0
        self.values = 'noTXT'

        self.prev_gga_time = None
        self.gap_threshold = 3

        # Константы
        self.SYSTEMS = {
            'GPS': {
                'satellite_system': '$GPGSV',
                'gsa_id_system': '1',
                'gsa_id_signal': {
                    '1': 'L1CA_L1',
                    '2': 'L1P_L1',
                    '3': 'L1M_L1',
                    '9': 'L1C_L1',
                    '5': 'L2CM_L2',
                    '6': 'L2CL_L2',
                    '7': 'L5I_L5',
                    '8': 'L5Q_L5',
                    '11': 'L6_L6',
                    'GPS': 'L1'
                },
                'possible_sat_in_system': list(range(1, 33)),
            },
            'Glonass': {
                'satellite_system': '$GLGSV',
                'gsa_id_system': '2',
                'gsa_id_signal': {
                    '1': 'G1CA_L1',
                    '3': 'G2CA_L2',
                    'Glonass': 'L1'
                },
                'possible_sat_in_system': list(range(65, 97)) + list(range(1, 29)),
            },
            'BeiDou': {
                'satellite_system': ['$GBGSV', '$BDGSV'],
                'gsa_id_system': '4',
                'gsa_id_signal': {
                    '1': 'B1I_L1',
                    '9': 'B1C_L1',
                    '2': 'B2I_L2',
                    'B': 'L2',
                    '4': 'B2A_L5',
                    '5': 'L5',
                    '3': 'B3I_L3',
                    'BeiDou': 'L1'
                },
                'possible_sat_in_system': list(range(1, 64)) + list(range(201, 264)),
            },
            'Galileo': {
                'satellite_system': '$GAGSV',
                'gsa_id_system': '3',
                'gsa_id_signal': {
                    '6': 'L1A_L1',
                    '7': 'L1BC_L1',
                    '2': 'E5B_L2',
                    '1': 'E5A_L2',
                    'Galileo': 'L1'
                },
                'possible_sat_in_system': list(range(101, 137)) + list(range(1, 37)) + list(range(301, 337)),
            },
            'SBAS': {
                'satellite_system': '$GPGSV',
                'gsa_id_system': '0',
                'gsa_id_signal': {
                    '1': 'id_L1',
                    '7': 'id_L2'
                },
                'possible_sat_in_system': list(range(33, 65)) + list(range(152, 159)),
            },
            'QZSS': {
                'satellite_system': '$GQGSV',
                'gsa_id_system': '5',
                'gsa_id_signal': {
                    '1': 'id_L1',
                    '6': 'id_L2'
                },
                'possible_sat_in_system': list(range(0, 100)) + list(range(193, 198)),
            },
            'IRNSS': {
                'satellite_system': '$GPGSV',
                'gsa_id_system': '6',
                'gsa_id_signal': {
                    '1': 'id_L1',
                    '7': 'id_L2'
                },
                'possible_sat_in_system': list(range(1, 19)),
            }
        }

        self.min_elevation = 10
        self.min_snr = 15

        self.system_mapping = {details['gsa_id_system']: system_name for system_name, details in self.SYSTEMS.items()}
        self.gsv_mapping = {'$GPGSV': 'GPS', '$GLGSV': 'Glonass', '$BDGSV': 'BeiDou', '$GBGSV': 'BeiDou',
                            '$GAGSV': 'Galileo'}
        self.possible_nmea = ['$GPGGA', '$GPGSA', '$GPGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$BDGSV', '$GBGSV', '$GAGSV',
                              '$GNRMC',
                              '$GNGGA', '$GNTXT', '$PHDANT']


        # Создание необходимых директорий
        self._create_directories()

        # Очистка файла проблем
        txt_file_path = os.path.join('problemAlly', f'{self.name_file_int}_problems.txt')
        if os.path.exists(txt_file_path):
            os.remove(txt_file_path)

    def _create_directories(self):
        """Создание необходимых директорий"""
        directories = ['Result_SNR', 'Result_CSV', 'problemAlly']
        for directory in directories:
            self.create_dir_if_not_exists(directory)

    @staticmethod
    def create_dir_if_not_exists(directory: str):
        """Создание директории если она не существует"""
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except FileExistsError:
                logger.error(f'Error creating folder: {directory}')

    def sat_snr(self, system: str, system_id: str, snr_dict: Dict, line_sat: int, line_snr: int, time_val: datetime) -> \
    Tuple[int, Optional[int]]:
        """Заполнение словаря SNR"""
        sat_n = int(self.new_line[line_sat].strip())
        snr_n = self.new_line[line_snr].strip()

        if snr_n == '' or int(snr_n) <= self.min_snr:
            value = None
        else:
            value = int(snr_n)

        if system not in snr_dict:
            snr_dict[system] = {}
        if system_id not in snr_dict[system]:
            snr_dict[system][system_id] = {}
        if sat_n not in snr_dict[system][system_id]:
            snr_dict[system][system_id][sat_n] = {}

        snr_dict[system][system_id][sat_n][time_val] = value
        return sat_n, value

    def sat_elevation(self, system: str, system_id: str, elevation_dict: Dict, line_sat: int, line_elev: int,
                      time_val: datetime) -> Tuple[int, Optional[int]]:
        """Заполнение словаря elevation"""
        sat_n = int(self.new_line[line_sat].strip())
        elev_n = self.new_line[line_elev].strip()

        if elev_n == '' or int(elev_n) <= self.min_elevation:
            value = None
        else:
            value = int(elev_n)

        if system not in elevation_dict:
            elevation_dict[system] = {}
        if system_id not in elevation_dict[system]:
            elevation_dict[system][system_id] = {}
        if sat_n not in elevation_dict[system][system_id]:
            elevation_dict[system][system_id][sat_n] = {}

        elevation_dict[system][system_id][sat_n][time_val] = value
        return sat_n, value

    def parser_gsv_in_use(self, line_from_file: List[str], inuse_sat: Dict, all_sat_snr: Dict, not_inuse_sat_snr: Dict,
                          time_val: datetime):
        """Парсер сообщений GSV"""
        for gsv in self.gsv_mapping:
            if line_from_file[0] == gsv:
                system = self.gsv_mapping[gsv]
                if len(self.new_line) % 2 != 0:
                    line_sys_id = line_from_file[-3]
                else:
                    line_sys_id = system

                if line_sys_id in self.SYSTEMS[system]['gsa_id_signal']:
                    system_id = self.SYSTEMS[system]['gsa_id_signal'][line_sys_id]
                    if line_from_file[5] != "*":
                        for i in range(4, 20, 4):
                            if line_from_file.index('*') > i + 3 and len(str(line_from_file[i])) < 3:
                                sat_number = int(line_from_file[i]) if line_from_file[i] else None
                                if sat_number:
                                    if sat_number in inuse_sat.get(system, []):
                                        self.sat_snr(system, system_id, all_sat_snr, i, i + 3, time_val)
                                        self.sat_elevation(system, system_id, self.all_sat_elevation, i, i + 1,
                                                           time_val)
                                    else:
                                        self.sat_snr(system, system_id, not_inuse_sat_snr, i, i + 3, time_val)
                                        self.sat_elevation(system, system_id, self.not_inuse_sat_elevation, i, i + 1,
                                                           time_val)
                                else:
                                    self.count_error_chk += 1

    def parser_rmc(self, line_from_file: List[str]):
        """Парсер сообщений RMC"""
        time1 = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
        formatted_output1 = time1.strftime('%H:%M:%S.%f')
        velocity = round(1.852 / 3.6 * float(self.check_argument(line_from_file[7])), 2)
        self.dict_rmc[formatted_output1] = (line_from_file[2], line_from_file[-4], line_from_file[-3], velocity)

    def parser_gga(self, line_from_file: List[str]) -> datetime:
        """Парсер сообщений GGA"""
        time_val = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
        self.list_time_gga.append(line_from_file[1])
        formatted_output = time_val.strftime('%H:%M:%S.%f')
        self.dict_gga[formatted_output] = (
            float(self.check_argument(line_from_file[-8])),
            float(self.check_argument(line_from_file[-4])),
            int(line_from_file[6]),
            float(self.check_argument(line_from_file[-9]))
        )
        return time_val

    def parser_gsa(self, line_from_file: List[str]):
        """Парсер сообщений GSA"""
        system_name = None
        for i in self.system_mapping:
            if int(line_from_file[-3]) == int(i):
                system_name = self.system_mapping[i]

        if system_name:
            for i in range(3, len(line_from_file) - 6):
                if line_from_file[i] != '':
                    self.in_use_sat[system_name].append(int(line_from_file[i]))

    def parser_txt(self, line_from_file: List[str], time_from_line: datetime):
        """Парсер сообщений TXT"""
        self.check_argument(str(line_from_file))
        self.dict_txt[time_from_line.strftime('%H:%M:%S.%f')] = line_from_file[1:-2]

    def chksum_nmea(self, sentence: List[str]) -> bool:
        """Проверка контрольной суммы NMEA"""
        normstring = ",".join(sentence)
        if sentence[-2] != '*':
            self.count_error_chk += 1
            return False

        cksum = sentence[-1]
        if len(cksum) != 3:
            self.count_error_chk += 1
            return False

        chksumdata = re.sub("(\n|\r\n)", "", normstring[normstring.find("$") + 1:normstring.find("*") - 1])
        csum = 0

        for c in chksumdata:
            csum ^= ord(c)

        try:
            hex(int(cksum.lower(), 16))
        except:
            self.count_error_chk += 1
            return False

        if hex(csum) == hex(int(cksum.lower(), 16)):
            self.count_chk += 1
            return True

        self.count_error_chk += 1
        return False

    @staticmethod
    def average(data_dict: Dict) -> Tuple[List[float], List[int], List[int]]:
        """Расчет средних значений"""
        list_average = []
        list_count_average = []
        list_sat = []

        for number_of_sat, values in data_dict.items():
            clean_values = [int(v) for v in values.values() if v is not None and v != '']
            if clean_values:
                avg = float(round(sum(clean_values) / len(clean_values), 1))
                list_average.append(avg)
                list_count_average.append(len(clean_values))
                list_sat.append(number_of_sat)

        return list_average, list_count_average, list_sat

    def check_argument(self, arg: str) -> float:
        """Проверка аргумента"""
        default_value = -1
        if not arg:
            self.numsec_er += 1
            return default_value
        try:
            return float(arg)
        except ValueError:
            self.numsec_er += 1
            return default_value

    def print_alert(self, message: str):
        """Вывод предупреждения"""
        border = '*' * (len(message) + 4)
        print(f"\n{border}")
        print(f"* {message} *")
        print(f"{border}\n")

    def log_problem_message(self, problem_type: str, timestamp: str, message: str):
        """Логирование проблемных сообщений"""
        self.create_dir_if_not_exists('problemAlly')
        log_file = f'problemAlly/{self.name_file_int}_problems.txt'
        with open(log_file, 'a', encoding='utf-8') as problem_log:
            problem_log.write(f"[{problem_type}] {timestamp}\n")
            problem_log.write(f"{message}\n\n")

    def parse_file(self):
        """Основной метод парсинга файла"""
        with open(self.name_file, encoding="CP866") as inf2:
            for line in inf2:
                if ('HD9311' in line) or ('3.018.d861dfe1' in line):
                    self.flags["HD9311"] = True

                nmea_count = line.count('$')
                if nmea_count >= 2:
                    second_dollar = line.find('$', line.find('$') + 1)
                    if second_dollar != -1:
                        line = line[second_dollar:]

                for prefix in self.possible_nmea:
                    start_index = line.find(prefix)
                    if start_index != -1:
                        split_line = line[start_index:].split(',')
                        if len(split_line) < 2 or split_line[1] == '':
                            self.count_error_chk += 1
                            break

                        try:
                            self.new_line = line[start_index::].replace('*', ',*,').split(',')
                            if '*' not in self.new_line:
                                self.count_error_chk += 1
                                break

                            if not self.chksum_nmea(self.new_line):
                                break

                            if ('$GNGGA' in self.new_line or '$GPGGA' in self.new_line) and (
                                    self.new_line[6] == '' or self.new_line[6] == '0'):
                                time_val = datetime.strptime(str(split_line[1].strip()), '%H''%M''%S.%f') + timedelta(
                                    seconds=18)
                                self.log_problem_message('GGA_Empty', time_val.strftime('%H:%M:%S.%f')[:-5],
                                                         str(self.new_line))
                                break

                            elif ('$GNGGA' in self.new_line or '$GPGGA' in self.new_line) and self.new_line[1] != '':
                                self.flags["GGA"] = True
                                self.count_gga += 1

                                for i in self.in_use_sat:
                                    self.in_use_sat[i] = []

                                if len(self.new_line) == 17:
                                    time_val = self.parser_gga(self.new_line)

                                    if self.flags["HD9311"]:
                                        self.log_problem_message('HD9311', time_val.strftime('%H:%M:%S.%f')[:-5],
                                                                 'REBOOT, message ver HD9311')
                                        print(time_val.strftime('%H:%M:%S.%f')[:-5], 'REBOOT, message ver HD9311')
                                        self.flags["HD9311"] = False

                                    if self.prev_gga_time is not None:
                                        time_diff = (time_val - self.prev_gga_time).total_seconds()
                                        if time_diff > self.gap_threshold:
                                            self.log_problem_message('Time_GGA>3',
                                                                     time_val.strftime('%H:%M:%S.%f')[:-5],
                                                                     str(time_diff))
                                            print('Time_GGA>3', time_val.strftime('%H:%M:%S.%f')[:-5], time_diff, 'sec')

                                    self.prev_gga_time = time_val
                                else:
                                    self.count_error_chk += 1
                                    break

                            elif '$GNGSA' in self.new_line:
                                self.flags["GSA"] = True
                                self.flags["GSV"] = False

                                if 22 > len(self.new_line) > 19 and self.count_gga >= 1:
                                    if self.new_line[2] == '3':
                                        if len(self.new_line) == 21:
                                            id_system = self.new_line[-3]
                                        elif len(self.new_line) == 20:
                                            id_system = 'L1'

                                        if not id_system in self.dict_id_systems and len(self.new_line) > 20:
                                            id_system = self.new_line[-3]
                                            self.dict_id_systems[id_system] = [self.system_mapping[id_system]]

                                        if id_system in self.system_mapping:
                                            self.parser_gsa(self.new_line)
                                            break
                                elif len(self.new_line) == 20 and self.count_gga >= 1:
                                    if self.new_line[2] == '3':
                                        id_system = 'L1'
                                    else:
                                        self.log_problem_message('GSA_Empty', time_val.strftime('%H:%M:%S.%f')[:-5],
                                                                 line[start_index:-1])
                                        break
                                else:
                                    self.count_error_chk += 1
                                    break

                            elif self.new_line[0] in self.gsv_mapping and self.count_gga >= 1:
                                if self.system_gsv:
                                    for i in self.in_use_sat:
                                        self.in_use_sat[i] = []
                                    self.parser_gsv_in_use(self.new_line, self.in_use_sat, self.all_sat_snr,
                                                           self.not_inuse_sat_snr, time_val)
                                else:
                                    if self.flags["GSA"]:
                                        self.parser_gsv_in_use(self.new_line, self.in_use_sat, self.all_sat_snr,
                                                               self.not_inuse_sat_snr, time_val)
                                    else:
                                        self.flags["GSV"] = True
                                        self.parser_gsv_in_use(self.new_line, self.in_use_sat, self.all_sat_snr,
                                                               self.not_inuse_sat_snr, time_val)
                                break

                            elif '$GNRMC' in self.new_line and self.count_gga >= 1 and len(self.new_line) > 4:
                                self.flags["RMC"] = True
                                self.parser_rmc(self.new_line)
                                break

                            elif (('$GNTXT' in self.new_line) or ('$PHDANT' in self.new_line)) and self.count_gga >= 1:
                                self.flags["TXT"] = True
                                if 'ALLYSTAR' in self.new_line:
                                    self.log_problem_message('ALLYSTAR', time_val.strftime('%H:%M:%S.%f')[:-5],
                                                             str(self.new_line))
                                    print(time_val.strftime('%H:%M:%S.%f')[:-5])
                                    print(self.new_line)
                                self.parser_txt(self.new_line, time_val)

                        except Exception as e:
                            self.count_error_chk += 1
                            logger.error(f"Error parsing line: {e}")
                            continue

    def process_results(self):
        """Обработка результатов парсинга"""
        if self.flags["GGA"]:
            last = datetime.strptime(self.list_time_gga[-1], '%H''%M''%S.%f')
            first = datetime.strptime(self.list_time_gga[0], '%H''%M''%S.%f')
            time_of_flight = int((last - first).total_seconds())

            file_name = os.path.join('Result_CSV', f'{self.name_file_int}_GGA.csv')
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write("GPS_Time,Altitude,rtkAGE,Status,HDOP\n")
                for time_val, values in self.dict_gga.items():
                    line = f"{time_val},{values[0]},{values[1]},{values[2]},{values[3]}\n"
                    file.write(line)

        if self.flags["RMC"]:
            file_name = os.path.join('Result_CSV', f'{self.name_file_int}_RMC.csv')
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write("GPS_Time,status,mode_indicator,nav_status,Speed\n")
                for time_val, values in self.dict_rmc.items():
                    line = f"{time_val},{values[0]},{values[1]},{values[2]},{values[3]}\n"
                    file.write(line)

        if self.flags["TXT"]:
            file_name = os.path.join('Result_CSV', f'{self.name_file_int}_TXT.csv')
            max_len = max(len(values) for values in self.dict_txt.values())
            with open(file_name, 'w', encoding='utf-8') as file:
                header = "GPS_Time," + ",".join([f"{i + 1}" for i in range(max_len)]) + "\n"
                file.write(header)
                for time_val, values in self.dict_txt.items():
                    values_str = ",".join(map(str, values + [None] * (max_len - len(values))))
                    line = f"{time_val},{values_str}\n"
                    file.write(line)

        logger.info(f'Errors: {self.count_error_chk}')

        if self.flags["GSV"] or self.system_gsv == 'GSV':
            self.print_alert("NOT GSA MESSAGE!!!!")
            self.all_sat_snr = self.not_inuse_sat_snr
            self.all_sat_elevation = self.not_inuse_sat_elevation

        if self.flags["GSA"] or self.flags["GSV"]:
            last = datetime.strptime(self.list_time_gga[-1], '%H''%M''%S.%f')
            first = datetime.strptime(self.list_time_gga[0], '%H''%M''%S.%f')

            for sys_name in self.all_sat_snr:
                for sys_id in self.all_sat_snr[sys_name]:
                    average_snr = 0
                    count_snr1 = 0
                    p = self.average(self.all_sat_snr[sys_name][sys_id])
                    m = self.average(self.all_sat_elevation[sys_name][sys_id])

                    for i in range(len(p[0])):
                        if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > self.min_snr:
                            average_snr += p[0][i]
                            count_snr1 += 1

                    if count_snr1 != 0 and average_snr != 0:
                        avg_snr = round((average_snr / count_snr1), 1)
                        print(f"{sys_name} {sys_id}")
                        print(f"average SNR: {avg_snr}")
                        print(f"number of sat average SNR: {count_snr1}\n")

                        file_name = f'Result_SNR/{sys_name}_{sys_id}.txt'
                        with open(file_name, 'a') as f1:
                            f1.write(f"{self.name_file_int}_{sys_name}_{sys_id} "
                                     f"{avg_snr} "
                                     f"{count_snr1} "
                                     f"{self.count_gga} "
                                     f"{round((last - first).total_seconds())} "
                                     f"{self.count_error_chk} "
                                     f"{self.values}\n")

                    # Сохранение данных в CSV
                    csv_filename = f'Result_CSV/{self.name_file_int}_{sys_name}_{sys_id}_SNR.csv'
                    with open(csv_filename, 'w', encoding='utf-8') as file:
                        sat_numbers = sorted(self.all_sat_snr[sys_name][sys_id].keys())
                        headers = "GPS_Time," + ",".join(map(str, sat_numbers)) + "\n"
                        file.write(headers)

                        all_times = set()
                        for time_data in self.all_sat_snr[sys_name][sys_id].values():
                            all_times.update(time_data.keys())

                        for time_val in sorted(all_times):
                            time_str = time_val.strftime("%H:%M:%S")
                            values_str = ",".join(
                                str(self.all_sat_snr[sys_name][sys_id][sat_n].get(time_val, '')) for sat_n in
                                sat_numbers
                            )
                            line = f"{time_str},{values_str}\n"
                            file.write(line)

                    # Построение графиков
                    self._create_plot(sys_name, sys_id, last, first)

    def _create_plot(self, sys_name: str, sys_id: str, last: datetime, first: datetime):
        """Создание графиков"""
        fig, ax = plt.subplots(figsize=(12, 8))
        result = self.all_sat_snr[sys_name][sys_id].values()

        for k in result:
            k = {key: value for (key, value) in k.items() if value}
            if k:
                times, snrs = zip(*sorted(k.items()))
                ax.plot(times, snrs, marker='o', markersize=2, linewidth=0.5)

        time_of_flight = int((last - first).total_seconds())
        interval_time_of_flight = time_of_flight // 8
        time_format = mdates.DateFormatter('%H:%M:%S')
        locator = SecondLocator(interval=interval_time_of_flight)
        ax.xaxis.set_major_formatter(time_format)

        ax.set_xlabel('Time', fontsize=14)
        ax.set_ylabel('SNR, dBHz', fontsize=14)
        ax.text(0.01, 0.98, 'average SNR: ', fontsize=14, transform=ax.transAxes, verticalalignment='top')

        if self.flags["GSV"]:
            ax.text(0.01, 0.9, 'ONLY GSV!', fontsize=14, transform=ax.transAxes, verticalalignment='top')

        p = self.average(self.all_sat_snr[sys_name][sys_id])

        # Исправленные строки с генераторами
        count_snr1 = sum(1 for i in range(len(p[0]))
                         if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > self.min_snr)

        average_snr = sum(p[0][i] for i in range(len(p[0]))
                          if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > self.min_snr)

        if count_snr1 != 0:
            ax.text(0.01, 0.94, f'{round((average_snr / count_snr1), 1)} dBHz', fontsize=14, transform=ax.transAxes,
                    verticalalignment='top')
            ax.text(0.2, 0.98, f'calcSNR>{self.min_snr} dBHz', fontsize=14, transform=ax.transAxes,
                    verticalalignment='top')
            ax.text(0.2, 0.94, f'calcELEV>{self.min_elevation}°', fontsize=14, transform=ax.transAxes,
                    verticalalignment='top')

        ax.set_title(f"{self.name_file_int}, {sys_name}_{sys_id}", fontsize=14)
        ax.set_ylim(10, 60)
        ax.grid(color='black', linestyle='--', linewidth=0.2)
        ax.legend(self.all_sat_snr[sys_name][sys_id].keys(), loc='upper right')

        jpeg_filename = f'Result_SNR/{self.name_file_int}_{sys_name}_{sys_id}.png'
        plt.savefig(jpeg_filename, dpi=200)
        plt.close()


def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Usage: python NMEA.py <filename> [GSV]")
        sys.exit(1)

    name_file = sys.argv[1]
    system_gsv = sys.argv[2] if len(sys.argv) > 2 else None

    parser = NMEAParser(name_file, system_gsv)
    parser.parse_file()
    parser.process_results()


if __name__ == "__main__":
    main()