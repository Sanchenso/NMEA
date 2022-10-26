import matplotlib.pyplot as plt
import datetime
import seaborn as sns
import re
import sys

nameFile = sys.argv[1]  # for example 'test.ubx'
systemName = sys.argv[2]  # for example 'GPS'
IDsystem = sys.argv[3] # for example 'L1'

data = {}
new_Data = {}
all_sat = {}
all_sat2 = {}
all_satElevation = {}
all_satElevation2 = {}
inUse_sat = []
PossibleSatInSystem = []
listTimeGGA = []
possibleNMEA = ['$GPGGA', '$GPGSA', '$GNGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$BDGSV', '$GBGSV', '$GAGSV']

# значение elevation, значения ниже этого в рассчете не участует
MinElevation = 10
# значение SNR, значения ниже этого в рассчете не участует
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
    [PossibleSatInSystem.append(i) for i in range(1, 33)]
else:
    if systemName == 'Glonass':
        satelliteSystem = '$GLGSV'
        GSA_idSystem = '2'
        [PossibleSatInSystem.append(i) for i in range(65, 89)]
    else:
        if systemName == 'BeiDou':
            satelliteSystem = ['$GBGSV', '$BDGSV']
            GSA_idSystem = '4'
            [PossibleSatInSystem.append(i) for i in range(1, 64)]
        else:
            if systemName == 'Galileo':
                satelliteSystem = '$GAGSV'
                GSA_idSystem = '3'
                [PossibleSatInSystem.append(i) for i in range(101, 137)]
            else:
                satelliteSystem = 'NON'
                GSA_idSystem = 'NON'
                PossibleSatInSystem = 'NON'
if satelliteSystem == 'NON' or GSA_idSystem == 'NON':
    print('name system error!')
    print('please choose one to enter:')
    print('GPS or Glonass or BeiDou or Galileo')
    print('L1 or L2')
print(PossibleSatInSystem)

# ф-я заполнение словаря all_sat, включающее L1
def SatSnr(lineSat, lineSnr):
    satN = int(newLine[lineSat].strip())
    snrN = newLine[lineSnr].strip()
    if satN in all_sat:
        if snrN == '':
            all_sat[satN][time] = snrN
        else:
            all_sat[satN][time] = int(snrN)
    else:
        if snrN == '':
            data[time] = snrN
        else:
            data[time] = int(snrN)
        all_sat[satN] = data.copy()
    return satN, snrN


# ф-я заполнение словаря all_sat2, включающее L2 и др. системы
def SatSnr2(lineSat, lineSnr):
    satN = int(newLine[lineSat].strip())
    snrN = newLine[lineSnr].strip()
    if satN in all_sat2:
        if snrN == '':
            all_sat2[satN][time] = snrN
        else:
            all_sat2[satN][time] = int(snrN)
    else:
        if snrN == '':
            data[time] = snrN
        else:
            data[time] = int(snrN)
        all_sat2[satN] = data.copy()
    return satN, snrN


# ф-я заполнение словаря satElevation, включающее L1
def SatElevation(lineSat, lineElev):
    satN = int(newLine[lineSat].strip())
    elevN = newLine[lineElev].strip()
    if satN in all_satElevation:
        if elevN == '':
            all_satElevation[satN][time] = elevN
        else:
            all_satElevation[satN][time] = int(elevN)
    else:
        if elevN == '':
            data[time] = elevN
        else:
            data[time] = int(elevN)
        all_satElevation[satN] = data.copy()
    return satN, elevN


# ф-я заполнение словаря satElevation, включающее L2 и другие системы
def SatElevation2(lineSat, lineElev):
    satN = int(newLine[lineSat].strip())
    elevN = newLine[lineElev].strip()
    if satN in all_satElevation2:
        if elevN == '':
            all_satElevation2[satN][time] = elevN
        else:
            all_satElevation2[satN][time] = int(elevN)
    else:
        if elevN == '':
            data[time] = elevN
        else:
            data[time] = int(elevN)
        all_satElevation2[satN] = data.copy()
    return satN, elevN


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


# функция парсера сообщений GSV вывод SNR
def parserGSV(newLine):
    if newLine[-3] == '1' and newLine[5] != "*":
        if newLine.index('*') > 7:
            if newLine[4] != '' and int(newLine[4]) in PossibleSatInSystem:
                [SatElevation(4, 5) if newLine[5] != '' and int(newLine[5]) > MinElevation else 'zero']
                [SatSnr(4, 7) if newLine[5] != '' and int(newLine[5]) > MinElevation else 'zero']
            if newLine.index('*') > 11:
                if newLine[8] != '' and newLine[8] != '' and int(newLine[8]) in PossibleSatInSystem:
                    [SatElevation(8, 9) if newLine[9] != '' and int(newLine[9]) > MinElevation else 'zero']
                    [SatSnr(8, 11) if newLine[9] != '' and int(newLine[9]) > MinElevation else 'zero']
                if newLine.index('*') > 15:
                    if newLine[12] != '' and int(newLine[12]) in PossibleSatInSystem:
                        [SatElevation(12, 13) if newLine[13] != '' and int(newLine[13]) > MinElevation else 'zero']
                        [SatSnr(12, 15) if newLine[13] != '' and int(newLine[13]) > MinElevation else 'zero']
                    if newLine.index('*') > 19:
                        if newLine[16] != '' and int(newLine[16]) in PossibleSatInSystem:
                            [SatElevation(16, 17) if newLine[17] != '' and int(newLine[17]) > MinElevation else 'zero']
                            [SatSnr(16, 19) if newLine[17] != '' and int(newLine[17]) > MinElevation else 'zero']

    else:
        if newLine[5] != "*":
            if newLine.index('*') > 7:
                if newLine[4] != '' and int(newLine[4]) in PossibleSatInSystem:
                    [SatElevation2(4, 5) if newLine[5] != '' and int(newLine[5]) > MinElevation else 'zero']
                    [SatSnr2(4, 7) if newLine[5] != '' and int(newLine[5]) > MinElevation else 'zero']
                if newLine.index('*') > 11:
                    if newLine[8] != '' and int(newLine[8]) in PossibleSatInSystem:
                        [SatElevation2(8, 9) if newLine[9] != '' and int(newLine[9]) > MinElevation else 'zero']
                        [SatSnr2(8, 11) if newLine[9] != '' and int(newLine[9]) > MinElevation else 'zero']
                    if newLine.index('*') > 15:
                        if newLine[12] != '' and int(newLine[12]) in PossibleSatInSystem:
                            [SatElevation2(12, 13) if newLine[13] != '' and int(newLine[13]) > MinElevation else 'zero']
                            [SatSnr2(12, 15) if newLine[13] != '' and int(newLine[13]) > MinElevation else 'zero']
                        if newLine.index('*') > 19:
                            if newLine[16] != '' and int(newLine[16]) in PossibleSatInSystem:
                                [SatElevation2(16, 17) if newLine[17] != '' and int(
                                    newLine[17]) > MinElevation else 'zero']
                                [SatSnr2(16, 19) if newLine[17] != '' and int(newLine[17]) > MinElevation else 'zero']
    return


# функция парсера сообщений GSV вывод SNR с учетом сообщений GSA (все видимы спутники)
def parserGSV_inUse(newLine, inUse_sat):
    if newLine[-3] == '1':
        if newLine[5] != "*":
            if newLine.index('*') > 7:
                if int(newLine[4]) in inUse_sat and int(newLine[4]) in PossibleSatInSystem:
                    SatElevation(4, 5)
                    SatSnr(4, 7)
                if newLine.index('*') > 11:
                    if int(newLine[8]) in inUse_sat and int(newLine[8]) in PossibleSatInSystem:
                        SatElevation(8, 9)
                        SatSnr(8, 11)
                    if newLine.index('*') > 15 and int(newLine[12]) in PossibleSatInSystem:
                        if int(newLine[12]) in inUse_sat:
                            SatElevation(12, 13)
                            SatSnr(12, 15)
                        if newLine.index('*') > 19 and int(newLine[16]) in PossibleSatInSystem:
                            if int(newLine[16]) in inUse_sat:
                                SatElevation(16, 17)
                                SatSnr(16, 19)
    else:
        if newLine[5] != "*":
            if newLine.index('*') > 7:
                if int(newLine[4]) in inUse_sat and int(newLine[4]) in PossibleSatInSystem:
                    SatElevation2(4, 5)
                    SatSnr2(4, 7)
                if newLine.index('*') > 11:
                    if int(newLine[8]) in inUse_sat and int(newLine[8]) in PossibleSatInSystem:
                        SatElevation2(8, 9)
                        SatSnr2(8, 11)
                    if newLine.index('*') > 15:
                        if int(newLine[12]) in inUse_sat and int(newLine[12]) in PossibleSatInSystem:
                            SatElevation2(12, 13)
                            SatSnr2(12, 15)
                        if newLine.index('*') > 19:
                            if int(newLine[16]) in inUse_sat and int(newLine[16]) in PossibleSatInSystem:
                                SatElevation2(16, 17)
                                SatSnr2(16, 19)


# функция вывода данных в список для записи в файл
def average(dataDict):
    list_Average = []
    list_count_Average = []
    list_Sat = []
    for i in dataDict.items():
        numerOfSat = 0
        for j in i:
            if type(j) != dict:
                numerOfSat = j
            else:
                Average = 0
                count_Average = 0
                for k in j.values():
                    if k != '':
                        Average += int(k)
                        count_Average += 1
                if Average != 0 and count_Average != 0:
                    list_Average.append(round((Average / count_Average), 1))
                    list_count_Average.append(count_Average)
                    list_Sat.append(numerOfSat)
    return list_Average, list_count_Average, list_Sat


# Base перебор сообщений из файла
with open(nameFile, encoding="CP866") as inf2:
    for line in inf2:
        sym = -1
        for i in set(possibleNMEA):
            if line.find(i) != -1:
                sym = line.find(i)

        if sym != -1 and len(line) > 10:
            newLine = line[sym::].replace('*', ',*,').split(',')
            if ((newLine[0] == '$GNGGA') or (newLine[0] == '$GPGGA')) and newLine[1] != '' and chksum_nmea(newLine):
                inUse_sat = []
                try:
                    Time = str(float(newLine[1].strip()))
                    time = datetime.datetime.strptime(Time, '%H''%M''%S.%f')
                    countGGA += 1
                    listTimeGGA.append(newLine[1])
                except:
                    print('find error in logger')
                    print(newLine)
                    print()
            if ((newLine[0] == '$GNGSA') or (newLine[0] == '$GPGSA')) and (newLine[2] == '2' or newLine[2] == '3') \
                    and chksum_nmea(newLine) and countGGA >= 1:
#                    and chksum_nmea(newLine) and countGGA >= 1 and newLine[-3] == GSA_idSystem:
                for i in range(3, len(newLine) - 6):
                    if newLine[i] != '' and len(newLine[i]) == 2:
                        inUse_sat.append(int(newLine[i]))
            if newLine[0] in satelliteSystem and countGGA >= 1 and chksum_nmea(newLine) and len(newLine) < 24:
                parserGSV(newLine)
                #parserGSV_inUse(newLine, inUse_sat)

print('Number of sat all: ', end='')
print(len(all_sat.keys()))
print('Number of sat in use: ', end='')
print(len(inUse_sat))
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
print((last - first).total_seconds())
print('Frequency:', end=' ')
print(freq, end=' Hz \n')
print('Number of meesage GGA to be:', end=' ')
print((round((last - first).total_seconds()*freq)))

# Подсчет количества секунд и подсчет количества GGA сообщений
countTime = datetime.timedelta(days=0, hours=0, minutes=0)
for i in all_sat.values():
    chislo = max(i.keys()) - min(i.keys())
    if countTime < chislo:
        countTime = chislo
print('Number of seconds:', end=' ')
print(round(countTime.total_seconds())+1)
print('Number of meesage GGA to be:', end=' ')
print((round(countTime.total_seconds())+1)*freq)
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
print(p)
print(m)

for i in range(len(p[0])):
    if p[1][i] > (countGGA / 10) and p[0][i] > minSNR:
        averageSNR += p[0][i]
        countSNR1 += 1
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

# запись полученных данных в новый файл
with open(nameFile + ", " + systemName + '_' + IDsystem + '.txt', 'w') as f:
    f.write('                    ')
    f.write(nameFile[0:-4] + '_' + systemName + '_' + IDsystem)
    f.write('\n')
    f.write('                    ')
    f.write('CountMes: ' + str(countChk) + ' ErrMes: ' + str(countErrorChk))
    f.write('\n')
    f.write('                    ')
    f.write('CountPiont: ' + str(countTime.total_seconds() * 5))
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

    # вывод графика и сохранение в jpeg
    result = all_sat_chosen.values()

# дозапись осреденных в файл test.txt - для скрипта
with open('test.txt', 'a') as f1:
    f1.write(nameFile)
    f1.write('_')
    f1.write(systemName)
    f1.write('_')
    f1.write(IDsystem)
    f1.write('\n')
    f1.write('average_SNR: ')
    f1.write(str(round((averageSNR / countSNR1), 1)))
    f1.write(' ')
    f1.write(str(countSNR1))
    f1.write('\n')
    f1.write('real_average_SNR: ')
    f1.write(str(round((Average / schet), 1)))
    f1.write(' ')
    f1.write(str(gh))
    f1.write('\n')

# вывод и сохранение графика в формате jpeg
for k in result:
    k = {key: value for (key, value) in k.items() if value}
    myList = sorted(k.items())
    if len(myList) > 0:
        x, y = zip(*myList)
        sns.set_theme(style="ticks",
                      rc={"axes.spines.right": False, "axes.spines.top": False, 'figure.figsize': (8, 6)})
        sns.lineplot(x=x, y=y, size=8)
        sns.scatterplot(x=x, y=y, s=8)


plt.xlabel('Time')
plt.ylabel('SNR, dBHz')
print(x[0])
plt.text(x[0], 57, 'average_SNR:')
plt.text(x[0], 55, '        dBHz')
plt.text(x[0], 55, str(round((Average / schet), 1)))
plt.title(nameFile + ", " + systemName + '_' + IDsystem)
#plt.title(nameFile + ", " + systemName)
plt.ylim(10, 60)
plt.grid(color='black', linestyle='--', linewidth=0.2)
plt.legend([], [], frameon=False)
plt.legend(all_sat_chosen.keys(), loc='upper right')
nameFileSaved = nameFile[0:-4] + '_' + systemName + '_' + IDsystem + '.png'
plt.savefig(nameFileSaved, dpi=500)
plt.show()
