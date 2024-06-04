import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from matplotlib.dates import MinuteLocator

dfGPSL1 = pd.DataFrame()
dfGPSL2 = pd.DataFrame()
dfBeiDouL1 = pd.DataFrame()
dfBeiDouL2 = pd.DataFrame()
dfGlonassL1 = pd.DataFrame()
dfGlonassL2 = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)
format_date_time = "%H:%M:%S.%f"

if not os.path.exists('Result_SNR_4'):
    os.makedirs('Result_SNR_4')

for binfile in os.listdir():
    nameFile_int, nameFile_ext = os.path.splitext(binfile) 
    if nameFile_ext == '.cyno':
        print(binfile)
        csv_files = {
            'dfGPSL1': '_GPS_L1_SNR.csv',
            'dfGPSL2': '_GPS_L2_SNR.csv',
            'dfBeiDouL1': '_BeiDou_L1_SNR.csv',
            'dfBeiDouL2': '_BeiDou_L2_SNR.csv',
            'dfGlonassL1': '_Glonass_L1_SNR.csv',
            'dfGlonassL2': '_Glonass_L2_SNR.csv'
        }
        loaded_dataframes = {}
        for key, suffix in csv_files.items():
            csv_file = os.path.join(path, nameFile_int + suffix)
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, header=0, sep=',', skiprows=0)
                df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'], format=format_date_time)
                loaded_dataframes[key] = df
        
        
        # Extract loaded DataFrames
        dfGPSL1 = loaded_dataframes.get('dfGPSL1')
        dfGPSL2 = loaded_dataframes.get('dfGPSL2')
        dfBeiDouL1 = loaded_dataframes.get('dfBeiDouL1')
        dfBeiDouL2 = loaded_dataframes.get('dfBeiDouL2')
        dfGlonassL1 = loaded_dataframes.get('dfGlonassL1')
        dfGlonassL2 = loaded_dataframes.get('dfGlonassL2')
        
        dataframes = [dfGPSL1, dfGPSL2, dfGlonassL1, dfGlonassL2, dfBeiDouL1, dfBeiDouL2]
        
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df['Unnamed: 0'].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df['Unnamed: 0'].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time.strftime(format_date_time), max_time.strftime(format_date_time))
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4], x=0.5, y=0.95, verticalalignment='top')

                # SNR
        # Initialize the 2x2 grid of subplots
        def plot_snr(dataframe, title, ax, min_time, max_time):
            ax.set_title(title, fontsize=11)
            for column in dataframe.columns[1:]:
                ax.plot(dataframe['Unnamed: 0'], dataframe[column], label=column)
            sumSNR = dataframe.iloc[:, 1:].sum().sum()
            countSNR = dataframe.iloc[:, 1:].count().sum()
            avgSNR = round(sumSNR / countSNR, 1)
            print(avgSNR)
            ax.text(0.1, 0.9, 'average:', fontsize=10, transform=ax.transAxes)
            ax.text(0.27, 0.9, f'{avgSNR} dBHz', fontsize=10, transform=ax.transAxes)
            ax.set_ylim(10, 60)
            ax.set_xlim(min_time, max_time)
            ax.set_ylabel('SNR, dBHz', fontsize=10)
            ax.grid(color='black', linestyle='--', linewidth=0.1)
            ax.legend(bbox_to_anchor=(1, 1), loc="upper left", fontsize=10)
            time_format = mdates.DateFormatter('%H:%M:%S')
            # Locator для определения интервала в 2 минуты
            locator = MinuteLocator(interval=3)
            ax.xaxis.set_major_locator(locator) # Задаем интервал
            ax.xaxis.set_major_formatter(time_format)


        fig, axs = plt.subplots(3, 2, figsize=(12, 10))

        plot_snr(dfGPSL1, 'SNR GPS L1, NMEA GSV', axs[0, 0], min_time, max_time)
        plot_snr(dfGPSL2, 'SNR GPS L2, NMEA GSV', axs[0, 1], min_time, max_time)
        plot_snr(dfGlonassL1, 'SNR Glonass L1, NMEA GSV', axs[1, 0], min_time, max_time)
        plot_snr(dfGlonassL2, 'SNR Glonass L2, NMEA GSV', axs[1, 1], min_time, max_time)
        plot_snr(dfBeiDouL1, 'SNR BeiDou L1, NMEA GSV', axs[2, 0], min_time, max_time)
        plot_snr(dfBeiDouL2, 'SNR BeiDou L2, NMEA GSV', axs[2, 1], min_time, max_time)
        axs[1, 1].set_xlabel('Time')  # Добавлено значение для оси X на последнем графике

        plt.tight_layout()
        plt.savefig('Result_SNR_4/' + binfile[:-4], dpi=500)
        plt.show()
        