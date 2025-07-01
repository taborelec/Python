import os 
import sys 

srcpath = os.path.realpath('SourceFiles') 
sys.path.append(srcpath)

from tevisainst import TEVisaInst 


inst_addr = 'TCPIP::192.168.1.16::5025::SOCKET' # <- use the IP address WDS found. 
inst = TEVisaInst(inst_addr) # get instruent pointer
resp = inst.send_scpi_query("*IDN?")
print('Connected to: ' + resp) # print insturmrnt ID

