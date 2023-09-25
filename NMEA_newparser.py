import sys
import pynmea2
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

nameFile = sys.argv[1]  # for example 'test.ubx'
#nameFile = '20146.txt'
speeds = []
timestamps = []
dictSpeedTime = {}
numsec = 0
numsecEr = 0

def knots_to_kmph(speed_knots):
    speed_kmph = speed_knots * 1.852
    return speed_kmph


with open(nameFile, 'r', encoding="CP866") as file:
    print('Time_Error:', end='\n')
    for line in file:
        start_index = line.find('$GNRMC')
        if start_index == -1:
            continue
        elif line[start_index:].split(',')[1] == '':
            numsecEr += 1
            continue
        numsec += 1
        # пропускаем первые три сообщения
        if numsec >= 3:
            try:
                message = line[start_index:].strip()
                msg = pynmea2.parse(message)
                # Получаем время из сообщения
                Time = str(message.split(',')[1].strip())
                time = datetime.datetime.strptime(Time, '%H''%M''%S.%f')

                if msg.spd_over_grnd != None:
                    dictSpeedTime[time] = [msg.spd_over_grnd * 1.852]
                else:
                    numsecEr += 1
                    print(time)
            except pynmea2.ParseError:
                continue
print('Number of massage:', numsec)
print('Number of error value:', numsecEr)

# Построение графика
fig, ax = plt.subplots(figsize=(10, 6))

timestamps = list(dictSpeedTime.keys())
speeds = [value[0] for value in dictSpeedTime.values()]
'''
start_time = datetime.datetime(1900, 1, 1, 00, 23, 38)
end_time = datetime.datetime(1900, 1, 1, 00, 24, 15)
plt.xlim(start_time, end_time)
'''
time_format = mdates.DateFormatter('%H:%M:%S')
ax.xaxis.set_major_formatter(time_format)
plt.grid(color='black', linestyle='--', linewidth=0.2)
plt.plot(timestamps, speeds, marker='o', markersize=2)
plt.xlabel('Time', fontsize=12)
plt.ylabel('Velocity, kmph', fontsize=12)

plt.title(nameFile[:-4], fontsize=18)
plt.savefig(nameFile[:-4], dpi=500)
plt.show()
