import os
import sys

import warnings # this is for GUI warnings
warnings.filterwarnings("ignore")

srcpath = os.path.realpath('SourceFiles')
sys.path.append(srcpath)

from tevisainst import TEVisaInst


'''
# Connect to instrument(PXI)
sid = 4 #PXI slot of AWT on chassis
from teproteus import TEProteusAdmin as TepAdmin
admin = TepAdmin() #required to control PXI module
inst = admin.open_instrument(slot_id=sid) 
resp = inst.send_scpi_query("*IDN?") # Get the instrument's *IDN
print('connected to: ' + resp) # Print *IDN
'''

# Connect to instrument(LAN)
inst_addr = 'TCPIP::192.168.1.13::5025::SOCKET' #Proteus Lan
#inst_addr = 'TCPIP::127.0.0.1::5025::SOCKET' #Proteus Local 

inst = TEVisaInst(inst_addr) # get instruent pointer
resp = inst.send_scpi_query("*IDN?")
print('Connected to: ' + resp) # Serial Number, FPGA Version

resp = inst.send_scpi_query("*OPT?")
print('Options: ' + resp) # print options

inst.send_scpi_cmd(':INST:ACT:SEL 1')  # Select instrument in Chassis

resp = inst.send_scpi_query(":SYST:INF:FPGA:VERS?")
print('FPGA Ver: ' + resp) # print FPGA Version

resp = inst.send_scpi_query(":SYST:INF:FIRM:SVN?")
print('FW Ver: ' + resp) # print FW Version
