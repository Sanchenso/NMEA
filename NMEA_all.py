import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import csv
import subprocess
import numpy as np

processes = []
files = os.listdir()
path = "Result_CSV"

for i in files:
    if i[-4:] in ('.dat', '.ubx', '.log') or i[-5:] == '.cyno':
        print(i)
        subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'GSV', shell=True)
        #subprocess.call("python3 " + 'NMEA.py ' + i, shell=True)
# Wait for all processes to complete
for process in processes:
    process.wait()


path = "Result_CSV"
files_in_path = os.listdir(path)
format_date_time = "%H:%M:%S.%f"

def parse_time(time_str):
    """Парсит время из строки в объект datetime"""
    if not time_str or not isinstance(time_str, str):
        return None

    # Убираем лишние пробелы и кавычки
    time_str = time_str.strip().strip('"').strip("'")

    time_formats = [
        '%H:%M:%S',
        '%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S.%f'
    ]

    for fmt in time_formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    print(f"Не удалось преобразовать: {time_str}")
    return None


def read_snr_csv(file_path):
    """Читает CSV файл с SNR данными и возвращает структурированные данные"""
    times = []
    data = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Читаем заголовки

            # Создаем структуру для хранения данных по спутникам
            for header in headers[1:]:  # Пропускаем первый столбец (время)
                data[header] = []

            # Читаем данные построчно
            for row in reader:
                if not row or len(row) < 2:
                    continue

                # Парсим время
                time_obj = parse_time(row[0])
                if time_obj is None:
                    continue

                times.append(time_obj)

                # Заполняем данные по спутникам
                for i, value in enumerate(row[1:]):
                    if i < len(headers) - 1:  # Убедимся, что не выходим за границы
                        try:
                            data[headers[i + 1]].append(float(value) if value else None)
                        except ValueError:
                            data[headers[i + 1]].append(None)

    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")

    return times, data


def plot_snr(ax, times, data, title, min_time, max_time):
    """Рисует график SNR на указанных осях"""
    ax.set_title(title, fontsize=10)

    # Рисуем данные для каждого спутника
    legend_handles = []
    for sat_id, values in data.items():
        # Фильтруем данные: убираем None значения
        valid_times = []
        valid_values = []

        for t, v in zip(times, values):
            if v is not None:
                valid_times.append(t)
                valid_values.append(v)

        if valid_times:
            line, = ax.plot(valid_times, valid_values, linewidth=0.5, marker='o', markersize=2)
            legend_handles.append((line, sat_id))

    # Добавляем легенду только если есть данные
    if legend_handles:
        lines, labels = zip(*legend_handles)
        ax.legend(lines, labels, fontsize=6, loc='upper right')

    # Рассчитываем среднее SNR
    all_values = []
    for values in data.values():
        all_values.extend([v for v in values if v is not None])

    if all_values:
        avg_snr = round(sum(all_values) / len(all_values), 1)
        ax.text(0.05, 0.9, 'average:', fontsize=8, transform=ax.transAxes, verticalalignment='top')
        ax.text(0.16, 0.9, f'{avg_snr} dBHz', fontsize=8, transform=ax.transAxes, verticalalignment='top')

    # Настраиваем оси
    ax.set_ylim(10, 60)
    ax.set_xlim(min_time, max_time)
    ax.set_xlabel('Time', fontsize=8)
    ax.tick_params(axis='x', which='major', labelsize=8)
    ax.tick_params(axis='y', which='major', labelsize=8)
    ax.set_ylabel('SNR, dBHz', fontsize=8)
    ax.grid(color='black', linestyle='--', linewidth=0.2)

    # Форматирование времени на оси X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))


def create_combined_plots(nameFile_int):
    """Создает объединенные графики SNR для всех систем и сигналов"""
    path = "Result_CSV"

    # Определяем конфигурацию графиков: (приоритет, заголовок)
    plot_config = {
        'GPS_L1CA_L1': (0, 'SNR GPS L1'),
        'GPS_L1': (0, 'SNR GPS L1'),
        'GPS_L2CM_L2': (1, 'SNR GPS L2'),
        'GPS_L2CL_L2': (1, 'SNR GPS L2'),
        'GPS_L5Q_L5': (1, 'SNR GPS L5'),
        'Glonass_G1CA_L1': (2, 'SNR Glonass L1'),
        'Glonass_L1': (2, 'SNR Glonass L1'),
        'Glonass_G2CA_L2': (3, 'SNR Glonass L2'),
        'BeiDou_B1I_L1': (4, 'SNR BeiDou L1'),
        'BeiDouL1': (4, 'SNR BeiDou L1'),
        'BeiDou_L2': (5, 'SNR BeiDou L2'),
        'BeiDou_L5': (5, 'SNR BeiDou L5'),
        'Galileo_L1BC_L1': (6, 'SNR Galileo L1'),
        'Galileo_E5B_L2': (7, 'SNR Galileo L2'),
        'Galileo_E5A_L2': (7, 'SNR Galileo L5')
    }

    # Собираем все доступные данные
    available_data = []

    # Проходим по всем CSV файлам с SNR данными
    for csv_file in os.listdir(path):
        if not csv_file.endswith('_SNR.csv') or nameFile_int not in csv_file:
            continue

        # Извлекаем информацию о системе и сигнале из имени файла
        file_key = csv_file.replace(f'{nameFile_int}_', '').replace('_SNR.csv', '')

        if file_key not in plot_config:
            continue

        # Читаем данные из CSV
        times, data = read_snr_csv(os.path.join(path, csv_file))

        if times:  # Если есть данные
            priority, title = plot_config[file_key]
            available_data.append({
                'key': file_key,
                'times': times,
                'data': data,
                'title': title,
                'priority': priority
            })

    # Сортируем данные по приоритету
    available_data.sort(key=lambda x: x['priority'])

    # Определяем количество графиков
    n_plots = len(available_data)
    if n_plots == 0:
        return

    # Определяем оптимальную конфигурацию сетки
    if n_plots <= 3:
        n_rows, n_cols = 1, n_plots
        figsize = (6 * n_cols, 6)
    elif n_plots <= 6:
        n_rows, n_cols = 2, (n_plots + 1) // 2
        figsize = (6 * n_cols, 12)
    else:
        n_rows, n_cols = 3, (n_plots + 2) // 3
        figsize = (6 * n_cols, 18)

    # Создаем фигуру с нужным количеством subplots
    fig, axs = plt.subplots(n_rows, n_cols, figsize=figsize)

    # Если только один subplot, преобразуем в массив для единообразия
    if n_plots == 1:
        axs = np.array([axs])
    if n_rows == 1:
        axs = axs.reshape(1, -1)
    elif n_cols == 1:
        axs = axs.reshape(-1, 1)

    # Собираем все временные метки для установки общих пределов
    all_times = []
    for data in available_data:
        all_times.extend(data['times'])

    # Устанавливаем общие временные пределы
    if all_times:
        min_time = min(all_times) - timedelta(seconds=10)
        max_time = max(all_times) + timedelta(seconds=10)
    else:
        min_time = max_time = None

    # Рисуем каждый график на своем subplot
    for idx, data in enumerate(available_data):
        row = idx // n_cols
        col = idx % n_cols
        ax = axs[row][col]

        plot_snr(ax, data['times'], data['data'], data['title'], min_time, max_time)

    # Скрываем пустые subplots
    for i in range(n_plots, n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        axs[row][col].set_visible(False)

    # Настраиваем общий вид
    plt.suptitle(f'SNR Analysis - {nameFile_int}', fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93 if n_rows == 1 else 0.95)

    # Создаем папку для результатов, если она не существует
    if not os.path.exists('Result_SNR_4'):
        os.makedirs('Result_SNR_4')

    # Сохраняем график
    output_path = os.path.join('Result_SNR_4', f'{nameFile_int}_combined.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


# Основной код
if __name__ == "__main__":
    # Обрабатываем все файлы в текущей директории
    files = [f for f in os.listdir('.') if f[-4:] in ('.dat', '.ubx', '.log') or f[-5:] == '.cyno']

    for file in files:
        print(f"Processing: {file}")
        # Здесь должен быть код для обработки файла с помощью NMEA.py
        # В данном случае мы просто создаем объединенные графики для уже обработанных файлов
        nameFile_int, _ = os.path.splitext(file)
        create_combined_plots(nameFile_int)