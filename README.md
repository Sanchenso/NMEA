# NMEA
parser SNR for Nmea

nameFile = sys.argv[1]  # for example 'test.ubx'
systemName = sys.argv[2]  # for example 'GPS'
IDsystem = sys.argv[3] # for example 'L1'

For example:
'python3 test.ubx GPS L1'

output file:
nameFile_GPS_L1.png - picture of SNR
nameFile, GPS_L1.txt - table containing detailed information about SNR.

Column names:
SNR, count of point SNR, name Satillites, elevation, count of point Elevation, name Satillites
