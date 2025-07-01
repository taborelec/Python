import os 
import sys 

srcpath = os.path.realpath('SourceFiles') 
sys.path.append(srcpath)

from tevisainst import TEVisaInst 

import matplotlib.pyplot as plt
import numpy as np

inst_addr = 'TCPIP::169.254.148.9::5025::SOCKET' # <- use the IP address WDS found. 
inst_addr = 'TCPIP::192.168.1.14::5025::SOCKET' # <- use the IP address WDS found. 
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


segLen = 1024 # must be a multiple of 64
# #scale to 16 bits
max_dac=65535 # Max Dac
half_dac=max_dac/2 # DC Level
data_type = np.uint16 # DAC data type 

# Make a waveform DC
dacWave = np.ones(segLen)
dacWave = dacWave * max_dac  # scale
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

# Create and download a second Segment

# Make a waveform 
dacWave = np.ones(segLen)
dacWave = dacWave * half_dac  # scale
dacWave = dacWave.astype(data_type)  

segnum = 2
cmd = ':TRAC:DEF {0}, {1}'.format(segnum, len(dacWave)) # memory location and length
inst.send_scpi_cmd(cmd)

# Select the segment
cmd = ':TRAC:SEL {0}'.format(segnum)
inst.send_scpi_cmd(cmd)

inst.timeout = 30000 #increase
inst.write_binary_data('*OPC?; :TRAC:DATA', dacWave) # write, and wait while *OPC completes
inst.timeout = 10000 # return to normal


# Make a waveform 
dacWave = np.zeros(segLen)
dacWave = dacWave.astype(data_type)  

segnum = 3
cmd = ':TRAC:DEF {0}, {1}'.format(segnum, len(dacWave)) # memory location and length
inst.send_scpi_cmd(cmd)

# Select the segment
cmd = ':TRAC:SEL {0}'.format(segnum)
inst.send_scpi_cmd(cmd)

inst.timeout = 30000 #increase
inst.write_binary_data('*OPC?; :TRAC:DATA', dacWave) # write, and wait while *OPC completes
inst.timeout = 10000 # return to normal



#Create a Task Table
cmd = ':TASK:COMP:LENG 3' # set task table length
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:SEL 1' # set task 1
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:SEGM 1'
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:NEXT1 2'
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:SEL 2' # set task 2
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:SEGM 2'
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:NEXT1 3'
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:SEL 3' # set task 3
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:SEGM 3'
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:LOOP 2' 
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:NEXT1 1'
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:WRITE' #write to FPGA
inst.send_scpi_cmd(cmd)

cmd = ':SOUR:FUNC:MODE TASK'
inst.send_scpi_cmd(cmd)

cmd = ':OUTP ON'
rc = inst.send_scpi_cmd(cmd)



