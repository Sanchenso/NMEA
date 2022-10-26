import os
import subprocess

dirname = '/Users/a.timoshkov/PycharmProjects/pythonProject'
files = os.listdir(dirname)
for i in files:
    if i[-4:] == '.dat' or i[-4:] == '.ubx':
        print(i)
        #subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'GPS' + ' ' + 'L1')
        subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'GPS' + ' ' + 'L2')
        #subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'Glonass' + ' ' + 'L1')
        subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'Glonass' + ' ' + 'L2')
        #subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'BeiDou' + ' ' + 'L1')
        #subprocess.call("python " + 'NMEA.py' + ' ' + i + ' ' + 'BeiDou' + ' ' + 'L2')

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

