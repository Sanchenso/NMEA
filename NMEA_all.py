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
