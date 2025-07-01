import os 
import sys 

srcpath = os.path.realpath('SourceFiles') 
sys.path.append(srcpath)

from tevisainst import TEVisaInst 

import matplotlib.pyplot as plt
import numpy as np

inst_addr = 'TCPIP::192.168.1.22::5025::SOCKET' # <- use the IP address WDS found. 
inst = TEVisaInst(inst_addr) # get instruent pointer
resp = inst.send_scpi_query("*IDN?")
print('Connected to: ' + resp) # print insturmrnt ID

inst.send_scpi_cmd('*CLS; *RST') # Init instrument
#AWG channel
ch = 1 # everything after relates to CH 1
cmd = ':INST:CHAN {0}'.format(ch) #Everything is now CH one only operation
inst.send_scpi_cmd(cmd)

sampleRateDAC = 1E9
cmd = ':FREQ:RAST {0}'.format(sampleRateDAC) 
inst.send_scpi_cmd(cmd)
cmd = ':TRAC:DEL:ALL' # Clear CH 1 Memory
inst.send_scpi_cmd(cmd)
cmd = ':INIT:CONT ON' # play waveform continuously

# Make a waveform
amp = 1
cycles = 10
segLen = 1024 # must be a multiple of 64
time = np.linspace(0, segLen-1, segLen)
w = 2 * np.pi * cycles
dacWave = amp * np.sin(w*time/segLen) 
print('Frequency {0} Hz'.format(sampleRateDAC*cycles/segLen))

#scale to 16 bits
max_dac=65535 # Max Dac
half_dac=max_dac/2 # DC Level
data_type = np.uint16 # DAC data type 
dacWave = ((dacWave) + 1.0) * half_dac  
dacWave = dacWave.astype(data_type) 

# Create a waveform memory segment
segnum = 1
cmd = ':TRAC:DEF {0}, {1}'.format(segnum, len(dacWave)) # memory location and length
inst.send_scpi_cmd(cmd)

# Select the segment
cmd = ':TRAC:SEL {0}'.format(segnum)
inst.send_scpi_cmd(cmd)

#Download
inst.timeout = 30000 #increase
inst.write_binary_data('*OPC?; :TRAC:DATA', dacWave) # write, and wait while *OPC completes
inst.timeout = 10000 # return to normal

#Select segment and Switch output on
cmd = ':FUNC:MODE:SEGM {0}'.format(segnum)
inst.send_scpi_cmd(cmd)
cmd = ':OUTP ON'
rc = inst.send_scpi_cmd(cmd)

