import os
import subprocess

#dirname = '/Users/a.timoshkov/PycharmProjects/pythonProject'
files = os.listdir()
for i in files:
    if i[-4:] == '.dat' or i[-4:] == '.ubx' or i[-4:] == '.log' or i[-5:] == '.cyno':
        print(i)
        subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'GPS' + ' ' + 'L1', shell=True)
        subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'GPS' + ' ' + 'L2', shell=True)
        #subprocess.call("python3 " + 'NMEA.py' + ' ' + i + ' ' + 'Glonass' + ' ' + 'L1', shell=True)
        #subprocess.call("python3 " + 'NMEA.py' + ' ' + i + ' ' + 'Glonass' + ' ' + 'L2', shell=True)
        subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'BeiDou' + ' ' + 'L1', shell=True)
        subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'BeiDou' + ' ' + 'L2', shell=True)
        #subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'Galileo' + ' ' + 'L1', shell=True)
        #subprocess.call("python3 " + 'NMEA.py ' + i + ' ' + 'Galileo' + ' ' + 'L2', shell=True)
'''
dirname = '/Users/a.timoshkov/PycharmProjects/pythonProject'
files = os.listdir(dirname)
type = 'ou_L1.txt', 'ou_L2.txt', 'PS_L1.txt', 'PS_L2.txt', 'ss_L1.txt', 'ss_L2.txt'
print(type)
for k in type:
    with open('all_dat_' + k, 'w') as f:
        for i in files:
            if i[-9::] == k:
                print(i)
                file = open(i).read()
                f.write(file)
                f.write('\n')
'''
