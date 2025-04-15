import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime
from matplotlib.dates import SecondLocator
import subprocess

dfGPSL1 = pd.DataFrame()
dfGPSL2 = pd.DataFrame()
dfBeiDouL1 = pd.DataFrame()
dfBeiDouL2 = pd.DataFrame()
dfGlonassL1 = pd.DataFrame()
dfGlonassL2 = pd.DataFrame()
df = pd.DataFrame()
files = os.listdir()
processes = []


for i in files:
    if i[-4:] in ('.dat', '.ubx', '.log') or i[-5:] == '.cyno':
        print(i)
        #subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'GSV', shell=True)
        subprocess.call("python3 " + 'NMEA.py ' + i, shell=True)
# Wait for all processes to complete
for process in processes:
    process.wait()

path = "Result_CSV"
files_in_path = os.listdir(path)
format_date_time = "%H:%M:%S.%f"

def parse_multiple_formats(date_str):
    formats = ["%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S.%f"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    print(f"Не удалось преобразовать: {date_str}")  # Вывод строки, которая не подошла ни под один формат
    return pd.NaT  # Если ни один формат не подошел, возвращаем NaT

if not os.path.exists('Result_SNR_4'):
    os.makedirs('Result_SNR_4')


for binfile in os.listdir():
    nameFile_int, nameFile_ext = os.path.splitext(binfile)
    if nameFile_ext in ('.dat', '.ubx', '.log') or nameFile_ext == '.cyno':
        csv_files = {
            'dfGPSL1': '_GPS_L1CA_L1_SNR.csv',
            'dfGPSL2_CM': '_GPS_L2CM_L2_SNR.csv',
            'dfGPSL2_CL': '_GPS_L2CL_L2_SNR.csv',
            'dfGPSL5': '_GPS_L5Q_L5_SNR.csv',
            'dfBeiDouL1': '_BeiDou_B1I_L1_SNR.csv',
            'dfBeiDouL2': '_BeiDou_L2_SNR.csv',
            'dfBeiDouL5': '_BeiDou_L5_SNR.csv',
            'dfGlonassL1': '_Glonass_G1CA_L1_SNR.csv',
            'dfGlonassL2': '_Glonass_G2CA_L2_SNR.csv',
            'dfGalileoL1': '_Galileo_L1BC_L1_SNR.csv',
            'dfGalileoL2': '_Galileo_E5B_L2_SNR.csv',
            'dfGalileoL5': '_Galileo_E5A_L2_SNR.csv'
        }
        loaded_dataframes = {}
        for key, suffix in csv_files.items():
            csv_file = os.path.join(path, nameFile_int + suffix)
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, header=0, sep=',', skiprows=0)
                #df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'], format=format_date_time)
                loaded_dataframes[key] = df
        
        
        # Extract loaded DataFrames
        dfGPSL1 = loaded_dataframes.get('dfGPSL1')
        dfGPSL2_CM = loaded_dataframes.get('dfGPSL2_CM')
        dfGPSL2_CL = loaded_dataframes.get('dfGPSL2_CL')
        dfGPSL5 = loaded_dataframes.get('dfGPSL5')
        dfBeiDouL1 = loaded_dataframes.get('dfBeiDouL1')
        dfBeiDouL2 = loaded_dataframes.get('dfBeiDouL2')
        dfBeiDouL5 = loaded_dataframes.get('dfBeiDouL5')
        dfGlonassL1 = loaded_dataframes.get('dfGlonassL1')
        dfGlonassL2 = loaded_dataframes.get('dfGlonassL2')

        dataframes = [dfGPSL1, dfGPSL2_CM, dfGPSL2_CL, dfGlonassL1, dfGlonassL2, dfBeiDouL1, dfBeiDouL2, dfGPSL5, dfBeiDouL5]
        # Check missing dataframes
        dataframes = [df for df in dataframes if df is not None]
        if len(dataframes) != 0:
            for df in dataframes:
                df['GPS_Time'] = df['GPS_Time'].apply(parse_multiple_formats)
                #df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'])
            min_time = min(df['GPS_Time'].min() for df in dataframes) - timedelta(seconds=5)
            max_time = max(df['GPS_Time'].max() for df in dataframes) + timedelta(seconds=5)

                # SNR
        # Initialize the 2x2 grid of subplots
        def plot_snr(dataframe, title, ax, min_time, max_time):
            ax.set_title(title,x=0.5, y=1, fontsize=8)
            for column in dataframe.columns[1:]:
                ax.plot(dataframe['GPS_Time'], dataframe[column], label=column, linewidth=0.2)
                ax.scatter(dataframe['GPS_Time'], dataframe[column], s=2)
            sumSNR = dataframe.iloc[:, 1:].sum().sum()
            countSNR = dataframe.iloc[:, 1:].count().sum()
            avgSNR = round(sumSNR / countSNR, 1)
            print(avgSNR)
            ax.text(0.05, 0.9, 'average:', fontsize=8, transform=ax.transAxes, verticalalignment='top')
            ax.text(0.16, 0.9, f'{avgSNR} dBHz', fontsize=8, transform=ax.transAxes, verticalalignment='top')
            ax.set_ylim(10, 60)
            ax.set_xlim(min_time, max_time)
            ax.set_xlabel('Time', fontsize=8)
            ax.tick_params(axis='x', which='major', labelsize=8)
            ax.tick_params(axis='y', which='major', labelsize=8)
            ax.set_ylabel('SNR, dBHz', fontsize=8)
            ax.grid(color='black', linestyle='--', linewidth=0.2)
            ax.legend(bbox_to_anchor=(1, 1), loc='upper left', fontsize=8)
            time_format = mdates.DateFormatter('%H:%M:%S')
            
            # Locator для определения интервала
            time_of_flight = max_time - min_time
            interval_time_of_flight = int(time_of_flight.total_seconds()//5)
            #locator = SecondLocator(interval=interval_time_of_flight)
            #locator = MinuteLocator(interval=int(time_of_flight.total_seconds()/360))
            #ax.xaxis.set_major_locator(locator) # Задаем интервал
            ax.xaxis.set_major_formatter(time_format)
            

        fig, axs = plt.subplots(3, 2, figsize=(12, 10))

        # Flatten the array to iterate easily
        axs = axs.flatten()

        # List to keep track of used subplots
        used_axs = []
        if dfGPSL1 is not None:
            plot_snr(dfGPSL1, 'SNR GPS L1, NMEA GSV', axs[0], min_time, max_time)
            used_axs.append(0)
        if dfGPSL2_CM is not None:
            plot_snr(dfGPSL2_CM, 'SNR GPS L2, NMEA GSV', axs[1], min_time, max_time)
            used_axs.append(1)
        if dfGPSL2_CL is not None:
            plot_snr(dfGPSL2_CL, 'SNR GPS L2, NMEA GSV', axs[1], min_time, max_time)
            used_axs.append(1)
        if dfGPSL5 is not None:
            plot_snr(dfGPSL5, 'SNR GPS L5, NMEA GSV', axs[1], min_time, max_time)
            used_axs.append(1)
        if dfBeiDouL1 is not None:
            plot_snr(dfBeiDouL1, 'SNR BeiDou L1, NMEA GSV', axs[2], min_time, max_time)
            used_axs.append(2)
        if dfBeiDouL2 is not None:
            plot_snr(dfBeiDouL2, 'SNR BeiDou L2, NMEA GSV', axs[3], min_time, max_time)
            used_axs.append(3)
        if dfBeiDouL5 is not None:
            plot_snr(dfBeiDouL5, 'SNR BeiDou L5, NMEA GSV', axs[3], min_time, max_time)
            used_axs.append(3)
        if dfGlonassL1 is not None:
            plot_snr(dfGlonassL1, 'SNR Glonass L1, NMEA GSV', axs[4], min_time, max_time)
            used_axs.append(4)
        if dfGlonassL2 is not None:
            plot_snr(dfGlonassL2, 'SNR Glonass L2, NMEA GSV', axs[5], min_time, max_time)
            used_axs.append(5)         

        # Adjust layout
        for ax_idx in set(range(6)) - set(used_axs):
            fig.delaxes(axs[ax_idx])
        
        # Optional: Reconfigure the layout for remaining subplots
        fig.tight_layout()
        fig.suptitle(binfile[:-4], x=0.5, y=0.97, verticalalignment='top')

        plt.tight_layout()
        plt.savefig('Result_SNR_4/' + binfile[:-4] + '.jpeg', dpi=200, bbox_inches='tight')
        #plt.show()
        plt.close()