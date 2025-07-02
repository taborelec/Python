import os
import sys

srcpath = os.path.realpath('../SourceFiles')
sys.path.append(srcpath)

import warnings # this is for GUI warnings
warnings.filterwarnings("ignore")

from tevisainst import TEVisaInst

import numpy as np

import matplotlib.pyplot as plt

data_type = np.uint16


#Set sample rate for ADC
sampleRateADC = 5.4E9
#sampleRateADC = 2.7E9

#Set number of frames to be collected
numframes, framelen = 1, 200*4800
totlen = numframes * framelen

#Preallocate processing memory
wav1 = np.zeros(framelen, dtype=np.uint16)
xT = np.linspace(0, numframes * framelen,  numframes * framelen )
xT = xT/sampleRateADC
tpCount = len(wav1)
timeStep = xT[1]-xT[0]
xF = np.fft.fftfreq(tpCount, timeStep)
xF = xF[range(int(len(wav1)/2))]


'''
# Connect to instrument(PXI)
sid = 12 #PXI slot of AWT on chassis
from teproteus import TEProteusAdmin as TepAdmin
admin = TepAdmin() #required to control PXI module
inst = admin.open_instrument(slot_id=sid) 
resp = inst.send_scpi_query("*IDN?") # Get the instrument's *IDN
print('connected to: ' + resp) # Print *IDN
'''
# Connect to instrument(LAN)
inst_addr = 'TCPIP::192.168.1.12::5025::SOCKET' #Proteus 9484 in office '
inst = TEVisaInst(inst_addr)

resp = inst.send_scpi_query("*IDN?")
print('connected to: ' + resp)

# initialize DAC and take the first capture.
inst.send_scpi_cmd(':DIG:MODE SING')

print('ADC Clk Freq {0}'.format(sampleRateADC))
cmd = ':DIG:FREQ  {0}'.format(sampleRateADC)
inst.send_scpi_cmd(cmd)

# Enable capturing data from channel 1
inst.send_scpi_cmd(':DIG:CHAN:SEL 1')
inst.send_scpi_cmd(':DIG:CHAN:STATE ENAB')
# Select the internal-trigger as start-capturing trigger:
inst.send_scpi_cmd(':DIG:TRIG:SOURCE CPU')

#Define the ADC frame
cmd = ':DIG:ACQuire:FRAM:DEF {0},{1}'.format(numframes, framelen)
inst.send_scpi_cmd(cmd)

# Select the frames fto be captured
# (all the four frames in this example)
capture_first, capture_count = 1, numframes
cmd = ':DIG:ACQuire:FRAM:CAPT {0},{1}'.format(capture_first, capture_count)
inst.send_scpi_cmd(cmd)

# Start the digitizer's capturing machine
inst.send_scpi_cmd(':DIG:INIT ON')
inst.send_scpi_cmd(':DIG:TRIG:IMM')
inst.send_scpi_cmd(':DIG:INIT OFF')

# Choose which frames to read (all in this example)
inst.send_scpi_cmd(':DIG:DATA:SEL ALL')

# Choose what to read 
# (only the frame-data without the header in this example)
inst.send_scpi_cmd(':DIG:DATA:TYPE FRAM')

# Get the total data size (in bytes)
resp = inst.send_scpi_query(':DIG:DATA:SIZE?')
num_bytes = np.uint32(resp)
print('Total read size in bytes: ' + resp)
print()

# Read the data that was captured by channel 1:
inst.send_scpi_cmd(':DIG:CHAN:SEL 1')
wavlen = num_bytes // 2
# The redback of this data must be of this form, the read back date is moved into the variable wav1, which size and type has been pre-allocatied.
rc = inst.read_binary_data(':DIG:DATA:READ?', wav1, num_bytes)

plt.plot(wav1)
plt.show()
