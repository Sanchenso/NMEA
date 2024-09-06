# NMEA
parser SNR for Nmea

### NMEA.py

functions: parsing the NMEA 4.10 (GGA, GSA, RMC, GSV messages) of the selected configuration

arguments (configuration):

1 - name of log ("logname.dat")

2 - name of gnss system ("GPS""Glonass"/"BeiDou"/"Galileo")

3 - name of frequency ("L1" or "L2")

usage example: python3 NMEA.py logname.dat GPS L1

output:

- create folder "Result_SNR" with resulst picture logname.png with the SNR of the selected configuration
- create folder "Result_CSV" with data of SNR of the selected configuration
- generate file text.txt with average data of the selected configuration or additional writing to a file if it exist
- show plot


### NMEA_all.py 

arguments: None

functions:

- launches the NMEA.py with configurations "GPS L1", "GPS L2", "BeiDou L1", "BeiDou L2".
- parses all logs with the dat extension in the directory
- add one picture with all graphics in folder "Result_SNR_4" and show this picture

usage example: python3 NMEA_all.py


### NMEA.exe 

functions: compiled script NMEA.py for Windows

usage example in CMD/PowerShell: .\NMEA.exe logname.dat GPS L1

### NMEA.bin 

functions: compiled script NMEA.py for Linux

usage example in bash: ./NMEA.bin logname.dat GPS L1
