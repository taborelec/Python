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

sampleRateDAC = 1.1E9
cmd = ':FREQ:RAST {0}'.format(sampleRateDAC) 
inst.send_scpi_cmd(cmd)
cmd = ':TRAC:DEL:ALL' # Clear CH 1 Memory
inst.send_scpi_cmd(cmd)
cmd = ':INIT:CONT ON' # play waveform continuously

max_dac=65535 # Max Dac
half_dac=max_dac/2 # DC Level
data_type = np.uint16 # DAC data type 

# Make and scale waveform
segLen = 1024 # must be a multiple of 64
dacWave = np.ones(segLen)
dacWave = dacWave * max_dac 
dacWave = dacWave.astype(data_type)

# reshapes for IQIQIQIQIQ....
arr_tuple = (dacWave, dacWave)
dacWave = np.vstack(arr_tuple).reshape((-1,), order='F')

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
segnum = 2
dacWaveDC = np.ones(segLen)
dacWaveDC = dacWaveDC * half_dac  # scale
dacWaveDC = dacWaveDC.astype(data_type)  

# reshapes for IQIQIQIQIQ....
arr_tuple = (dacWaveDC, dacWaveDC)
dacWaveDC = np.vstack(arr_tuple).reshape((-1,), order='F')

cmd = ':TRAC:DEF {0}, {1}'.format(segnum, len(dacWaveDC)) # memory location and length
inst.send_scpi_cmd(cmd)
cmd = ':TRAC:SEL {0}'.format(segnum)
inst.send_scpi_cmd(cmd)

inst.timeout = 30000 #increase
inst.write_binary_data('*OPC?; :TRAC:DATA', dacWaveDC) # write, and wait while *OPC completes
inst.timeout = 10000 # return to normal

#Create a Task Table
cmd = ':TASK:COMP:LENG 2' # set task table length
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:SEL 1' # set task 1
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:SEGM 1'
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:DTR ON' # Trigger the Digitizer
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:NEXT1 2'
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:SEL 2' # set task 2
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:SEGM 2'
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:LOOP 10' 
inst.send_scpi_cmd(cmd)
cmd = ':TASK:COMP:NEXT1 1'
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:WRITE' #write to FPGA
inst.send_scpi_cmd(cmd)

cmd = ':SOUR:FUNC:MODE TASK'
inst.send_scpi_cmd(cmd)

cmd = ':SOUR:MODE DUC'
resp = inst.send_scpi_cmd(cmd)
cmd = ':SOUR:IQM ONE'
resp = inst.send_scpi_cmd(cmd)
# Set x8 interpolation
cmd = ':SOUR:INT X8'
resp = inst.send_scpi_cmd(cmd)
# Reset sample rate to interpolated rate
sampleRateDACInt = sampleRateDAC * 8
cmd = ':FREQ:RAST {0}'.format(sampleRateDACInt)
resp = inst.send_scpi_cmd(cmd)
#Set the LO (NCO)
ncoFreq = 10E6
cmd = ':SOUR:NCO:CFR1 {0}'.format(ncoFreq)
resp = inst.send_scpi_cmd(cmd)

cmd = ':OUTP ON'
rc = inst.send_scpi_cmd(cmd)

# Digitize
numframes, framelen = 1, 9600
totalLen = numframes * framelen
wav1 = np.zeros(framelen, dtype=np.uint16)
inst.send_scpi_cmd(':DIG:MODE DUAL') # enables CH1 and CH2, max rate is 2.5GS/s
sampleRateADC = 1E9
cmd = ':DIG:FREQ  {0}'.format(sampleRateADC)
inst.send_scpi_cmd(cmd)

inst.send_scpi_cmd(':DIG:CHAN:SEL 1')
inst.send_scpi_cmd(':DIG:CHAN:STATE ENAB')
inst.send_scpi_cmd(':DIG:TRIG:SOURCE TASK1')
cmd = ':DIG:ACQuire:FRAM:DEF {0},{1}'.format(numframes, framelen)
inst.send_scpi_cmd(cmd)
capture_first, capture_count = 1, numframes
cmd = ':DIG:ACQuire:FRAM:CAPT {0},{1}'.format(capture_first, capture_count)
inst.send_scpi_cmd(cmd)
# Start the digitizer's capture machine
inst.send_scpi_cmd(':DIG:INIT ON')
inst.send_scpi_cmd(':DIG:TRIG:IMM')
inst.send_scpi_cmd(':DIG:INIT OFF')

inst.send_scpi_cmd(':DIG:DATA:SEL ALL')
inst.send_scpi_cmd(':DIG:DATA:TYPE FRAM')
resp = inst.send_scpi_query(':DIG:DATA:SIZE?')
rc = inst.read_binary_data(':DIG:DATA:READ?', wav1, totalLen)
plt.plot(wav1)
plt.show()
