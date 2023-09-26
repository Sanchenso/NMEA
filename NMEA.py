import matplotlib.pyplot as plt
import datetime
import re
import sys

nameFile = sys.argv[1]  # for example 'test.ubx'
systemName = sys.argv[2]  # for example 'GPS'
IDsystem = sys.argv[3]  # for example 'L1'

data = {}
new_Data = {}
all_sat = {}
all_sat2 = {}
all_satElevation = {}
all_satElevation2 = {}

inUse_sat_GPS = []
inUse_sat_Glonass = []
inUse_sat_BeiDou = []
inUse_sat_Galileo = []

PossibleSatInSystem = []
listTimeGGA = []
possibleNMEA = ['$GPGGA', '$GPGSA', '$GNGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$BDGSV', '$GBGSV', '$GAGSV']

# значение elevation, значения ниже этого в рассчете не участует
MinElevation = 10
# значение SNR, значения ниже этого в рассчете не участуют
minSNR = 20
# значение частоты выдачи сообщений в Герц
freq = 1

nSat = 0
countGGA = 0
normstring = 0
countErrorChk = 0
countMess = 0
countChk = 0
averageSNR = 0
countSNR1 = 0

# Проверка входных аргументов. Пример "ally_2J_channel_gnss_126.dat Glonass L2"
if systemName == 'GPS':
    satelliteSystem = '$GPGSV'
    GSA_idSystem = '1'
    inUse_sat_sys = inUse_sat_GPS
    [PossibleSatInSystem.append(i) for i in range(1, 33)]
else:
    if systemName == 'Glonass':
        satelliteSystem = '$GLGSV'
        GSA_idSystem = '2'
        inUse_sat_sys = inUse_sat_Glonass
        [PossibleSatInSystem.append(i) for i in list(range(65, 97)) + list(range(1, 25))]
    else:
        if systemName == 'BeiDou':
            satelliteSystem = ['$GBGSV', '$BDGSV']
            GSA_idSystem = '4'
            inUse_sat_sys = inUse_sat_BeiDou
            [PossibleSatInSystem.append(i) for i in range(1, 64)]
        else:
            if systemName == 'Galileo':
                satelliteSystem = '$GAGSV'
                GSA_idSystem = '3'
                inUse_sat_sys = inUse_sat_Galileo
                [PossibleSatInSystem.append(i) for i in list(range(101, 137)) + list(range(1, 37))]
            else:
                satelliteSystem = 'NON'
                GSA_idSystem = 'NON'
                PossibleSatInSystem = 'NON'
if satelliteSystem == 'NON' or GSA_idSystem == 'NON':
    print('name system error!')
    print('please choose one to enter:')
    print('GPS or Glonass or BeiDou or Galileo')
    print('L1 or L2')


# ф-я заполнение словаря all_sat, включающее L1, L2 и др
def SatSnr(snr_dict, lineSat, lineSnr):
    satN = int(newLine[lineSat].strip())
    snrN = newLine[lineSnr].strip()
    if snrN == '':
        value = snrN
    else:
        value = int(snrN)
    snr_dict.setdefault(satN, {})[time] = value
    return satN, snrN


# ф-я заполнение словаря satElevation, включающее L1, L2 и др
def SatElevation(elevation_dict, lineSat, lineElev):
    satN = int(newLine[lineSat].strip())
    elevN = newLine[lineElev].strip()
    if elevN == '':
        value = elevN
    else:
        value = int(elevN)
    elevation_dict.setdefault(satN, {})[time] = value
    return satN, elevN


# функция парсера сообщений GSV вывод SNR с учетом сообщений GSA (только используемые спутники)
def parserGSV_inUse(newLine, inUse_sat_sys):
    satElevation = all_satElevation if newLine[-3] == '1' else all_satElevation2
    satSnr = all_sat if newLine[-3] == '1' else all_sat2
    if newLine[5] != "*":
        for i in range(4, 20, 4):
            if newLine.index('*') > i + 3:
                if int(newLine[i]) in inUse_sat_sys and int(newLine[i]) in PossibleSatInSystem:
                    SatElevation(satElevation, i, i + 1)
                    SatSnr(satSnr, i, i + 3)
    return


# функция парсера сообщений GSV вывод SNR с учетом сообщений GSA (все видимые спутники)
def parserGSV(newLine):
    satElevation = all_satElevation if newLine[-3] == '1' else all_satElevation2
    satSnr = all_sat if newLine[-3] == '1' else all_sat2
    if newLine[5] != "*":
        for i in range(4, 20, 4):
            if newLine.index('*') > i + 3:
                if newLine[i] != '' and int(newLine[i]) in PossibleSatInSystem:
                    SatElevation(satElevation, i, i + 1)
                    SatSnr(satSnr, i, i + 3)
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
        clean_values = [int(v) for v in values.values() if v != '']
        if clean_values:
            avg = round(sum(clean_values) / len(clean_values), 1)
            list_Average.append(avg)
            list_count_Average.append(len(clean_values))
            list_Sat.append(numerOfSat)

    return list_Average, list_count_Average, list_Sat


# Base перебор сообщений из файла
with open(nameFile, encoding="CP866") as inf2:
    for line in inf2:
        sym = -1
        for i in set(possibleNMEA):
            found = line.find(i)
            if found != -1:
                sym = found

        if sym != -1 and len(line) > 10:
            newLine = line[sym::].replace('*', ',*,').split(',')
            if ((newLine[0] == '$GNGGA') or (newLine[0] == '$GPGGA')) and newLine[1] != '' and chksum_nmea(newLine):
                inUse_sat_sys = []
                try:
                    Time = str(newLine[1].strip())
                    time = datetime.datetime.strptime(Time, '%H''%M''%S.%f')
                    countGGA += 1
                    listTimeGGA.append(newLine[1])
                except:
                    print('find error in logger')
                    print(newLine)
                    print()
            if ((newLine[0] == '$GNGSA') or (newLine[0] == '$GPGSA')) and (newLine[2] == '2' or newLine[2] == '3') \
                    and countGGA >= 1 and newLine[-3] == GSA_idSystem and chksum_nmea(newLine):
                for i in range(3, len(newLine) - 6):
                    if newLine[i] != '':
                        inUse_sat_sys.append(int(newLine[i]))
            if newLine[0] in satelliteSystem and countGGA >= 1 and chksum_nmea(newLine) and len(newLine) < 24:
                # parserGSV(newLine)
                parserGSV_inUse(newLine, inUse_sat_sys)


print('Number of sat in use', systemName, end=': ')
print(len(set(inUse_sat_sys)))
print()

# Подсчет кол-ва сообщений, прошедших проверку  cheksumm
print('Number of messages:', end=' ')
print(countChk)
print('Number of error chksum:', end=' ')
print(countErrorChk)
print('Number of GGA messages:', end=' ')
print(countGGA)
print()

# еще один подсчет времени по сообщениям GGA
last = datetime.datetime.strptime(listTimeGGA[-1], '%H''%M''%S.%f')
first = datetime.datetime.strptime(listTimeGGA[0], '%H''%M''%S.%f')
print('DifTime from first and last GGA:', end=' ')
print((last - first).total_seconds(), 'sec')
print('Frequency:', end=' ')
print(freq, end=' Hz \n')
print('Number of meesage GGA to be:', end=' ')
print((round((last - first).total_seconds() * freq)))

# Подсчет количества секунд и подсчет количества GGA сообщений
countTime = datetime.timedelta(days=0, hours=0, minutes=0)
for i in all_sat.values():
    chislo = max(i.keys()) - min(i.keys())
    if countTime < chislo:
        countTime = chislo
print('Number of seconds:', end=' ')
print(round(countTime.total_seconds()) + 1)
print()

# вывод значений среднего SNR для каждого спутника в зависимости от системы в консоли
if IDsystem == 'L1':
    all_sat_chosen = all_sat
    all_satElevation_chosen = all_satElevation
else:
    all_sat_chosen = all_sat2
    all_satElevation_chosen = all_satElevation2

p = average(all_sat_chosen)
m = average(all_satElevation_chosen)

for i in range(len(p[0])):
    if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > minSNR:
        averageSNR += p[0][i]
        countSNR1 += 1
    else:
        print('Sat', p[2][i], 'CountValue', p[1][i], 'CountSec', round((last - first).total_seconds()), '\n',
              'Check log! Many miss value!')
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
for i in all_sat_chosen.values():
    gh += 1
    for k in i.values():
        if k != '':
            schet += 1
            Average += int(k)
print('real average SNR:', end=' ')
print(round((Average / schet), 1))
print('real number of sat average SNR: ', end='')
print(gh)

'''
# запись полученных данных в новый файл
with open(nameFile + ", " + systemName + '_' + IDsystem + '.txt', 'w') as f:
    f.write('                    ')
    f.write(nameFile[0:-4] + '_' + systemName + '_' + IDsystem)
    f.write('\n')
    f.write('                    ')
    f.write('CountMes: ' + str(countChk) + ' ErrMes: ' + str(countErrorChk))
    f.write('\n')
    f.write('                    ')
    f.write('CountPiont: ' + str(countTime.total_seconds()))
    f.write('\n')

    for j in range(len(p[0])):
        f.write(str(p[0][j]))
        f.write(' ')
        f.write(str(p[1][j]))
        f.write(' ')
        f.write(str(p[2][j]))
        f.write(' ')
        if j < len(m[0]):
            f.write(str(m[0][j]))
            f.write(' ')
            f.write(str(m[1][j]))
            f.write(' ')
            f.write(str(m[2][j]))
            f.write('\n')
        else:
            f.write('\n')
'''

# вывод графика и сохранение в jpeg
result = all_sat_chosen.values()

# дозапись осреденных в файл test.txt - для скрипта
with open('test.txt', 'a') as f1:
    f1.write(nameFile[0:-4])
    f1.write('_')
    f1.write(systemName)
    f1.write('_')
    f1.write(IDsystem)
    # f1.write('L1')
    f1.write(' ')
    f1.write(str(round((Average / schet), 1)))
    # f1.write(str(round((averageSNR / countSNR1), 1)))
    f1.write(' ')
    f1.write(str(gh))
    f1.write(' ')
    f1.write(str(countGGA))  # number of GGA messages
    f1.write(' ')
    f1.write(str(countErrorChk))  # ErrMes
    f1.write(' ')
    f1.write(str(round((last - first).total_seconds() * freq)))  # DifTime from first and last GGA
    f1.write('\n')

# вывод и сохранение графика в формате jpeg
fig, ax = plt.subplots(figsize=(12, 8))
for k in result:
    k = {key: value for (key, value) in k.items() if value}
    myList = sorted(k.items())
    if len(myList) > 0:
        x, y = zip(*myList)
        """sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False, 'figure.figsize': (
        20, 10)}) sns.lineplot(x=x, y=y, size=6) sns.scatterplot(x=x, y=y, s=6)"""
        ax.plot(x, y, marker='o', markersize=2)

# установка формата времени на оси x
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# создание пользовательского локатора с шагом в 30 минут
# locator = mdates.MinuteLocator(interval=1)

# установка пользовательского локатора на оси x
# ax.xaxis.set_major_locator(locator)


plt.xlabel('Time', fontsize=14)
plt.ylabel('SNR, dBHz', fontsize=14)
# print(x[0])
plt.text(x[0], 57, 'average SNR:', fontsize=14)
plt.text(x[0], 54, '        dBHz', fontsize=14)
plt.text(x[0], 54, str(round((Average / schet), 1)), fontsize=14)
# plt.text(x[0], 55, str(round((averageSNR / countSNR1), 1)))
plt.title(nameFile + ", " + systemName + '_' + IDsystem, fontsize=14)
# plt.title(nameFile + ", " + systemName + '_' + 'L1')
# plt.title(nameFile + ", " + systemName)
plt.ylim(10, 60)
plt.grid(color='black', linestyle='--', linewidth=0.2)
plt.legend([], [], frameon=False)
plt.legend(all_sat_chosen.keys(), loc='upper right')
nameFileSaved = nameFile[0:-4] + '_' + systemName + '_' + IDsystem + '.png'
# nameFileSaved = nameFile[0:-4] + '_' + systemName + '_' + 'L1' + '.png'
plt.savefig(nameFileSaved, dpi=500)
plt.show()
